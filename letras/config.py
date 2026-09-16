import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LETRAS_DIR = DATA_DIR / "letras"
DOCS_DIR = LETRAS_DIR / "documentos"
DB_PATH = LETRAS_DIR / "letras.db"
UNIVERSIDADES_CSV = DATA_DIR / "universidades_publicas.csv"
CACHE_BUSCA = LETRAS_DIR / "cache_busca.json"

USER_AGENT = os.getenv(
    "LETRAS_USER_AGENT",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0 Safari/537.36 pesquisa-academica/1.0",
)


@dataclass
class Config:
    http_timeout: float = float(os.getenv("LETRAS_HTTP_TIMEOUT", "45"))
    http_delay: float = float(os.getenv("LETRAS_HTTP_DELAY", "1.0"))
    http_retries: int = int(os.getenv("LETRAS_HTTP_RETRIES", "3"))
    search_delay: float = float(os.getenv("LETRAS_SEARCH_DELAY", "3.0"))
    search_region: str = os.getenv("LETRAS_SEARCH_REGION", "br-pt")
    max_resultados_busca: int = int(os.getenv("LETRAS_MAX_RESULTADOS", "15"))
    max_documentos_por_universidade: int = int(
        os.getenv("LETRAS_MAX_DOCS", "12")
    )
    max_documentos_total: int = int(os.getenv("LETRAS_MAX_DOCS_TOTAL", "20"))
    workers: int = max(1, int(os.getenv("LETRAS_WORKERS", "1")))
    usar_cache_busca: bool = os.getenv("LETRAS_CACHE_BUSCA", "1") not in {"0", "false", "False"}

    docs_dir: Path = DOCS_DIR
    db_path: Path = DB_PATH
    universidades_csv: Path = UNIVERSIDADES_CSV
    cache_path: Path = CACHE_BUSCA


def get_config() -> Config:
    cfg = Config()
    cfg.docs_dir.mkdir(parents=True, exist_ok=True)
    return cfg


class CacheBusca:
    """Cache simples em JSON para não repetir consultas de busca."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self._dados: dict[str, list] = {}
        if path.exists():
            try:
                self._dados = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._dados = {}

    def get(self, chave: str) -> Optional[list]:
        with self._lock:
            return self._dados.get(chave)

    def set(self, chave: str, valor: list) -> None:
        with self._lock:
            self._dados[chave] = valor
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(self._dados, ensure_ascii=False, indent=1), encoding="utf-8"
            )
