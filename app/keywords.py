import re
import unicodedata

TECH_KEYWORDS = [
    "tecnologia",
    "tecnologico",
    "ciencia e tecnologia",
    "inovacao",
    "startup",
    "digital",
    "digitalizacao",
    "transformacao digital",
    "governo digital",
    "identidade digital",
    "inclusao digital",
    "letramento digital",
    "internet",
    "banda larga",
    "conectividade",
    "5g",
    "telecomunicacoes",
    "telefonia",
    "espectro",
    "informatica",
    "computacao",
    "computador",
    "software",
    "programa de computador",
    "aplicativo",
    "algoritmo",
    "inteligencia artificial",
    "aprendizado de maquina",
    "machine learning",
    "robotica",
    "automacao",
    "drone",
    "veiculo autonomo",
    "carro autonomo",
    "semicondutor",
    "chip",
    "nanotecnologia",
    "biotecnologia",
    "realidade virtual",
    "realidade aumentada",
    "metaverso",
    "blockchain",
    "criptomoeda",
    "moeda digital",
    "ativo virtual",
    "nuvem",
    "computacao em nuvem",
    "datacenter",
    "centro de dados",
    "dados pessoais",
    "protecao de dados",
    "privacidade",
    "lgpd",
    "ciberseguranca",
    "seguranca cibernetica",
    "crime cibernetico",
    "cibercrime",
    "seguranca da informacao",
    "compartilhamento de dados",
    "abertura de dados",
    "dados abertos",
    "big data",
    "internet das coisas",
    "rede social",
    "plataforma digital",
    "economia digital",
    "comercio eletronico",
    "assinatura eletronica",
    "documento eletronico",
    "processo eletronico",
    "protocolo eletronico",
    "desinformacao",
    "fake news",
    "moderacao de conteudo",
    "tecnologia da informacao",
    "tics",
    "pesquisa e desenvolvimento",
    "propriedade intelectual",
    "software livre",
    "codigo aberto",
    "interoperabilidade",
    "rastreamento",
    "geolocalizacao",
    "biometria",
    "reconhecimento facial",
    "vigilancia",
    "smartphone",
    "dispositivo",
    "hardware",
    "telemedicina",
    "ensino a distancia",
    "educacao digital",
    "streaming",
    "jogos eletronicos",
    "e-sports",
    "impressao 3d",
    "energia renovavel",
]

_PATTERNS = None


def _normalize(text: str) -> str:
    text = (text or "").lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return f" {text.strip()} "


def _get_patterns():
    global _PATTERNS
    if _PATTERNS is None:
        _PATTERNS = [(_normalize(k).strip(), re.compile(r"\b" + re.escape(k) + r"\b")) for k in TECH_KEYWORDS]
    return _PATTERNS


def termos_encontrados(text: str) -> list:
    normalizado = _normalize(text)
    achados = []
    for termo, regex in _get_patterns():
        if regex.search(normalizado):
            achados.append(termo)
    return achados


def is_tech(text: str, minimo: int = 1) -> bool:
    return len(termos_encontrados(text)) >= minimo
