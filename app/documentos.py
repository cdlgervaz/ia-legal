import copy
import re
import threading
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple

import httpx

from .catalog import CATALOGO, categoria_de, get as get_catalogo
from .config import get_settings
from .db import Database
from .models import DocumentoCatalogo, ImportRequest
from .rag import get_rag_index
from .temas import classificar
from .texto import normalizar

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)

_IGNORAR = {"script", "style", "head", "nav", "header", "footer", "form", "noscript", "svg"}
_QUEBRA = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article"}

_import_lock = threading.Lock()
_import_state = {
    "running": False,
    "fase": "ocioso",
    "documento": "",
    "processados": 0,
    "total": 0,
    "chunks": 0,
    "mensagens": [],
    "erros": [],
    "iniciado_em": None,
    "concluido_em": None,
    "resultado": None,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _estado() -> dict:
    with _import_lock:
        return copy.deepcopy(_import_state)


def get_import_state() -> dict:
    return _estado()


def _update(**kwargs) -> None:
    with _import_lock:
        _import_state.update(kwargs)


class _ExtratorHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.partes: List[str] = []
        self._ignorando = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in _IGNORAR:
            self._ignorando += 1
        elif tag in _QUEBRA and self.partes:
            self.partes.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _IGNORAR and self._ignorando:
            self._ignorando -= 1
        elif tag in _QUEBRA and self.partes:
            self.partes.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignorando:
            return
        texto = re.sub(r"\s+", " ", data).strip()
        if texto:
            self.partes.append(texto)
            self.partes.append(" ")

    def texto(self) -> str:
        bruto = "".join(self.partes)
        bruto = re.sub(r"[ \t]+", " ", bruto)
        bruto = re.sub(r"\n\s*\n+", "\n\n", bruto)
        return bruto.strip()


def extrair_html(caminho: Path) -> List[Tuple[Optional[int], str]]:
    bruto = caminho.read_bytes()
    for codificacao in ("utf-8", "latin-1"):
        try:
            conteudo = bruto.decode(codificacao)
            break
        except UnicodeDecodeError:
            continue
    else:
        conteudo = bruto.decode("utf-8", errors="ignore")
    parser = _ExtratorHTML()
    parser.feed(conteudo)
    return [(None, parser.texto())]


def extrair_pdf(caminho: Path) -> List[Tuple[Optional[int], str]]:
    from pypdf import PdfReader

    leitor = PdfReader(BytesIO(caminho.read_bytes()))
    paginas: List[Tuple[Optional[int], str]] = []
    for numero, pagina in enumerate(leitor.pages, start=1):
        try:
            texto = pagina.extract_text() or ""
        except Exception:
            texto = ""
        texto = re.sub(r"[ \t]+", " ", texto)
        texto = re.sub(r"\n{3,}", "\n\n", texto).strip()
        if texto:
            paginas.append((numero, texto))
    return paginas


def extrair(caminho: Path, formato: str) -> List[Tuple[Optional[int], str]]:
    if formato == "pdf" or caminho.suffix.lower() == ".pdf":
        return extrair_pdf(caminho)
    return extrair_html(caminho)


def _dividir_bloco(bloco: str, tamanho: int, sobreposicao: int) -> List[str]:
    partes: List[str] = []
    inicio = 0
    while inicio < len(bloco):
        fim = min(len(bloco), inicio + tamanho)
        if fim < len(bloco):
            corte = bloco.rfind(". ", inicio + tamanho // 2, fim)
            if corte > 0:
                fim = corte + 1
        partes.append(bloco[inicio:fim].strip())
        if fim >= len(bloco):
            break
        inicio = max(inicio + 1, fim - sobreposicao)
    return [p for p in partes if p]


def dividir_em_chunks(texto: str, tamanho: int, sobreposicao: int) -> List[str]:
    blocos = [b.strip() for b in re.split(r"\n\s*\n|\n(?=[A-ZÀ-Ú0-9])", texto) if b and b.strip()]
    chunks: List[str] = []
    atual = ""
    for bloco in blocos:
        if len(bloco) > tamanho:
            if atual:
                chunks.append(atual.strip())
                atual = ""
            chunks.extend(_dividir_bloco(bloco, tamanho, sobreposicao))
            continue
        if len(atual) + len(bloco) + 2 <= tamanho:
            atual = f"{atual}\n{bloco}" if atual else bloco
        else:
            if atual:
                chunks.append(atual.strip())
            atual = bloco
    if atual:
        chunks.append(atual.strip())
    vistos = set()
    limpos: List[str] = []
    for chunk in chunks:
        if len(chunk) < 60 and limpos:
            continue
        chave = normalizar(chunk)
        if not chave or chave in vistos:
            continue
        vistos.add(chave)
        limpos.append(chunk)
    return limpos


def montar_chunks(
    paginas: List[Tuple[Optional[int], str]], tamanho: int, sobreposicao: int
) -> List[dict]:
    itens: List[dict] = []
    ordem = 0
    for numero, texto in paginas:
        for parte in dividir_em_chunks(texto, tamanho, sobreposicao):
            itens.append(
                {
                    "ordem": ordem,
                    "pagina": numero,
                    "texto": parte,
                    "normalizado": normalizar(parte),
                }
            )
            ordem += 1
    return itens


def baixar(url: str, destino: Path, timeout: float = 120.0, retries: int = 3) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    ultimo_erro: Optional[Exception] = None
    for tentativa in range(1, retries + 1):
        try:
            with httpx.Client(
                timeout=timeout,
                follow_redirects=True,
                headers={"User-Agent": USER_AGENT, "Accept": "application/pdf,text/html,*/*"},
            ) as client:
                resposta = client.get(url)
                resposta.raise_for_status()
                if not resposta.content:
                    raise RuntimeError("conteúdo vazio")
                destino.write_bytes(resposta.content)
                return destino
        except Exception as exc:
            ultimo_erro = exc
            time.sleep(min(2 ** tentativa, 8))
    raise RuntimeError(f"Falha ao baixar {url}: {ultimo_erro}")


def importar_documento(
    item: DocumentoCatalogo,
    db: Database,
    rag,
    forcar: bool = False,
    baixar_arquivo: bool = True,
    arquivo: Optional[Path] = None,
    titulo: Optional[str] = None,
    tipo: Optional[str] = None,
    ano: Optional[int] = None,
    orgao: Optional[str] = None,
    temas: Optional[List[str]] = None,
) -> dict:
    settings = get_settings()
    if not item.importavel and arquivo is None:
        raise ValueError(f"Documento '{item.id}' não é importável automaticamente.")
    existente = db.get_documento(item.id)
    if existente and existente["chunks"] and not forcar and arquivo is None:
        return {
            "id": item.id,
            "titulo": existente["titulo"],
            "chunks": existente["chunks"],
            "paginas": existente["paginas"],
            "pulado": True,
        }

    formato = (item.formato or "pdf").lower()
    if arquivo is None:
        arquivo = settings.docs_dir / f"{item.id}.{'pdf' if formato == 'pdf' else 'html'}"
    if not arquivo.exists():
        if not baixar_arquivo:
            raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")
        baixar(item.url, arquivo)
    if arquivo.suffix.lower() == ".pdf":
        formato = "pdf"

    paginas = extrair(arquivo, formato)
    if not paginas:
        raise RuntimeError(f"Nenhum texto extraído de {arquivo.name}.")
    total_paginas = max((p for p, _ in paginas if p), default=len(paginas))
    chunks = montar_chunks(paginas, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        raise RuntimeError(f"Nenhum trecho gerado para {arquivo.name}.")

    texto_completo = "\n".join(texto for _, texto in paginas)
    temas_finais = temas if temas is not None else (item.temas or classificar(texto_completo))

    db.delete_chunks(item.id)
    rag.delete_chunks(item.id)
    db.insert_chunks(item.id, chunks)
    rag.index_chunks(item, chunks)
    db.upsert_documento(
        {
            "id": item.id,
            "titulo": titulo or item.titulo,
            "tipo": tipo or item.tipo,
            "ano": ano if ano is not None else item.ano,
            "orgao": orgao or item.orgao,
            "url": item.url,
            "temas": temas_finais,
            "arquivo": str(arquivo),
            "chunks": len(chunks),
            "paginas": total_paginas,
            "importado_em": _now(),
            "categoria": item.categoria or categoria_de(item.tipo),
            "vigente": item.vigente,
            "situacao": item.situacao,
            "substituido_por": item.substituido_por,
        }
    )
    return {
        "id": item.id,
        "titulo": titulo or item.titulo,
        "chunks": len(chunks),
        "paginas": total_paginas,
        "temas": temas_finais,
        "pulado": False,
    }


def importar(req: ImportRequest) -> dict:
    settings = get_settings()
    db = Database(settings.db_path)
    rag = get_rag_index()

    ids = req.ids or [item.id for item in CATALOGO if item.importavel]
    iniciais = [i for i in (get_catalogo(x) for x in ids) if i is not None]
    mensagens: List[str] = []
    erros: List[str] = []

    _update(
        running=True,
        fase="iniciando",
        documento="",
        processados=0,
        total=len(iniciais),
        chunks=0,
        mensagens=[],
        erros=[],
        iniciado_em=_now(),
        concluido_em=None,
        resultado=None,
    )
    inicio = time.time()
    importados = 0
    total_chunks = 0
    try:
        for indice, item in enumerate(iniciais, start=1):
            _update(fase=f"importando {item.titulo}", documento=item.id)
            try:
                resultado = importar_documento(
                    item, db, rag, forcar=req.forcar, baixar_arquivo=req.baixar
                )
                total_chunks += resultado["chunks"]
                if resultado.get("pulado"):
                    mensagens.append(f"{item.titulo}: já importado ({resultado['chunks']} trechos)")
                else:
                    importados += 1
                    mensagens.append(
                        f"{item.titulo}: {resultado['chunks']} trechos, {resultado['paginas']} páginas"
                    )
            except Exception as exc:
                erros.append(f"{item.titulo}: {exc}")
                mensagens.append(f"{item.titulo}: erro - {exc}")
            db.log_sync("documentos", importados, f"item={item.id}")
            _update(processados=indice, chunks=total_chunks, mensagens=list(mensagens), erros=list(erros))
    finally:
        resposta = {
            "importados": importados,
            "chunks": total_chunks,
            "erros": erros,
            "duracao_segundos": round(time.time() - inicio, 1),
            "mensagens": mensagens,
        }
        _update(
            running=False,
            fase="concluido",
            duracao_segundos=resposta["duracao_segundos"],
            concluido_em=_now(),
            mensagens=mensagens,
            erros=erros,
            resultado=resposta,
            processados=len(iniciais),
        )
    return resposta


def start_import_background(req: ImportRequest) -> bool:
    if _estado()["running"]:
        return False

    def _run():
        try:
            importar(req)
        except Exception as exc:
            _update(running=False, fase=f"erro: {exc}", concluido_em=_now())

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return True


def importar_arquivo_local(
    caminho: Path,
    documento_id: str,
    titulo: str,
    tipo: str,
    ano: Optional[int],
    orgao: str,
    temas: List[str],
) -> dict:
    settings = get_settings()
    db = Database(settings.db_path)
    rag = get_rag_index()
    item = DocumentoCatalogo(
        id=documento_id,
        titulo=titulo,
        tipo=tipo,
        ano=ano,
        orgao=orgao,
        descricao="Documento importado localmente.",
        url="",
        formato="pdf" if caminho.suffix.lower() == ".pdf" else "html",
        temas=temas,
        importavel=False,
    )
    return importar_documento(
        item,
        db,
        rag,
        forcar=True,
        baixar_arquivo=False,
        arquivo=caminho,
        titulo=titulo,
        tipo=tipo,
        ano=ano,
        orgao=orgao,
        temas=temas,
    )
