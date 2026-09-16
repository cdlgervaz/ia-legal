import copy
import threading
import time
from datetime import datetime, timezone
from typing import Callable, List, Optional

from .config import get_settings
from .db import Database
from .keywords import is_tech, termos_encontrados
from .models import SyncRequest, SyncResponse
from .rag import get_rag_index
from .sources import CamaraClient, SenadoClient, TEMA_CIENCIA_TECNOLOGIA, TEMA_COMUNICACOES

_sync_lock = threading.Lock()
_sync_state = {
    "running": False,
    "fase": "ocioso",
    "fonte": "",
    "processados": 0,
    "indexados": 0,
    "mensagens": [],
    "iniciado_em": None,
    "concluido_em": None,
    "resultado": None,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _estado() -> dict:
    with _sync_lock:
        return copy.deepcopy(_sync_state)


def get_sync_state() -> dict:
    return _estado()


def _update(**kwargs) -> None:
    with _sync_lock:
        _sync_state.update(kwargs)


class _Progress:
    def __init__(self, mensagens: List[str]):
        self.mensagens = mensagens
        self.processados = 0
        self.indexados = 0

    def fase(self, texto: str, fonte: str = "") -> None:
        self.mensagens.append(texto)
        _update(fase=texto, fonte=fonte, processados=self.processados, indexados=self.indexados)

    def inc(self, indexados: int = 0) -> None:
        self.processados += 1
        self.indexados += indexados
        if self.processados % 5 == 0:
            _update(processados=self.processados, indexados=self.indexados)


def _flush_index(rag, pares: List[tuple]) -> int:
    return rag.index_many(pares)


def sync_camara(
    db: Database,
    rag,
    progress: _Progress,
    anos: List[int],
    tipos: List[str],
    max_itens_por_ano: int,
    incluir_comunicacoes: bool,
    buscar_tramitacoes: bool,
) -> int:
    temas = [TEMA_CIENCIA_TECNOLOGIA]
    if incluir_comunicacoes:
        temas.append(TEMA_COMUNICACOES)
    total = 0
    with CamaraClient(
        timeout=get_settings().http_timeout,
        delay=get_settings().http_delay,
        retries=get_settings().request_retries,
    ) as client:
        for ano in anos:
            candidatos: dict = {}
            for tipo in tipos:
                for cod_tema in temas:
                    try:
                        itens = client.listar_por_tema(cod_tema, tipo, ano, max_itens_por_ano)
                    except RuntimeError:
                        continue
                    for item in itens:
                        candidatos[int(item["id"])] = item
            selecionados = list(candidatos.values())[:max_itens_por_ano]
            progress.fase(
                f"Câmara {ano}: {len(selecionados)} proposições de tecnologia", "camara"
            )
            pares = []
            for item in selecionados:
                pid = int(item["id"])
                try:
                    temas_prop = client.temas(pid)
                    detalhe = client.detalhe(pid)
                    nomes = client.autores(pid)
                    tram = client.tramitacoes(pid) if buscar_tramitacoes else []
                except RuntimeError:
                    continue
                status = detalhe.get("statusProposicao") or {}
                prop = client.normalize(
                    item,
                    temas=temas_prop,
                    autor=", ".join(nomes[:3]) if nomes else None,
                    situacao=status.get("descricaoSituacao"),
                    orgao=status.get("siglaOrgao"),
                )
                if not prop.ementa:
                    continue
                db.upsert_proposicao(prop)
                if tram:
                    db.replace_tramitacoes(prop.id, tram)
                pares.append((prop, tram))
                total += 1
                progress.inc()
                if len(pares) >= 50:
                    _flush_index(rag, pares)
                    pares = []
            if pares:
                _flush_index(rag, pares)
    db.log_sync("camara", total)
    return total


def sync_senado(
    db: Database,
    rag,
    progress: _Progress,
    anos: List[int],
    tipos: List[str],
    max_itens_por_ano: int,
    buscar_tramitacoes: bool,
) -> int:
    total = 0
    with SenadoClient(
        timeout=get_settings().http_timeout,
        delay=get_settings().http_delay,
        retries=get_settings().request_retries,
    ) as client:
        for ano in anos:
            candidatos: dict = {}
            for tipo in tipos:
                try:
                    itens = client.listar(tipo, ano)
                except RuntimeError:
                    continue
                for item in itens:
                    if is_tech(item.get("Ementa", "")):
                        candidatos[str(item.get("Codigo"))] = item
            selecionados = list(candidatos.values())[:max_itens_por_ano]
            progress.fase(
                f"Senado {ano}: {len(selecionados)} matérias de tecnologia", "senado"
            )
            pares = []
            for item in selecionados:
                codigo = str(item.get("Codigo"))
                try:
                    situacao = client.situacao_atual(codigo)
                    tram = client.movimentacoes(codigo) if buscar_tramitacoes else []
                except RuntimeError:
                    situacao, tram = {}, []
                prop = client.normalize(item, situacao=situacao)
                if not prop.ementa:
                    continue
                prop.temas = termos_encontrados(prop.ementa)[:6]
                db.upsert_proposicao(prop)
                if tram:
                    db.replace_tramitacoes(prop.id, tram)
                pares.append((prop, tram))
                total += 1
                progress.inc()
                if len(pares) >= 50:
                    _flush_index(rag, pares)
                    pares = []
            if pares:
                _flush_index(rag, pares)
    db.log_sync("senado", total)
    return total


def run_sync(req: SyncRequest, progress_cb: Optional[Callable] = None) -> SyncResponse:
    settings = get_settings()
    db = Database(settings.db_path)
    rag = get_rag_index()

    anos = req.anos or [datetime.now().year, datetime.now().year - 1, datetime.now().year - 2]
    mensagens: List[str] = []
    progress = _Progress(mensagens)
    inicio = time.time()
    resposta = SyncResponse()

    _update(
        running=True,
        iniciado_em=_now(),
        concluido_em=None,
        processados=0,
        indexados=0,
        mensagens=[],
        resultado=None,
    )
    try:
        if req.camara:
            resposta.camara = sync_camara(
                db,
                rag,
                progress,
                anos,
                req.tipos,
                req.max_itens_por_ano,
                req.incluir_comunicacoes,
                req.buscar_tramitacoes,
            )
        if req.senado:
            resposta.senado = sync_senado(
                db,
                rag,
                progress,
                anos,
                req.tipos,
                req.max_itens_por_ano,
                req.buscar_tramitacoes,
            )
        resposta.indexados = rag.count()
    finally:
        resposta.duracao_segundos = round(time.time() - inicio, 1)
        resposta.mensagens = mensagens
        _update(
            running=False,
            fase="concluido",
            concluido_em=_now(),
            mensagens=mensagens,
            resultado=resposta.model_dump(),
            processados=progress.processados,
            indexados=progress.indexados,
        )
    return resposta


def start_sync_background(req: SyncRequest) -> bool:
    if _estado()["running"]:
        return False

    def _run():
        try:
            run_sync(req)
        except Exception as exc:
            _update(running=False, fase=f"erro: {exc}", concluido_em=_now())

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return True
