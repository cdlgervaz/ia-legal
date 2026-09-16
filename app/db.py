import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from .models import Proposicao, ProposicaoDetalhe, Tramitacao

SCHEMA = """
CREATE TABLE IF NOT EXISTS proposicoes (
    id TEXT PRIMARY KEY,
    casa TEXT NOT NULL,
    tipo TEXT NOT NULL,
    numero TEXT NOT NULL,
    ano INTEGER NOT NULL,
    ementa TEXT NOT NULL,
    autor TEXT,
    data TEXT,
    url TEXT,
    situacao TEXT,
    orgao TEXT,
    temas TEXT,
    fonte TEXT,
    atualizado_em TEXT
);
CREATE INDEX IF NOT EXISTS idx_prop_casa ON proposicoes(casa);
CREATE INDEX IF NOT EXISTS idx_prop_tipo ON proposicoes(tipo);
CREATE INDEX IF NOT EXISTS idx_prop_ano ON proposicoes(ano);

CREATE TABLE IF NOT EXISTS tramitacoes (
    proposicao_id TEXT NOT NULL,
    sequencia INTEGER NOT NULL,
    data_hora TEXT,
    orgao TEXT,
    descricao TEXT,
    situacao TEXT,
    regime TEXT,
    PRIMARY KEY (proposicao_id, sequencia)
);
CREATE INDEX IF NOT EXISTS idx_tram_prop ON tramitacoes(proposicao_id);

CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    executado_em TEXT NOT NULL,
    fonte TEXT,
    inseridos INTEGER,
    detalhe TEXT
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def upsert_proposicao(self, prop: Proposicao) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO proposicoes
                    (id, casa, tipo, numero, ano, ementa, autor, data, url,
                     situacao, orgao, temas, fonte, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    ementa=excluded.ementa,
                    autor=excluded.autor,
                    data=excluded.data,
                    url=excluded.url,
                    situacao=excluded.situacao,
                    orgao=excluded.orgao,
                    temas=excluded.temas,
                    fonte=excluded.fonte,
                    atualizado_em=excluded.atualizado_em
                """,
                (
                    prop.id,
                    prop.casa,
                    prop.tipo,
                    prop.numero,
                    prop.ano,
                    prop.ementa,
                    prop.autor,
                    prop.data,
                    prop.url,
                    prop.situacao,
                    prop.orgao,
                    json.dumps(prop.temas, ensure_ascii=False),
                    prop.fonte,
                    _now(),
                ),
            )

    def replace_tramitacoes(self, proposicao_id: str, tramitacoes: Iterable[Tramitacao]) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM tramitacoes WHERE proposicao_id = ?", (proposicao_id,))
            conn.executemany(
                """
                INSERT OR REPLACE INTO tramitacoes
                    (proposicao_id, sequencia, data_hora, orgao, descricao, situacao, regime)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        proposicao_id,
                        t.sequencia if t.sequencia is not None else idx,
                        t.data_hora,
                        t.orgao,
                        t.descricao,
                        t.situacao,
                        t.regime,
                    )
                    for idx, t in enumerate(tramitacoes)
                ],
            )

    def _row_to_proposicao(self, row: sqlite3.Row) -> Proposicao:
        return Proposicao(
            id=row["id"],
            casa=row["casa"],
            tipo=row["tipo"],
            numero=row["numero"],
            ano=row["ano"],
            ementa=row["ementa"],
            autor=row["autor"],
            data=row["data"],
            url=row["url"],
            situacao=row["situacao"],
            orgao=row["orgao"],
            temas=json.loads(row["temas"]) if row["temas"] else [],
            fonte=row["fonte"],
        )

    def get_proposicao(self, proposicao_id: str) -> Optional[ProposicaoDetalhe]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM proposicoes WHERE id = ?", (proposicao_id,)
            ).fetchone()
            if row is None:
                return None
            prop = self._row_to_proposicao(row)
            tram_rows = conn.execute(
                "SELECT * FROM tramitacoes WHERE proposicao_id = ? ORDER BY sequencia",
                (proposicao_id,),
            ).fetchall()
        detalhe = ProposicaoDetalhe(**prop.model_dump())
        detalhe.atualizado_em = row["atualizado_em"]
        detalhe.tramitacoes = [
            Tramitacao(
                sequencia=t["sequencia"],
                data_hora=t["data_hora"],
                orgao=t["orgao"],
                descricao=t["descricao"],
                situacao=t["situacao"],
                regime=t["regime"],
            )
            for t in tram_rows
        ]
        return detalhe

    def all_proposicoes(self) -> List[Proposicao]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM proposicoes").fetchall()
        return [self._row_to_proposicao(r) for r in rows]

    def get_many(self, ids: List[str]) -> List[Proposicao]:
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        with self.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM proposicoes WHERE id IN ({placeholders})", ids
            ).fetchall()
        by_id = {r["id"]: self._row_to_proposicao(r) for r in rows}
        return [by_id[i] for i in ids if i in by_id]

    def list_proposicoes(
        self,
        casa: Optional[str] = None,
        tipo: Optional[str] = None,
        ano_de: Optional[int] = None,
        ano_ate: Optional[int] = None,
        busca: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Proposicao]:
        clauses: List[str] = []
        params: List = []
        if casa:
            clauses.append("casa = ?")
            params.append(casa)
        if tipo:
            clauses.append("tipo = ?")
            params.append(tipo)
        if ano_de is not None:
            clauses.append("ano >= ?")
            params.append(ano_de)
        if ano_ate is not None:
            clauses.append("ano <= ?")
            params.append(ano_ate)
        if busca:
            clauses.append("(ementa LIKE ? OR id LIKE ?)")
            params.extend([f"%{busca}%", f"%{busca}%"])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([limit, offset])
        with self.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM proposicoes {where} ORDER BY ano DESC, id DESC LIMIT ? OFFSET ?",
                params,
            ).fetchall()
        return [self._row_to_proposicao(r) for r in rows]

    def buscar_textual(self, query: str, limit: int = 20) -> List[Proposicao]:
        termos = [t for t in _tokenize(query) if len(t) > 2]
        if not termos:
            return []
        score_parts = []
        params: List = []
        for termo in termos:
            score_parts.append("(CASE WHEN ementa LIKE ? THEN 1 ELSE 0 END)")
            params.append(f"%{termo}%")
        score_expr = " + ".join(score_parts)
        sql = f"""
            SELECT *, ({score_expr}) AS score
            FROM proposicoes
            WHERE ({score_expr}) > 0
            ORDER BY score DESC, ano DESC
            LIMIT ?
        """
        exec_params = list(params) + list(params) + [limit]
        with self.connect() as conn:
            rows = conn.execute(sql, exec_params).fetchall()
        return [self._row_to_proposicao(r) for r in rows]

    def stats(self) -> dict:
        with self.connect() as conn:
            total = conn.execute("SELECT COUNT(*) AS c FROM proposicoes").fetchone()["c"]
            por_casa = {
                r["casa"]: r["c"]
                for r in conn.execute(
                    "SELECT casa, COUNT(*) AS c FROM proposicoes GROUP BY casa"
                ).fetchall()
            }
            por_tipo = {
                r["tipo"]: r["c"]
                for r in conn.execute(
                    "SELECT tipo, COUNT(*) AS c FROM proposicoes GROUP BY tipo ORDER BY c DESC"
                ).fetchall()
            }
            por_ano = {
                str(r["ano"]): r["c"]
                for r in conn.execute(
                    "SELECT ano, COUNT(*) AS c FROM proposicoes GROUP BY ano ORDER BY ano DESC"
                ).fetchall()
            }
            ultimo = conn.execute(
                "SELECT MAX(atualizado_em) AS u FROM proposicoes"
            ).fetchone()["u"]
        return {
            "total": total,
            "por_casa": por_casa,
            "por_tipo": por_tipo,
            "por_ano": por_ano,
            "atualizado_em": ultimo,
        }

    def log_sync(self, fonte: str, inseridos: int, detalhe: str = "") -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO sync_log (executado_em, fonte, inseridos, detalhe) VALUES (?, ?, ?, ?)",
                (_now(), fonte, inseridos, detalhe),
            )


def _tokenize(text: str) -> List[str]:
    import re

    return re.findall(r"[0-9a-záàâãéêíóôõúüç]+", text.lower())
