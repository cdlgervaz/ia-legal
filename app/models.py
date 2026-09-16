from typing import List, Optional

from pydantic import BaseModel, Field


class Tramitacao(BaseModel):
    sequencia: Optional[int] = None
    data_hora: Optional[str] = None
    orgao: Optional[str] = None
    descricao: Optional[str] = None
    situacao: Optional[str] = None
    regime: Optional[str] = None


class Proposicao(BaseModel):
    id: str
    casa: str
    tipo: str
    numero: str
    ano: int
    ementa: str
    autor: Optional[str] = None
    data: Optional[str] = None
    url: Optional[str] = None
    situacao: Optional[str] = None
    orgao: Optional[str] = None
    temas: List[str] = Field(default_factory=list)
    fonte: Optional[str] = None


class ProposicaoDetalhe(Proposicao):
    tramitacoes: List[Tramitacao] = Field(default_factory=list)
    atualizado_em: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    limit: int = 8
    casa: Optional[str] = None
    tipo: Optional[str] = None
    ano_de: Optional[int] = None
    ano_ate: Optional[int] = None


class SearchHit(BaseModel):
    proposicao: Proposicao
    score: float
    trecho: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    modo: str
    total: int
    resultados: List[SearchHit] = Field(default_factory=list)


class ChatRequest(BaseModel):
    query: str
    limit: int = 8
    casa: Optional[str] = None
    tipo: Optional[str] = None
    ano_de: Optional[int] = None
    ano_ate: Optional[int] = None


class ChatResponse(BaseModel):
    query: str
    resposta: str
    modo: str
    fontes: List[SearchHit] = Field(default_factory=list)


class SyncRequest(BaseModel):
    camara: bool = True
    senado: bool = True
    anos: List[int] = Field(default_factory=list)
    tipos: List[str] = Field(default_factory=lambda: ["PL", "PEC", "PLP", "MPV"])
    max_itens_por_ano: int = 60
    buscar_tramitacoes: bool = True
    incluir_comunicacoes: bool = True


class SyncResponse(BaseModel):
    camara: int = 0
    senado: int = 0
    indexados: int = 0
    duracao_segundos: float = 0.0
    mensagens: List[str] = Field(default_factory=list)
