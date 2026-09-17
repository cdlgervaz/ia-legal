from typing import Dict, List, Optional

import httpx

BASE_URL = "https://catalogo.ipea.gov.br/api"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)


def _ano(valor) -> Optional[int]:
    if not valor:
        return None
    texto = str(valor)
    if len(texto) >= 4 and texto[:4].isdigit():
        return int(texto[:4])
    return None


class IpeaClient:
    def __init__(self, timeout: float = 120.0, retries: int = 3):
        self.retries = retries
        self._client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "IpeaClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def _get(self, caminho: str):
        import json
        import time

        ultimo: Optional[Exception] = None
        for tentativa in range(1, self.retries + 1):
            try:
                resposta = self._client.get(f"{BASE_URL}/{caminho}")
                resposta.raise_for_status()
                return resposta.json()
            except (httpx.HTTPError, ValueError) as exc:
                ultimo = exc
                time.sleep(min(2 ** tentativa, 10))
        raise RuntimeError(f"Falha ao consultar o Catálogo do IPEA ({caminho}): {ultimo}")

    def mapa(self, recurso: str) -> Dict[int, str]:
        try:
            dados = self._get(recurso)
        except RuntimeError:
            return {}
        mapa = {}
        for item in dados:
            if isinstance(item, dict) and "id" in item:
                mapa[item["id"]] = item.get("nome") or item.get("titulo") or ""
        return mapa

    def politicas(self) -> List[dict]:
        return self._get("politica/")

    def normalize(self, item: dict, areas: Dict[int, str], grandes: Dict[int, str]) -> dict:
        orgaos = []
        for vinculo in item.get("politica_orgao") or []:
            orgao = (vinculo or {}).get("orgao") or {}
            nome = orgao.get("nome")
            if nome:
                orgaos.append(nome)
        area_id = item.get("area")
        grande_id = item.get("grande_area")
        vigencia_fim = item.get("vigencia_fim")
        return {
            "id": int(item["id"]),
            "nome": (item.get("nome") or "").strip(),
            "ano": _ano(item.get("ano")),
            "area_id": area_id,
            "area_nome": areas.get(area_id),
            "grande_area_id": grande_id,
            "grande_area": grandes.get(grande_id),
            "orgao": "; ".join(dict.fromkeys(orgaos)) or None,
            "instrumento_legal": item.get("instrumento_legal"),
            "legislacao": item.get("legislacao"),
            "vigencia_inicio": item.get("vigencia_inicio"),
            "vigencia_fim": vigencia_fim,
            "vigente": 0 if vigencia_fim else 1,
            "objetivos": item.get("objetivos"),
            "publico_alvo": item.get("publico_alvo_legislacao"),
            "link": item.get("link_legislacao"),
            "tipo_politica": str(item.get("tipo_politica"))
            if item.get("tipo_politica") is not None
            else None,
        }
