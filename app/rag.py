from functools import lru_cache
from typing import List, Optional

import chromadb

from .config import get_settings
from .db import Database
from .models import Proposicao, SearchHit

COLLECTION_NAME = "proposicoes_tech"


class RagIndex:
    def __init__(self, db: Database):
        self.db = db
        self.settings = get_settings()
        self._client: Optional[chromadb.ClientAPI] = None
        self._collection = None
        self._embedding_error: Optional[str] = None

    def _embedding_function(self):
        provider = self.settings.resolved_embedding_provider()
        if provider == "openai":
            from chromadb.utils import embedding_functions

            return embedding_functions.OpenAIEmbeddingFunction(
                api_key=self.settings.resolved_llm_key(),
                model_name=self.settings.embedding_model,
                api_base=self.settings.llm_base_url,
            )
        return None

    def _get_collection(self):
        if self._collection is not None:
            return self._collection
        self._client = chromadb.PersistentClient(path=str(self.settings.chroma_path))
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self._embedding_function(),
            metadata={"hnsw:space": "cosine"},
        )
        return self._collection

    @property
    def embedding_error(self) -> Optional[str]:
        return self._embedding_error

    def count(self) -> int:
        try:
            return self._get_collection().count()
        except Exception as exc:
            self._embedding_error = str(exc)
            return 0

    def build_document(self, prop: Proposicao, tramitacoes: Optional[List] = None) -> str:
        partes = [f"{prop.tipo} {prop.numero}/{prop.ano} ({prop.casa})"]
        partes.append(f"Ementa: {prop.ementa}")
        if prop.autor:
            partes.append(f"Autor: {prop.autor}")
        if prop.temas:
            partes.append(f"Temas: {', '.join(prop.temas)}")
        if prop.situacao:
            partes.append(f"Situação atual: {prop.situacao}")
        if prop.orgao:
            partes.append(f"Órgão atual: {prop.orgao}")
        if tramitacoes:
            linhas = []
            for t in tramitacoes[-8:]:
                desc = t.descricao or t.situacao or ""
                if not desc:
                    continue
                linhas.append(
                    f"- {t.data_hora or 's/ data'} {t.orgao or ''}: {desc}".strip()
                )
            if linhas:
                partes.append("Movimentações recentes:\n" + "\n".join(linhas))
        return "\n".join(partes)

    def index_proposicao(self, prop: Proposicao, tramitacoes: Optional[List] = None) -> None:
        collection = self._get_collection()
        documento = self.build_document(prop, tramitacoes)
        metadata = {
            "casa": prop.casa,
            "tipo": prop.tipo,
            "numero": prop.numero,
            "ano": prop.ano,
            "situacao": prop.situacao or "",
            "url": prop.url or "",
            "temas": "; ".join(prop.temas),
        }
        collection.upsert(ids=[prop.id], documents=[documento], metadatas=[metadata])

    def index_many(self, itens: List[tuple]) -> int:
        collection = self._get_collection()
        if not itens:
            return 0
        ids, documentos, metadatas = [], [], []
        for prop, tramitacoes in itens:
            ids.append(prop.id)
            documentos.append(self.build_document(prop, tramitacoes))
            metadatas.append(
                {
                    "casa": prop.casa,
                    "tipo": prop.tipo,
                    "numero": prop.numero,
                    "ano": prop.ano,
                    "situacao": prop.situacao or "",
                    "url": prop.url or "",
                    "temas": "; ".join(prop.temas),
                }
            )
        collection.upsert(ids=ids, documents=documentos, metadatas=metadatas)
        return len(ids)

    def _where(
        self,
        casa: Optional[str],
        tipo: Optional[str],
        ano_de: Optional[int],
        ano_ate: Optional[int],
    ) -> Optional[dict]:
        filtros: List[dict] = []
        if casa:
            filtros.append({"casa": casa})
        if tipo:
            filtros.append({"tipo": tipo})
        if ano_de is not None and ano_ate is not None:
            filtros.append({"ano": {"$gte": ano_de, "$lte": ano_ate}})
        elif ano_de is not None:
            filtros.append({"ano": {"$gte": ano_de}})
        elif ano_ate is not None:
            filtros.append({"ano": {"$lte": ano_ate}})
        if not filtros:
            return None
        if len(filtros) == 1:
            return filtros[0]
        return {"$and": filtros}

    def search(
        self,
        query: str,
        limit: int = 8,
        casa: Optional[str] = None,
        tipo: Optional[str] = None,
        ano_de: Optional[int] = None,
        ano_ate: Optional[int] = None,
    ) -> tuple[List[SearchHit], str]:
        if self.count() == 0:
            return self._search_textual(query, limit, casa, tipo, ano_de, ano_ate), "textual"
        try:
            collection = self._get_collection()
            result = collection.query(
                query_texts=[query],
                n_results=max(limit * 3, limit),
                where=self._where(casa, tipo, ano_de, ano_ate),
            )
        except Exception as exc:
            self._embedding_error = str(exc)
            return self._search_textual(query, limit, casa, tipo, ano_de, ano_ate), "textual"

        ids = (result.get("ids") or [[]])[0]
        documentos = (result.get("documents") or [[]])[0]
        distancias = (result.get("distances") or [[]])[0]
        ordem = list(dict.fromkeys(ids))
        props = self.db.get_many(ordem)
        by_id = {p.id: p for p in props}
        doc_by_id = {i: d for i, d in zip(ids, documentos)}
        dist_by_id = {i: d for i, d in zip(ids, distancias)}

        hits: List[SearchHit] = []
        for pid in ordem:
            prop = by_id.get(pid)
            if prop is None:
                continue
            distancia = dist_by_id.get(pid, 1.0)
            hits.append(
                SearchHit(
                    proposicao=prop,
                    score=round(max(0.0, 1.0 - float(distancia)), 4),
                    trecho=doc_by_id.get(pid),
                )
            )
        if not hits:
            return self._search_textual(query, limit, casa, tipo, ano_de, ano_ate), "textual"
        return hits[:limit], "semantica"

    def _search_textual(
        self,
        query: str,
        limit: int,
        casa: Optional[str],
        tipo: Optional[str],
        ano_de: Optional[int],
        ano_ate: Optional[int],
    ) -> List[SearchHit]:
        props = self.db.buscar_textual(query, limit=limit * 3)
        hits: List[SearchHit] = []
        for prop in props:
            if casa and prop.casa != casa:
                continue
            if tipo and prop.tipo != tipo:
                continue
            if ano_de is not None and prop.ano < ano_de:
                continue
            if ano_ate is not None and prop.ano > ano_ate:
                continue
            hits.append(SearchHit(proposicao=prop, score=0.5, trecho=self.build_document(prop)))
        return hits[:limit]

    def reset(self) -> None:
        try:
            client = chromadb.PersistentClient(path=str(self.settings.chroma_path))
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        self._collection = None


@lru_cache
def get_rag_index() -> RagIndex:
    return RagIndex(Database(get_settings().db_path))
