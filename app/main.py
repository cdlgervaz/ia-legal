from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .db import Database
from .ingest import get_sync_state, start_sync_background
from .llm import LLMClient, LLMNotConfigured
from .models import (
    ChatRequest,
    ChatResponse,
    ProposicaoDetalhe,
    SearchRequest,
    SearchResponse,
    SyncRequest,
    SyncResponse,
)
from .rag import get_rag_index

settings = get_settings()
STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Database(settings.db_path)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

llm = LLMClient(settings)


def _db() -> Database:
    return Database(settings.db_path)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    db = _db()
    rag = get_rag_index()
    return {
        "status": "ok",
        "llm_configurado": settings.llm_enabled(),
        "llm_provider": settings.llm_provider if settings.llm_enabled() else None,
        "embeddings": settings.resolved_embedding_provider(),
        "indexados": rag.count(),
        "stats": db.stats(),
    }


@app.get("/api/stats")
def stats() -> dict:
    return _db().stats()


@app.post("/api/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Consulta vazia.")
    rag = get_rag_index()
    hits, modo = rag.search(
        req.query,
        limit=req.limit or settings.default_search_limit,
        casa=req.casa,
        tipo=req.tipo,
        ano_de=req.ano_de,
        ano_ate=req.ano_ate,
    )
    return SearchResponse(query=req.query, modo=modo, total=len(hits), resultados=hits)


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Consulta vazia.")
    rag = get_rag_index()
    hits, modo = rag.search(
        req.query,
        limit=req.limit or settings.default_search_limit,
        casa=req.casa,
        tipo=req.tipo,
        ano_de=req.ano_de,
        ano_ate=req.ano_ate,
    )
    if not hits:
        return ChatResponse(
            query=req.query,
            resposta="Nenhum documento encontrado no índice. Execute a sincronização em Configurações.",
            modo=modo,
            fontes=[],
        )
    if not settings.llm_enabled():
        return ChatResponse(
            query=req.query,
            resposta=(
                "LLM não configurado. Os trechos legislativos mais relevantes foram recuperados "
                "abaixo. Configure LLM_API_KEY no arquivo .env para gerar respostas com IA."
            ),
            modo=modo,
            fontes=hits,
        )
    try:
        resposta = llm.responder(req.query, hits)
    except LLMNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erro no provedor de LLM: {exc}") from exc
    return ChatResponse(query=req.query, resposta=resposta, modo=modo, fontes=hits)


@app.get("/api/proposicoes")
def listar_proposicoes(
    casa: Optional[str] = None,
    tipo: Optional[str] = None,
    ano_de: Optional[int] = None,
    ano_ate: Optional[int] = None,
    busca: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    db = _db()
    itens = db.list_proposicoes(
        casa=casa, tipo=tipo, ano_de=ano_de, ano_ate=ano_ate, busca=busca, limit=limit, offset=offset
    )
    return {"total": len(itens), "itens": [p.model_dump() for p in itens]}


@app.get("/api/proposicoes/{proposicao_id}", response_model=ProposicaoDetalhe)
def detalhe_proposicao(proposicao_id: str) -> ProposicaoDetalhe:
    prop = _db().get_proposicao(proposicao_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="Proposição não encontrada.")
    return prop


@app.post("/api/proposicoes/{proposicao_id}/resumo")
def resumo_proposicao(proposicao_id: str) -> dict:
    db = _db()
    prop = db.get_proposicao(proposicao_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="Proposição não encontrada.")
    if not settings.llm_enabled():
        raise HTTPException(status_code=503, detail="LLM não configurado para gerar resumo.")
    try:
        texto = llm.resumir(prop, prop.tramitacoes)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erro no provedor de LLM: {exc}") from exc
    return {"id": proposicao_id, "resumo": texto}


@app.post("/api/sync", response_model=SyncResponse)
def sync(req: SyncRequest) -> SyncResponse:
    from .ingest import run_sync

    return run_sync(req)


@app.post("/api/sync/background")
def sync_background(req: SyncRequest) -> dict:
    iniciado = start_sync_background(req)
    if not iniciado:
        raise HTTPException(status_code=409, detail="Sincronização já em andamento.")
    return {"status": "iniciado", "estado": get_sync_state()}


@app.get("/api/sync/status")
def sync_status() -> dict:
    return get_sync_state()
