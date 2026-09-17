from functools import lru_cache
from typing import List, Optional

import chromadb

from .catalog import categoria_de
from .config import get_settings
from .db import Database
from .models import DocumentoCatalogo, Proposicao, SearchHit
from .temas import classificar
from .texto import sem_acento

COLLECTION_NAME = "proposicoes_tech"


def _sem_acento(texto: str) -> str:
    return sem_acento(texto).lower()


def montar_indice_se_preciso(chroma_path) -> None:
    from pathlib import Path
    import glob

    destino = Path(chroma_path) / "chroma.sqlite3"
    if destino.exists():
        return
    partes = sorted(
        glob.glob(str(Path(chroma_path).parent / "chroma_parts" / "chroma.sqlite3.part.*"))
    )
    if not partes:
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "wb") as saida:
        for parte in partes:
            with open(parte, "rb") as entrada:
                saida.write(entrada.read())


class RagIndex:
    def __init__(self, db: Database):
        self.db = db
        self.settings = get_settings()
        self._client: Optional[chromadb.ClientAPI] = None
        self._collection = None
        self._embedding_error: Optional[str] = None
        self._temas_cache: dict = {}

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
        montar_indice_se_preciso(self.settings.chroma_path)
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

    def build_document(
        self, prop: Proposicao, tramitacoes: Optional[List] = None, texto: Optional[str] = None
    ) -> str:
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
        if texto:
            partes.append(f"Texto: {texto}")
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

    def _metadata_proposicao(self, prop: Proposicao) -> dict:
        return {
            "casa": prop.casa,
            "tipo": prop.tipo,
            "numero": prop.numero,
            "ano": prop.ano,
            "situacao": prop.situacao or "",
            "url": prop.url or "",
            "temas": "; ".join(prop.temas),
            "origem": "proposicao",
        }

    def index_proposicao(
        self,
        prop: Proposicao,
        tramitacoes: Optional[List] = None,
        texto: Optional[str] = None,
    ) -> None:
        collection = self._get_collection()
        documento = self.build_document(prop, tramitacoes, texto)
        collection.upsert(
            ids=[prop.id], documents=[documento], metadatas=[self._metadata_proposicao(prop)]
        )

    def index_many(self, itens: List[tuple]) -> int:
        collection = self._get_collection()
        if not itens:
            return 0
        ids, documentos, metadatas = [], [], []
        for item in itens:
            prop, tramitacoes = item[0], item[1]
            texto = item[2] if len(item) > 2 else None
            ids.append(prop.id)
            documentos.append(self.build_document(prop, tramitacoes, texto))
            metadatas.append(self._metadata_proposicao(prop))
        collection.upsert(ids=ids, documents=documentos, metadatas=metadatas)
        return len(ids)

    def delete_chunks(self, documento_id: str) -> None:
        try:
            collection = self._get_collection()
            collection.delete(where={"documento_id": documento_id})
        except Exception as exc:
            self._embedding_error = str(exc)

    def index_chunks(self, item: DocumentoCatalogo, chunks: List[dict]) -> int:
        collection = self._get_collection()
        if not chunks:
            return 0
        temas = item.temas or classificar(" ".join(c["texto"] for c in chunks))
        temas = [t for t in temas if t][:3]
        total = 0
        lote = 100
        for inicio in range(0, len(chunks), lote):
            ids, documentos, metadatas = [], [], []
            for chunk in chunks[inicio : inicio + lote]:
                ids.append(f"{item.id}#{chunk['ordem']:05d}")
                documentos.append(f"{item.titulo} ({item.tipo}, {item.ano}).\n{chunk['texto']}")
                metadata = {
                    "origem": "documento",
                    "documento_id": item.id,
                    "titulo": item.titulo,
                    "tipo": item.tipo,
                    "categoria": item.categoria or categoria_de(item.tipo),
                    "ano": item.ano or 0,
                    "orgao": item.orgao or "",
                    "url": item.url or "",
                    "pagina": chunk.get("pagina") or 0,
                }
                for indice in range(3):
                    metadata[f"tema{indice + 1}"] = temas[indice] if indice < len(temas) else ""
                metadatas.append(metadata)
            collection.upsert(ids=ids, documents=documentos, metadatas=metadatas)
            total += len(ids)
        return total

    def index_politicas(self, politicas: List[dict]) -> int:
        collection = self._get_collection()
        if not politicas:
            return 0
        ids, documentos, metadatas = [], [], []
        for p in politicas:
            texto = (
                f"{p.get('nome') or ''}. "
                f"Área: {p.get('area_nome') or ''}. "
                f"Órgão: {p.get('orgao') or ''}. "
                f"{p.get('legislacao') or ''} {p.get('instrumento_legal') or ''}. "
                f"{p.get('objetivos') or ''}"
            )
            ids.append(f"politica-{p['id']}")
            documentos.append(texto[:6000])
            metadatas.append(
                {
                    "origem": "politica",
                    "casa": "IPEA",
                    "tipo": "Política pública",
                    "ano": p.get("ano") or 0,
                    "temas": p.get("area_nome") or "",
                    "url": p.get("link") or "",
                    "politica_id": p["id"],
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
        documento_id: Optional[str] = None,
        categoria: Optional[str] = None,
    ) -> Optional[dict]:
        filtros: List[dict] = []
        if casa:
            filtros.append({"casa": casa})
        if tipo:
            filtros.append({"tipo": tipo})
        if categoria:
            filtros.append({"categoria": categoria})
        if ano_de is not None and ano_ate is not None:
            filtros.append({"ano": {"$gte": ano_de, "$lte": ano_ate}})
        elif ano_de is not None:
            filtros.append({"ano": {"$gte": ano_de}})
        elif ano_ate is not None:
            filtros.append({"ano": {"$lte": ano_ate}})
        if documento_id:
            filtros.append({"documento_id": documento_id})
        if not filtros:
            return None
        if len(filtros) == 1:
            return filtros[0]
        return {"$and": filtros}

    def _temas_do_documento(self, documento_id: str) -> List[str]:
        doc = self.db.get_documento(documento_id)
        return doc["temas"] if doc else []

    def _temas_da_proposicao(self, prop: Proposicao) -> List[str]:
        if prop.id in self._temas_cache:
            return self._temas_cache[prop.id]
        temas = classificar(self.build_document(prop), maximo=4)
        self._temas_cache[prop.id] = temas
        return temas

    def _hit_documento(
        self, chunk: dict, titulo: str, score: float, consulta: str
    ) -> SearchHit:
        doc = self.db.get_documento(chunk["documento_id"]) or {}
        prop = Proposicao(
            id=chunk["documento_id"],
            casa=doc.get("orgao") or "Documento",
            tipo=doc.get("tipo") or "Documento",
            numero="",
            ano=doc.get("ano") or 0,
            ementa=doc.get("titulo") or titulo,
            url=doc.get("url"),
            temas=doc.get("temas") or [],
            fonte="documento",
        )
        trecho = self._snippet(chunk["texto"], consulta, largura=700) or chunk["texto"]
        return SearchHit(
            proposicao=prop,
            score=score,
            trecho=trecho,
            origem="documento",
            documento_id=chunk["documento_id"],
            titulo=doc.get("titulo") or titulo,
            pagina=chunk.get("pagina"),
            categoria=doc.get("categoria") or categoria_de(doc.get("tipo") or ""),
            vigente=doc.get("vigente"),
            situacao=doc.get("situacao"),
            substituido_por=doc.get("substituido_por"),
        )

    def search(
        self,
        query: str,
        limit: int = 8,
        casa: Optional[str] = None,
        tipo: Optional[str] = None,
        ano_de: Optional[int] = None,
        ano_ate: Optional[int] = None,
        tema: Optional[str] = None,
        documento_id: Optional[str] = None,
        categoria: Optional[str] = None,
    ) -> tuple[List[SearchHit], str]:
        candidatos: List[SearchHit] = []
        sem_ok = False
        if self.count() > 0:
            try:
                collection = self._get_collection()
                result = collection.query(
                    query_texts=[query],
                    n_results=min(max(limit * 6, 30), 200),
                    where=self._where(casa, tipo, ano_de, ano_ate, documento_id, categoria),
                )
                candidatos = self._hits_do_resultado(result, query, tema)
                sem_ok = True
            except Exception as exc:
                self._embedding_error = str(exc)
        textuais = self._search_textual(
            query, limit, casa, tipo, ano_de, ano_ate, tema, documento_id, categoria
        )
        combinados: dict = {}
        for hit in candidatos + textuais:
            if hit.origem == "documento":
                chave = ("documento", hit.documento_id or "")
            else:
                chave = ("proposicao", hit.proposicao.id)
            atual = combinados.get(chave)
            if atual is None or hit.score > atual.score:
                combinados[chave] = hit
        selecionados = sorted(combinados.values(), key=lambda h: h.score, reverse=True)[:limit]
        if not selecionados:
            return [], "textual"
        if sem_ok and candidatos and textuais:
            modo = "hibrida"
        elif sem_ok and candidatos:
            modo = "semantica"
        else:
            modo = "textual"
        return selecionados, modo

    def _hit_politica(self, pol: dict, score: float, consulta: str) -> SearchHit:
        situacao = "Vigente" if pol.get("vigente") else "Descontinuada"
        prop = Proposicao(
            id=f"politica-{pol['id']}",
            casa="IPEA",
            tipo="Política pública",
            numero="",
            ano=pol.get("ano") or 0,
            ementa=pol.get("objetivos") or pol.get("nome") or "",
            autor=pol.get("orgao"),
            url=pol.get("link"),
            situacao=situacao,
            orgao=pol.get("orgao"),
            temas=[pol.get("area_nome")] if pol.get("area_nome") else [],
            fonte="ipea",
        )
        return SearchHit(
            proposicao=prop,
            score=score,
            trecho=self._snippet(pol.get("objetivos") or pol.get("nome"), consulta, largura=500),
            origem="politica",
            titulo=pol.get("nome"),
            categoria="Política pública",
            vigente=pol.get("vigente"),
            situacao=situacao,
        )

    def _hits_do_resultado(self, result: dict, query: str, tema: Optional[str]) -> List[SearchHit]:
        ids = (result.get("ids") or [[]])[0]
        documentos = (result.get("documents") or [[]])[0]
        distancias = (result.get("distances") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]

        ids_prop: List[str] = []
        ids_chunk: List[str] = []
        ids_pol: List[str] = []
        for item_id in dict.fromkeys(ids):
            if item_id.startswith("politica-"):
                ids_pol.append(item_id)
            elif "#" in item_id:
                ids_chunk.append(item_id)
            else:
                ids_prop.append(item_id)

        props = {p.id: p for p in self.db.get_many(ids_prop)}
        chunks = {c["id"]: c for c in self.db.get_chunks_by_ids(ids_chunk)}
        politicas: dict = {}
        for item_id in ids_pol:
            try:
                pid = int(item_id.split("-", 1)[1])
            except (IndexError, ValueError):
                continue
            pol = self.db.get_politica(pid)
            if pol:
                politicas[item_id] = pol
        doc_by_id = {i: d for i, d in zip(ids, documentos)}
        dist_by_id = {i: d for i, d in zip(ids, distancias)}
        meta_by_id = {i: m for i, m in zip(ids, metadatas)}

        hits_prop: List[SearchHit] = []
        hits_doc: List[SearchHit] = []
        for item_id in dict.fromkeys(ids):
            distancia = float(dist_by_id.get(item_id, 1.0))
            score = round(max(0.0, 1.0 - distancia), 4)
            if item_id in props:
                prop = props[item_id]
                if tema and tema not in self._temas_da_proposicao(prop):
                    continue
                hits_prop.append(
                    SearchHit(
                        proposicao=prop,
                        score=score,
                        trecho=self._snippet(doc_by_id.get(item_id), query),
                    )
                )
                continue
            pol = politicas.get(item_id)
            if pol is not None:
                hits_prop.append(self._hit_politica(pol, score, query))
                continue
            chunk = chunks.get(item_id)
            if chunk is None:
                continue
            if tema and tema not in self._temas_do_documento(chunk["documento_id"]):
                continue
            meta = meta_by_id.get(item_id) or {}
            hits_doc.append(
                self._hit_documento(chunk, str(meta.get("titulo") or ""), score, query)
            )

        melhores: dict[str, SearchHit] = {}
        for hit in hits_doc:
            atual = melhores.get(hit.documento_id or "")
            if atual is None or hit.score > atual.score:
                melhores[hit.documento_id or ""] = hit
        return hits_prop + list(melhores.values())

    def _search_textual(
        self,
        query: str,
        limit: int,
        casa: Optional[str],
        tipo: Optional[str],
        ano_de: Optional[int],
        ano_ate: Optional[int],
        tema: Optional[str] = None,
        documento_id: Optional[str] = None,
        categoria: Optional[str] = None,
    ) -> List[SearchHit]:
        hits: List[SearchHit] = []
        if not documento_id and not categoria:
            for prop in self.db.buscar_textual(query, limit=limit * 3):
                if casa and prop.casa != casa:
                    continue
                if tipo and prop.tipo != tipo:
                    continue
                if ano_de is not None and prop.ano < ano_de:
                    continue
                if ano_ate is not None and prop.ano > ano_ate:
                    continue
                if tema and tema not in self._temas_da_proposicao(prop):
                    continue
                hits.append(SearchHit(proposicao=prop, score=0.45, trecho=self.build_document(prop)))
        for chunk in self.db.buscar_chunks(query, documento_id=documento_id, limit=limit * 3):
            if tema and tema not in self._temas_do_documento(chunk["documento_id"]):
                continue
            if categoria:
                doc = self.db.get_documento(chunk["documento_id"]) or {}
                doc_categoria = doc.get("categoria") or categoria_de(doc.get("tipo") or "")
                if doc_categoria != categoria:
                    continue
            relevancia = int(chunk.get("relevancia") or 1)
            score = min(0.59, 0.35 + 0.08 * relevancia)
            hits.append(self._hit_documento(chunk, "", score, query))
        melhores: dict[str, SearchHit] = {}
        for hit in hits:
            if hit.origem == "documento":
                chave = hit.documento_id or ""
            else:
                chave = hit.proposicao.id
            atual = melhores.get(chave)
            if atual is None or hit.score > atual.score:
                melhores[chave] = hit
        ordenados = sorted(melhores.values(), key=lambda h: h.score, reverse=True)
        return ordenados[:limit]

    def buscar_no_documento(
        self, documento_id: str, termo: str, limit: int = 20, modo: str = "chave"
    ) -> List[SearchHit]:
        if modo == "semantica":
            return self.search(termo, limit=limit, documento_id=documento_id)[0]
        chunks = self.db.buscar_chunks(termo, documento_id=documento_id, limit=limit)
        return [self._hit_documento(chunk, "", 0.0, termo) for chunk in chunks]

    def _snippet(self, texto: Optional[str], query: str, largura: int = 340) -> Optional[str]:
        if not texto:
            return None
        if len(texto) <= largura + 80:
            return texto
        normalizado = _sem_acento(texto)
        melhor = -1
        for termo in query.lower().split():
            termo = _sem_acento(termo).strip()
            if len(termo) < 4:
                continue
            posicao = normalizado.find(termo)
            if posicao >= 0 and (melhor < 0 or posicao < melhor):
                melhor = posicao
        if melhor < 0:
            return texto[:largura].strip() + " ..."
        inicio = max(0, melhor - largura // 3)
        fim = min(len(texto), inicio + largura)
        prefixo = "..." if inicio > 0 else ""
        sufixo = " ..." if fim < len(texto) else ""
        return f"{prefixo}{texto[inicio:fim].strip()}{sufixo}"

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
