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
from .sources import (
    CamaraClient,
    CneClient,
    DouClient,
    SenadoClient,
    TEMA_CIENCIA_TECNOLOGIA,
    TEMA_COMUNICACOES,
)
from .sources.dou import CONSULTAS_PADRAO, intervalo_padrao
from .sources.ipea import IpeaClient

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


def sync_cne(
    db: Database,
    rag,
    progress: _Progress,
    max_itens: int,
    extrair_texto: bool,
) -> int:
    total = 0
    with CneClient(
        timeout=get_settings().http_timeout,
        delay=0.2,
        retries=get_settings().request_retries,
    ) as client:
        try:
            itens = client.listar()
        except RuntimeError:
            itens = []
        if max_itens and len(itens) > max_itens:
            itens = itens[-max_itens:]
        progress.fase(f"CNE: {len(itens)} pareceres relatados encontrados", "cne")
        pares = []
        for item in itens:
            texto = ""
            if extrair_texto:
                try:
                    texto = client.extrair_texto(item["url"], item["id"])
                except RuntimeError:
                    texto = ""
            prop = client.normalize(item, texto)
            db.upsert_proposicao(prop)
            pares.append((prop, None, texto or None))
            total += 1
            progress.inc()
            if len(pares) >= 20:
                _flush_index(rag, pares)
                pares = []
        if pares:
            _flush_index(rag, pares)
    db.log_sync("cne", total)
    return total


def sync_dou(
    db: Database,
    rag,
    progress: _Progress,
    consultas: List[str],
    paginas: int,
    data_inicio: str,
    data_fim: str,
) -> int:
    total = 0
    consultas = consultas or CONSULTAS_PADRAO
    with DouClient(
        timeout=get_settings().http_timeout,
        delay=0.3,
        retries=get_settings().request_retries,
    ) as client:
        for termo in consultas:
            try:
                achados = client.buscar(termo, data_inicio, data_fim, paginas=paginas)
            except RuntimeError:
                continue
            inseridos = 0
            pares = []
            for item in achados:
                prop = client.normalize(item)
                if prop is None:
                    continue
                db.upsert_proposicao(prop)
                pares.append((prop, None))
                total += 1
                inseridos += 1
                progress.inc()
            if pares:
                _flush_index(rag, pares)
            progress.fase(
                f"Diário Oficial '{termo}': {inseridos} atos relevantes", "dou"
            )
    db.log_sync("dou", total)
    return total


def sync_ipea(db: Database, progress: Optional[_Progress] = None) -> int:
    with IpeaClient() as client:
        areas = client.mapa("area/")
        grandes = client.mapa("grande_area/")
        brutos = client.politicas()
        itens = [client.normalize(item, areas, grandes) for item in brutos]
    total = db.upsert_politicas(itens)
    if progress is not None:
        progress.fase(f"IPEA: {total} políticas públicas catalogadas", "ipea")
    db.log_sync("ipea", total)
    return total


_index_pol_lock = threading.Lock()
_index_pol_state = {
    "running": False,
    "processados": 0,
    "total": 0,
    "mensagens": [],
    "concluido_em": None,
}


def get_index_pol_state() -> dict:
    with _index_pol_lock:
        return copy.deepcopy(_index_pol_state)


def _index_pol_update(**kwargs) -> None:
    with _index_pol_lock:
        _index_pol_state.update(kwargs)


def indexar_politicas(db: Database, rag) -> int:
    itens = db.list_politicas(limit=100000)
    total = len(itens)
    _index_pol_update(running=True, processados=0, total=total, mensagens=[], concluido_em=None)
    processados = 0
    lote = 100
    try:
        for inicio in range(0, total, lote):
            rag.index_politicas(itens[inicio : inicio + lote])
            processados = min(inicio + lote, total)
            _index_pol_update(processados=processados)
    finally:
        _index_pol_update(running=False, processados=processados, concluido_em=_now())
    return processados


def start_indexar_politicas_background() -> bool:
    if get_index_pol_state()["running"]:
        return False

    def _run():
        settings = get_settings()
        db = Database(settings.db_path)
        rag = get_rag_index()
        try:
            indexar_politicas(db, rag)
        except Exception as exc:
            _index_pol_update(running=False, mensagens=[f"erro: {exc}"], concluido_em=_now())

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return True


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
        if req.cne:
            resposta.cne = sync_cne(
                db,
                rag,
                progress,
                req.cne_max,
                req.cne_extrair_texto,
            )
        if req.diario_oficial:
            data_inicio, data_fim = intervalo_padrao(
                max(len(anos), 3) if anos else 7
            )
            resposta.diario_oficial = sync_dou(
                db,
                rag,
                progress,
                req.dou_consultas,
                req.dou_paginas,
                data_inicio,
                data_fim,
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
