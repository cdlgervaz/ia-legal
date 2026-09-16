import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS universidades (
    sigla TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    categoria TEXT,
    uf TEXT,
    regiao TEXT,
    dominio TEXT,
    atualizado_em TEXT
);

CREATE TABLE IF NOT EXISTS documentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    universidade TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    titulo TEXT,
    tipo TEXT,
    caminho TEXT,
    status TEXT,
    chars INTEGER,
    paginas INTEGER,
    erro TEXT,
    coletado_em TEXT
);
CREATE INDEX IF NOT EXISTS idx_doc_universidade ON documentos(universidade);
CREATE INDEX IF NOT EXISTS idx_doc_status ON documentos(status);

CREATE TABLE IF NOT EXISTS disciplinas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    documento_id INTEGER NOT NULL,
    universidade TEXT NOT NULL,
    nome TEXT NOT NULL,
    trecho TEXT,
    palavras_chave TEXT,
    score INTEGER,
    pagina INTEGER,
    UNIQUE(documento_id, nome)
);
CREATE INDEX IF NOT EXISTS idx_disc_universidade ON disciplinas(universidade);

CREATE TABLE IF NOT EXISTS coleta_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    universidade TEXT,
    executado_em TEXT NOT NULL,
    documentos INTEGER,
    disciplinas INTEGER,
    detalhe TEXT
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path, timeout=60)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init(self) -> None:
        with self.connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(SCHEMA)

    def upsert_universidade(self, sigla: str, nome: str, categoria: str, uf: str,
                            regiao: str, dominio: Optional[str]) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO universidades (sigla, nome, categoria, uf, regiao, dominio, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sigla) DO UPDATE SET
                    nome=excluded.nome, categoria=excluded.categoria, uf=excluded.uf,
                    regiao=excluded.regiao,
                    dominio=COALESCE(excluded.dominio, universidades.dominio),
                    atualizado_em=excluded.atualizado_em
                """,
                (sigla, nome, categoria, uf, regiao, dominio, _now()),
            )

    def get_dominio(self, sigla: str) -> Optional[str]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT dominio FROM universidades WHERE sigla = ?", (sigla,)
            ).fetchone()
        return row["dominio"] if row else None

    def documento_por_url(self, url: str) -> Optional[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM documentos WHERE url = ?", (url,)
            ).fetchone()

    def inserir_documento(self, universidade: str, url: str, titulo: str, tipo: str,
                          caminho: Optional[str], status: str, chars: int, paginas: int,
                          erro: Optional[str] = None) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO documentos
                    (universidade, url, titulo, tipo, caminho, status, chars, paginas, erro, coletado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    titulo=excluded.titulo, tipo=excluded.tipo, caminho=excluded.caminho,
                    status=excluded.status, chars=excluded.chars, paginas=excluded.paginas,
                    erro=excluded.erro, coletado_em=excluded.coletado_em
                """,
                (universidade, url, titulo, tipo, caminho, status, chars, paginas,
                 erro, _now()),
            )
            if cur.lastrowid:
                return cur.lastrowid
            row = conn.execute(
                "SELECT id FROM documentos WHERE url = ?", (url,)
            ).fetchone()
            return row["id"]

    def limpar_disciplinas(self, documento_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM disciplinas WHERE documento_id = ?", (documento_id,))

    def inserir_disciplinas(self, documento_id: int, universidade: str,
                            disciplinas: Iterable[dict]) -> int:
        inseridas = 0
        with self.connect() as conn:
            for d in disciplinas:
                cur = conn.execute(
                    """
                    INSERT OR IGNORE INTO disciplinas
                        (documento_id, universidade, nome, trecho, palavras_chave, score, pagina)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        documento_id,
                        universidade,
                        d["nome"],
                        d.get("trecho"),
                        json.dumps(d.get("palavras_chave", []), ensure_ascii=False),
                        d.get("score", 0),
                        d.get("pagina"),
                    ),
                )
                inseridas += cur.rowcount
        return inseridas

    def log(self, universidade: str, documentos: int, disciplinas: int, detalhe: str = "") -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO coleta_log (universidade, executado_em, documentos, disciplinas, detalhe)
                VALUES (?, ?, ?, ?, ?)
                """,
                (universidade, _now(), documentos, disciplinas, detalhe),
            )

    def listar_disciplinas(self, universidade: Optional[str] = None,
                           texto: Optional[str] = None, limit: int = 500) -> list[dict]:
        clausulas, params = [], []
        if universidade:
            clausulas.append("d.universidade = ?")
            params.append(universidade.upper())
        if texto:
            clausulas.append("(d.nome LIKE ? OR d.trecho LIKE ? OR d.palavras_chave LIKE ?)")
            params.extend([f"%{texto}%"] * 3)
        where = f"WHERE {' AND '.join(clausulas)}" if clausulas else ""
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT d.*, doc.url, doc.titulo AS documento_titulo, doc.caminho,
                       u.nome AS universidade_nome, u.uf, u.categoria
                FROM disciplinas d
                JOIN documentos doc ON doc.id = d.documento_id
                LEFT JOIN universidades u ON u.sigla = d.universidade
                {where}
                ORDER BY d.universidade, d.score DESC, d.nome
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [dict(r) for r in rows]

    def estatisticas(self) -> dict:
        with self.connect() as conn:
            universidades = conn.execute(
                "SELECT COUNT(*) AS c FROM universidades"
            ).fetchone()["c"]
            documentos = conn.execute(
                "SELECT COUNT(*) AS c FROM documentos WHERE status = 'ok'"
            ).fetchone()["c"]
            disciplinas = conn.execute(
                "SELECT COUNT(*) AS c FROM disciplinas"
            ).fetchone()["c"]
            por_universidade = [
                dict(r) for r in conn.execute(
                    """
                    SELECT universidade, COUNT(*) AS disciplinas
                    FROM disciplinas GROUP BY universidade ORDER BY disciplinas DESC
                    """
                ).fetchall()
            ]
        return {
            "universidades": universidades,
            "documentos_ok": documentos,
            "disciplinas": disciplinas,
            "por_universidade": por_universidade,
        }
