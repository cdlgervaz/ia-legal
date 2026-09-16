import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.catalog import get as get_catalogo
from app.config import get_settings
from app.db import Database
from app.models import DocumentoCatalogo
from app.rag import RagIndex


def _itens_documentos(db: Database):
    vistos = set()
    for doc in db.list_documentos():
        vistos.add(doc["id"])
        yield (
            DocumentoCatalogo(
                id=doc["id"],
                titulo=doc["titulo"],
                tipo=doc["tipo"],
                ano=doc["ano"],
                orgao=doc.get("orgao") or "",
                url=doc.get("url") or "",
                temas=doc.get("temas") or [],
                importavel=False,
            ),
            db.get_chunks(doc["id"]),
        )
    with db.connect() as conn:
        orfaos = [
            r["documento_id"]
            for r in conn.execute("SELECT DISTINCT documento_id FROM chunks").fetchall()
        ]
    for documento_id in orfaos:
        if documento_id in vistos:
            continue
        do_catalogo = get_catalogo(documento_id)
        if do_catalogo is None:
            do_catalogo = DocumentoCatalogo(
                id=documento_id,
                titulo=documento_id,
                tipo="Documento",
                importavel=False,
            )
        yield do_catalogo, db.get_chunks(documento_id)


def main() -> int:
    settings = get_settings()
    db = Database(settings.db_path)
    rag = RagIndex(db)

    props = db.all_proposicoes()
    print(f"Reindexando {len(props)} proposições...")
    pares = []
    processados = 0
    for prop in props:
        detalhe = db.get_proposicao(prop.id)
        tram = detalhe.tramitacoes if detalhe else []
        texto = None
        if prop.fonte == "cne":
            cache = settings.data_dir / "cne_textos" / f"{prop.id}.txt"
            if cache.exists():
                texto = cache.read_text(encoding="utf-8", errors="ignore")
        pares.append((prop, tram, texto))
        if len(pares) >= 50:
            rag.index_many(pares)
            processados += len(pares)
            pares = []
            print(f"  {processados}/{len(props)}")
    if pares:
        rag.index_many(pares)

    total_docs = 0
    for item, chunks in _itens_documentos(db):
        if not chunks:
            continue
        rag.index_chunks(item, chunks)
        total_docs += 1
        print(f"  documento {item.id}: {len(chunks)} trechos")

    print(f"Concluído. Documentos: {total_docs} | vetores no índice: {rag.count()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
