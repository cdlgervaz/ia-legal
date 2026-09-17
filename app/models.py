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


class DocumentoCatalogo(BaseModel):
    id: str
    titulo: str
    tipo: str
    ano: Optional[int] = None
    orgao: str = ""
    descricao: str = ""
    url: str = ""
    formato: str = "pdf"
    temas: List[str] = Field(default_factory=list)
    importavel: bool = True
    observacao: Optional[str] = None
    categoria: str = ""
    vigente: Optional[bool] = None
    situacao: Optional[str] = None
    substituido_por: Optional[str] = None


class DocumentoInfo(DocumentoCatalogo):
    importado: bool = False
    chunks: int = 0
    paginas: int = 0
    importado_em: Optional[str] = None
    arquivo: Optional[str] = None


class TrechoDocumento(BaseModel):
    documento_id: str
    titulo: str = ""
    pagina: Optional[int] = None
    trecho: str
    posicao: int = 0


class SearchRequest(BaseModel):
    query: str
    limit: int = 8
    casa: Optional[str] = None
    tipo: Optional[str] = None
    categoria: Optional[str] = None
    ano_de: Optional[int] = None
    ano_ate: Optional[int] = None
    tema: Optional[str] = None
    documento_id: Optional[str] = None


class SearchHit(BaseModel):
    proposicao: Proposicao
    score: float
    trecho: Optional[str] = None
    origem: str = "proposicao"
    documento_id: Optional[str] = None
    titulo: Optional[str] = None
    pagina: Optional[int] = None
    categoria: Optional[str] = None
    vigente: Optional[bool] = None
    situacao: Optional[str] = None
    substituido_por: Optional[str] = None


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
    categoria: Optional[str] = None
    ano_de: Optional[int] = None
    ano_ate: Optional[int] = None
    tema: Optional[str] = None
    documento_id: Optional[str] = None


class ChatResponse(BaseModel):
    query: str
    resposta: str
    modo: str
    fontes: List[SearchHit] = Field(default_factory=list)


class ImportRequest(BaseModel):
    ids: List[str] = Field(default_factory=list)
    forcar: bool = False
    baixar: bool = True


class SyncRequest(BaseModel):
    camara: bool = True
    senado: bool = True
    cne: bool = True
    diario_oficial: bool = True
    anos: List[int] = Field(default_factory=list)
    tipos: List[str] = Field(default_factory=lambda: ["PL", "PEC", "PLP", "MPV"])
    max_itens_por_ano: int = 0
    ano_inicial: int = 1988
    buscar_tramitacoes: bool = True
    incluir_comunicacoes: bool = True
    cne_max: int = 200
    cne_extrair_texto: bool = True
    dou_paginas: int = 3
    dou_consultas: List[str] = Field(default_factory=list)


class SyncResponse(BaseModel):
    camara: int = 0
    senado: int = 0
    cne: int = 0
    diario_oficial: int = 0
    indexados: int = 0
    duracao_segundos: float = 0.0
    mensagens: List[str] = Field(default_factory=list)
