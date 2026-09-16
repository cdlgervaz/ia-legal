from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "IA Legal - Políticas Educacionais"
    data_dir: Path = BASE_DIR / "data"
    host: str = "127.0.0.1"
    port: int = 8000
    app_user: str = "professor"
    app_password: Optional[str] = None

    llm_provider: str = "ollama"
    llm_base_url: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_model: str = "qwen2.5:1.5b"
    llm_model_fallbacks: str = ""
    llm_temperature: float = 0.2
    llm_max_tokens: int = 700

    embedding_provider: str = "chroma"
    embedding_model: str = "text-embedding-3-small"

    http_timeout: float = 30.0
    http_delay: float = 0.25
    request_retries: int = 3

    default_search_limit: int = 8
    chunk_size: int = 1400
    chunk_overlap: int = 250
    max_context_chars: int = 24000

    @property
    def db_path(self) -> Path:
        return self.data_dir / "ialegal.db"

    @property
    def chroma_path(self) -> Path:
        return self.data_dir / "chroma"

    @property
    def docs_dir(self) -> Path:
        self.data_dir.joinpath("documentos").mkdir(parents=True, exist_ok=True)
        return self.data_dir / "documentos"

    def resolved_llm_key(self) -> Optional[str]:
        if self.llm_api_key:
            return self.llm_api_key
        if self.llm_provider == "ollama":
            return "ollama"
        return None

    def llm_enabled(self) -> bool:
        if self.llm_provider in ("none", "off"):
            return False
        return bool(self.resolved_llm_key())

    def resolved_embedding_provider(self) -> str:
        if self.embedding_provider != "auto":
            return self.embedding_provider
        if self.llm_api_key:
            return "openai"
        return "chroma"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
