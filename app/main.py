import base64
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .catalog import CATALOGO, get as get_catalogo, listar as listar_catalogo
from .config import get_settings
from .db import Database
from .documentos import (
    get_import_state,
    importar,
    start_import_background,
)
from .ingest import (
    get_index_pol_state,
    get_sync_state,
    start_indexar_politicas_background,
    start_sync_background,
)
from .llm import LLMClient, LLMNotConfigured
from .models import (
    ChatRequest,
    ChatResponse,
    ImportRequest,
    ProposicaoDetalhe,
    SearchRequest,
    SearchResponse,
    SyncRequest,
    SyncResponse,
)
from .rag import get_rag_index
from .temas import lista_temas
from .indicadores import TEMPLATE as TEMPLATE_INDICADORES
from .indicadores import parse_csv
from .trilhas import get as get_trilha
from .trilhas import listar as listar_trilhas

settings = get_settings()
STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Database(settings.db_path)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

llm = LLMClient(settings)


@app.middleware("http")
async def autenticar(request: Request, call_next):
    if not settings.app_password:
        return await call_next(request)
    caminho = request.url.path
    if caminho in ("/api/health", "/favicon.ico"):
        return await call_next(request)
    cabecalho = request.headers.get("authorization", "")
    if cabecalho.lower().startswith("basic "):
        try:
            credenciais = base64.b64decode(cabecalho.split(" ", 1)[1]).decode("utf-8")
            usuario, senha = credenciais.split(":", 1)
            if secrets.compare_digest(usuario, settings.app_user) and secrets.compare_digest(
                senha, settings.app_password
            ):
                return await call_next(request)
        except Exception:
            pass
    return Response(
        content="Autenticação necessária.",
        status_code=401,
        headers={"WWW-Authenticate": 'Basic realm="IAgora, profe?"'},
    )


def _db() -> Database:
    return Database(settings.db_path)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "index.html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@app.get("/api/health")
def health() -> dict:
    db = _db()
    rag = get_rag_index()
    return {
        "status": "ok",
        "app": settings.app_name,
        "llm_configurado": settings.llm_enabled(),
        "llm_provider": settings.llm_provider if settings.llm_enabled() else None,
        "llm_model": settings.llm_model if settings.llm_enabled() else None,
        "embeddings": settings.resolved_embedding_provider(),
        "indexados": rag.count(),
        "autenticacao": bool(settings.app_password),
        "stats": db.stats(),
    }


@app.get("/api/stats")
def stats() -> dict:
    return _db().stats()


@app.get("/api/politicas/stats")
def politicas_stats() -> dict:
    return _db().politicas_stats()


@app.get("/api/politicas")
def listar_politicas(
    area: Optional[str] = None,
    orgao: Optional[str] = None,
    ano_de: Optional[int] = None,
    ano_ate: Optional[int] = None,
    vigente: Optional[bool] = None,
    q: Optional[str] = None,
    limit: int = Query(default=60, le=300),
    offset: int = Query(default=0, ge=0),
) -> dict:
    itens = _db().list_politicas(
        area=area,
        orgao=orgao,
        ano_de=ano_de,
        ano_ate=ano_ate,
        vigente=vigente,
        q=q,
        limit=limit,
        offset=offset,
    )
    return {"total": len(itens), "itens": itens}


@app.post("/api/politicas/sincronizar")
def politicas_sincronizar() -> dict:
    from .ingest import sync_ipea

    return {"inseridos": sync_ipea(_db())}


@app.post("/api/politicas/indexar/background")
def politicas_indexar_background() -> dict:
    if not start_indexar_politicas_background():
        raise HTTPException(status_code=409, detail="Indexação já em andamento.")
    return {"status": "iniciado", "estado": get_index_pol_state()}


@app.get("/api/politicas/indexar/status")
def politicas_indexar_status() -> dict:
    return get_index_pol_state()


@app.get("/api/politicas/{politica_id}")
def politica_detalhe(politica_id: int) -> dict:
    item = _db().get_politica(politica_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Política não encontrada.")
    return item


@app.get("/api/indicadores/catalogo")
def indicadores_catalogo() -> dict:
    db = _db()
    return {"indicadores": db.indicadores_catalogo(), "ufs": db.ufs_indicadores()}


@app.get("/api/indicadores/stats")
def indicadores_stats() -> dict:
    return _db().indicadores_stats()


@app.get("/api/indicadores/modelo")
def indicadores_modelo() -> dict:
    return {"csv": TEMPLATE_INDICADORES}


@app.get("/api/indicadores")
def listar_indicadores(
    indicador: Optional[str] = None,
    uf: Optional[str] = None,
    localidade: Optional[str] = None,
    ano_de: Optional[int] = None,
    ano_ate: Optional[int] = None,
    limit: int = Query(default=300, le=2000),
    offset: int = Query(default=0, ge=0),
) -> dict:
    itens = _db().list_indicadores(
        indicador=indicador,
        uf=uf,
        localidade=localidade,
        ano_de=ano_de,
        ano_ate=ano_ate,
        limit=limit,
        offset=offset,
    )
    return {"total": len(itens), "itens": itens}


@app.post("/api/indicadores/importar")
def importar_indicadores(payload: dict) -> dict:
    texto = (payload or {}).get("csv") or ""
    itens, erros = parse_csv(texto)
    total = _db().upsert_indicadores(itens) if itens else 0
    return {"importados": total, "erros": erros}


@app.get("/api/temas")
def temas() -> dict:
    return {"temas": lista_temas()}


@app.get("/api/trilhas")
def api_trilhas() -> dict:
    return {"trilhas": listar_trilhas()}


@app.get("/api/trilhas/{trilha_id}")
def api_trilha(trilha_id: str) -> dict:
    item = get_trilha(trilha_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Trilha não encontrada.")
    return item


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
        tema=req.tema,
        documento_id=req.documento_id,
        categoria=req.categoria,
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
        tema=req.tema,
        documento_id=req.documento_id,
        categoria=req.categoria,
    )
    if not hits:
        return ChatResponse(
            query=req.query,
            resposta=(
                "Nenhum documento encontrado no índice. Importe os documentos na aba "
                "'Documentos' ou reformule a pergunta."
            ),
            modo=modo,
            fontes=[],
        )
    if not settings.llm_enabled():
        return ChatResponse(
            query=req.query,
            resposta=(
                "LLM não configurado. Os trechos mais relevantes foram recuperados abaixo. "
                "Configure LLM_API_KEY no arquivo .env para gerar respostas com IA."
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


@app.get("/api/documentos")
def listar_documentos(
    tema: Optional[str] = None,
    tipo: Optional[str] = None,
    q: Optional[str] = None,
) -> dict:
    db = _db()
    importados = {d["id"]: d for d in db.list_documentos()}
    itens = []
    for item in listar_catalogo(tema=tema, tipo=tipo):
        dados = item.model_dump()
        estado = importados.get(item.id)
        dados.update(
            {
                "importado": bool(estado and estado["chunks"]),
                "chunks": (estado or {}).get("chunks", 0),
                "paginas": (estado or {}).get("paginas", 0),
                "importado_em": (estado or {}).get("importado_em"),
            }
        )
        itens.append(dados)
    catalogo_ids = {item.id for item in CATALOGO}
    for estado in importados.values():
        if estado["id"] in catalogo_ids:
            continue
        if tema and tema not in (estado["temas"] or []):
            continue
        itens.append(
            {
                **estado,
                "descricao": "Documento importado localmente.",
                "formato": (
                    Path(estado["arquivo"]).suffix.lstrip(".") if estado.get("arquivo") else ""
                ),
                "importavel": True,
                "importado": True,
            }
        )
    if q:
        alvo = q.lower()
        itens = [
            i for i in itens if alvo in i["titulo"].lower() or alvo in (i.get("descricao") or "").lower()
        ]
    itens.sort(key=lambda i: (not i.get("importado"), -(i.get("ano") or 0), i.get("titulo")))
    return {"total": len(itens), "itens": itens}


@app.get("/api/documentos/importar/status")
def importar_status() -> dict:
    return get_import_state()


@app.post("/api/documentos/importar")
def importar_documentos(req: ImportRequest) -> dict:
    return importar(req)


@app.post("/api/documentos/importar/background")
def importar_background(req: ImportRequest) -> dict:
    if not start_import_background(req):
        raise HTTPException(status_code=409, detail="Importação já em andamento.")
    return {"status": "iniciado", "estado": get_import_state()}


@app.get("/api/documentos/{documento_id}")
def documento_detalhe(documento_id: str) -> dict:
    db = _db()
    estado = db.get_documento(documento_id)
    item = get_catalogo(documento_id)
    if estado is None and item is None:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    dados = item.model_dump() if item else {}
    if estado:
        dados.update(estado)
        dados["importado"] = True
    else:
        dados.update({"importado": False, "chunks": 0, "paginas": 0})
    return dados


@app.get("/api/documentos/{documento_id}/busca")
def buscar_no_documento(
    documento_id: str,
    q: str,
    modo: str = Query(default="chave", pattern="^(chave|semantica)$"),
    limit: int = Query(default=20, le=100),
) -> dict:
    if not q.strip():
        raise HTTPException(status_code=400, detail="Consulta vazia.")
    rag = get_rag_index()
    hits = rag.buscar_no_documento(documento_id, q, limit=limit, modo=modo)
    return {
        "documento_id": documento_id,
        "query": q,
        "modo": modo,
        "total": len(hits),
        "resultados": [hit.model_dump() for hit in hits],
    }


@app.get("/api/documentos/{documento_id}/conteudo")
def conteudo_documento(
    documento_id: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, le=50),
) -> dict:
    db = _db()
    doc = db.get_documento(documento_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Documento não importado.")
    trechos = db.get_chunks(documento_id, limit=limit, offset=offset)
    return {
        "documento_id": documento_id,
        "titulo": doc["titulo"],
        "total": doc["chunks"],
        "offset": offset,
        "itens": trechos,
    }


@app.post("/api/documentos/{documento_id}/resumo")
def resumo_documento(documento_id: str) -> dict:
    db = _db()
    doc = db.get_documento(documento_id)
    item = get_catalogo(documento_id)
    if doc is None and item is None:
        raise HTTPException(status_code=404, detail="Documento não encontrado.")
    if doc is None:
        raise HTTPException(status_code=400, detail="Documento ainda não importado.")
    if not settings.llm_enabled():
        raise HTTPException(status_code=503, detail="LLM não configurado para gerar resumo.")
    trechos = [c["texto"] for c in db.amostrar_chunks(documento_id, quantidade=24)]
    try:
        texto = llm.resumir_documento(
            doc["titulo"], doc["tipo"], doc["orgao"] or "", trechos
        )
    except LLMNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erro no provedor de LLM: {exc}") from exc
    return {"id": documento_id, "titulo": doc["titulo"], "resumo": texto}


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
