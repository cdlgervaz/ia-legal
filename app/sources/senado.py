import time
from typing import Dict, List, Optional, Union

import httpx

from ..models import Proposicao, Tramitacao

BASE_URL = "https://legis.senado.leg.br/dadosabertos"


def _as_list(value: Union[None, dict, list]) -> List:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


class SenadoClient:
    def __init__(self, timeout: float = 30.0, delay: float = 0.25, retries: int = 3):
        self.timeout = timeout
        self.delay = delay
        self.retries = retries
        self._client = httpx.Client(
            base_url=BASE_URL,
            timeout=timeout,
            headers={"Accept": "application/json", "User-Agent": "IALegal/1.0"},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "SenadoClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def _get(self, path: str, params: Optional[Dict] = None) -> dict:
        last_exc: Optional[Exception] = None
        for tentativa in range(1, self.retries + 1):
            try:
                resp = self._client.get(path, params=params)
                if resp.status_code == 429:
                    time.sleep(min(2 ** tentativa, 15))
                    continue
                resp.raise_for_status()
                time.sleep(self.delay)
                return resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                last_exc = exc
                time.sleep(min(2 ** tentativa, 15))
        raise RuntimeError(f"Falha ao consultar {path}: {last_exc}")

    def listar(self, sigla: str, ano: int) -> List[dict]:
        data = self._get("/materia/pesquisa/lista", {"sigla": sigla, "ano": ano})
        materias = data.get("PesquisaBasicaMateria", {}).get("Materias", {})
        return _as_list(materias.get("Materia"))

    def situacao_atual(self, codigo: str) -> dict:
        data = self._get(f"/materia/situacaoatual/{codigo}")
        materias = data.get("SituacaoAtualMateria", {}).get("Materias", {})
        itens = _as_list(materias.get("Materia"))
        if not itens:
            return {}
        situacao = itens[0].get("SituacaoAtual") or {}
        resultado = {"tramitando": itens[0].get("Tramitando")}
        autuacoes = _as_list((situacao.get("Autuacoes") or {}).get("Autuacao"))
        if autuacoes:
            ultima = autuacoes[-1]
            local = ultima.get("Local") or {}
            resultado["orgao"] = local.get("SiglaLocal") or local.get("NomeLocal")
            situacoes = _as_list((ultima.get("Situacoes") or {}).get("Situacao"))
            if situacoes:
                final = situacoes[-1]
                resultado["situacao"] = final.get("DescricaoSituacao")
                resultado["data"] = final.get("DataSituacao")
        return resultado

    def movimentacoes(self, codigo: str, max_eventos: int = 15) -> List[Tramitacao]:
        data = self._get(f"/materia/movimentacoes/{codigo}")
        materia = data.get("MovimentacaoMateria", {}).get("Materia", {})
        eventos: List[Tramitacao] = []
        autuacoes = _as_list(materia.get("Autuacoes"))
        if autuacoes and isinstance(autuacoes[0], dict):
            autuacoes = _as_list(autuacoes[0].get("Autuacao"))
        for autuacao in autuacoes:
            local = autuacao.get("Local") or {}
            orgao = local.get("SiglaLocal") or local.get("NomeLocal")
            for item in _as_list((autuacao.get("Situacoes") or {}).get("Situacao")):
                eventos.append(
                    Tramitacao(
                        sequencia=None,
                        data_hora=item.get("DataSituacao"),
                        orgao=orgao,
                        descricao=item.get("DescricaoSituacao"),
                        situacao=item.get("DescricaoSituacao"),
                        regime=None,
                    )
                )
        for despacho in _as_list(materia.get("Despachos")):
            if isinstance(despacho, dict):
                eventos.append(
                    Tramitacao(
                        sequencia=None,
                        data_hora=despacho.get("DataDespacho"),
                        orgao=None,
                        descricao=despacho.get("DescricaoDespacho"),
                        situacao=None,
                        regime=None,
                    )
                )
        for atualizacao in _as_list(materia.get("AtualizacoesRecentes")):
            if isinstance(atualizacao, dict):
                eventos.append(
                    Tramitacao(
                        sequencia=None,
                        data_hora=atualizacao.get("DataAtualizacao"),
                        orgao=None,
                        descricao=atualizacao.get("DescricaoAtualizacao"),
                        situacao=None,
                        regime=None,
                    )
                )
        eventos = [e for e in eventos if e.data_hora or e.descricao]
        eventos.sort(key=lambda e: (e.data_hora or ""), reverse=True)
        eventos = list(reversed(eventos[:max_eventos]))
        for idx, evento in enumerate(eventos):
            evento.sequencia = idx
        return eventos

    def normalize(self, item: dict, situacao: Optional[dict] = None) -> Proposicao:
        codigo = str(item.get("Codigo"))
        numero = str(item.get("Numero", "")).lstrip("0") or "0"
        ano = int(item.get("Ano") or 0)
        situacao = situacao or {}
        return Proposicao(
            id=f"senado-{codigo}",
            casa="Senado",
            tipo=item.get("Sigla", ""),
            numero=numero,
            ano=ano,
            ementa=(item.get("Ementa") or "").strip(),
            autor=item.get("Autor"),
            data=(item.get("Data") or "")[:10] or None,
            url=f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{codigo}",
            situacao=situacao.get("situacao"),
            orgao=situacao.get("orgao"),
            temas=[],
            fonte="senado",
        )
