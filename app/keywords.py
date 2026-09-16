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

EDUCACAO_KEYWORDS = [
    "educacao",
    "educacional",
    "formacao de professores",
    "formacao inicial",
    "formacao continuada",
    "formacao docente",
    "professor",
    "docente",
    "licenciatura",
    "pedagogia",
    "curriculo",
    "diretrizes curriculares",
    "base nacional comum curricular",
    "bncc",
    "educacao basica",
    "educacao infantil",
    "ensino fundamental",
    "ensino medio",
    "educacao superior",
    "educacao a distancia",
    "ensino remoto",
    "ensino hibrido",
    "escola",
    "estudante",
    "aluno",
    "aprendizagem",
    "alfabetizacao",
    "avaliacao educacional",
    "conselho nacional de educacao",
    "cne",
    "mec",
    "capes",
    "inep",
    "plano nacional de educacao",
    "pne",
    "politica nacional de educacao",
    "educacao digital",
    "cultura digital",
    "letramento digital",
    "secretaria de educacao",
    "rede publica de ensino",
    "instituicao de ensino",
    "curso de graduacao",
    "pos-graduacao",
]

_PATTERNS = None
_EDU_PATTERNS = None


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


def _get_edu_patterns():
    global _EDU_PATTERNS
    if _EDU_PATTERNS is None:
        _EDU_PATTERNS = [
            (_normalize(k).strip(), re.compile(r"\b" + re.escape(_normalize(k).strip()) + r"\b"))
            for k in EDUCACAO_KEYWORDS
        ]
    return _EDU_PATTERNS


def termos_educacao(text: str) -> list:
    normalizado = _normalize(text)
    achados = []
    for termo, regex in _get_edu_patterns():
        if regex.search(normalizado):
            achados.append(termo)
    return achados


def is_educacao(text: str, minimo: int = 1) -> bool:
    return len(termos_educacao(text)) >= minimo


def relevante(text: str) -> bool:
    return is_tech(text) or is_educacao(text)


def termos_relevantes(text: str) -> list:
    vistos = []
    for termo in termos_encontrados(text) + termos_educacao(text):
        if termo not in vistos:
            vistos.append(termo)
    return vistos
