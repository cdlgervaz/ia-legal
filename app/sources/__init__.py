from .camara import CamaraClient, TEMA_CIENCIA_TECNOLOGIA, TEMA_COMUNICACOES
from .cne import CneClient
from .dou import DouClient
from .senado import SenadoClient

__all__ = [
    "CamaraClient",
    "SenadoClient",
    "CneClient",
    "DouClient",
    "TEMA_CIENCIA_TECNOLOGIA",
    "TEMA_COMUNICACOES",
]
