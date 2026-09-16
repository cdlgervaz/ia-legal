import time
from dataclasses import dataclass
from typing import Optional

import httpx

from .config import Config, USER_AGENT


@dataclass
class Resposta:
    url: str
    url_final: str
    status: int
    content_type: str
    conteudo: bytes

    @property
    def tipo(self) -> str:
        ct = self.content_type.lower()
        if "pdf" in ct or self.url_final.lower().endswith(".pdf"):
            return "pdf"
        if "html" in ct or "xml" in ct:
            return "html"
        if self.url_final.lower().endswith(".pdf"):
            return "pdf"
        if self.url_final.lower().endswith((".htm", ".html", ".xhtml", ".php", ".asp", ".aspx")):
            return "html"
        return "outro"


def _desafio(resp: httpx.Response) -> bool:
    if resp.status_code in (403, 429):
        return True
    inicio = resp.content[:3000]
    return b"Just a moment" in inicio or b"cf-challenge" in inicio


def _via_wayback(url: str, cfg: Config) -> Optional[Resposta]:
    try:
        with httpx.Client(follow_redirects=True, timeout=max(cfg.http_timeout, 90)) as client:
            resp = client.get(f"https://web.archive.org/web/2id_/{url}")
        if resp.status_code >= 400 or not resp.content:
            return None
        return Resposta(
            url=url,
            url_final=url,
            status=200,
            content_type=resp.headers.get("content-type", ""),
            conteudo=resp.content,
        )
    except (httpx.HTTPError, OSError):
        return None


def _via_jina(url: str, cfg: Config) -> Optional[Resposta]:
    try:
        with httpx.Client(follow_redirects=True, timeout=max(cfg.http_timeout, 90)) as client:
            resp = client.get(f"https://r.jina.ai/{url}")
        if resp.status_code >= 400 or not resp.content:
            return None
        return Resposta(
            url=url,
            url_final=url,
            status=200,
            content_type="text/plain; charset=utf-8",
            conteudo=resp.content,
        )
    except (httpx.HTTPError, OSError):
        return None


def baixar(url: str, cfg: Config) -> Optional[Resposta]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/pdf,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.5",
    }
    for tentativa in range(cfg.http_retries):
        try:
            with httpx.Client(
                follow_redirects=True,
                timeout=cfg.http_timeout,
                headers=headers,
                verify=False,
            ) as client:
                resp = client.get(url)
            if _desafio(resp):
                alternativa = _via_wayback(url, cfg) or _via_jina(url, cfg)
                if alternativa is not None:
                    return alternativa
            if resp.status_code >= 400:
                if resp.status_code in (429, 500, 502, 503, 504):
                    time.sleep(2 * (tentativa + 1))
                    continue
                return None
            content_type = resp.headers.get("content-type", "")
            if "text/css" in content_type or "javascript" in content_type:
                return None
            return Resposta(
                url=url,
                url_final=str(resp.url),
                status=resp.status_code,
                content_type=content_type,
                conteudo=resp.content,
            )
        except (httpx.HTTPError, OSError):
            time.sleep(1.5 * (tentativa + 1))
    return None
