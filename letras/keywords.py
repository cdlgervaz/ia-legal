import re
import unicodedata

TERMOS_TECNOLOGIA = [
    "tecnologia", "tecnologias", "tecnologico", "tecnologica", "tecnologicas",
    "tdic", "tdics", "tic", "tics",
    "tecnologias digitais", "tecnologias da informacao e comunicacao",
    "tecnologia educacional", "tecnologias educacionais",
    "letramento digital", "letramentos digitais", "multiletramento", "multiletramentos",
    "cultura digital", "mundo digital", "ambiente digital", "midias digitais",
    "informatica", "computacao", "computador", "computacional",
    "internet", "web", "online", "software", "aplicativo", "aplicativos",
    "digital", "virtual", "cibercultura", "ciberespaco",
    "educacao a distancia", "ead", "ensino remoto", "ensino hibrido", "aulas remotas",
    "ambiente virtual de aprendizagem", "ava", "moodle",
    "gamificacao", "jogos digitais", "podcast", "hipertexto", "hipermidia",
    "inteligencia artificial", "chatgpt", "robotica", "programacao",
    "redes sociais", "midias sociais", "audiovisual", "multimodal", "multimodalidade",
    "recursos digitais", "recursos tecnologicos", "ferramentas digitais",
    "linguagem digital", "escrita digital", "nativos digitais",
    "processamento de linguagem natural", "pln", "corpus", "corpora",
    "mineracao de texto", "big data", "metaverso", "realidade aumentada", "realidade virtual",
    "producao de video", "edicao de video", "fotografia digital", "design digital",
    "midia", "midias", "suporte digital", "dispositivos moveis", "mobile",
]

TERMOS_COM_FRONTEIRA = {"tic", "tics", "tdic", "tdics", "ead", "ava", "pln", "web", "ia"}


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower()


def termo_presente(texto_norm: str, termo: str) -> bool:
    termo_norm = normalizar(termo)
    if termo_norm in TERMOS_COM_FRONTEIRA:
        return re.search(rf"(?<![a-z0-9]){re.escape(termo_norm)}(?![a-z0-9])", texto_norm) is not None
    return termo_norm in texto_norm


def palavras_encontradas(texto: str) -> list[str]:
    texto_norm = normalizar(texto)
    encontrados: list[str] = []
    for termo in TERMOS_TECNOLOGIA:
        if termo_presente(texto_norm, termo):
            encontrados.append(termo)
    return encontrados


INDICIOS_DISCIPLINA = [
    "disciplina", "componente curricular", "matriz curricular", "grade curricular",
    "ementa", "conteudo programatico", "carga horaria", "creditos",
    "pratica pedagogica", "pratica de ensino", "estagio", "licenciatura",
]

TERMOS_CURSO = ["letras", "licenciatura em letras", "curso de letras"]

ESTRUTURA_CODIGO = re.compile(r"^[A-Z]{2,8}[\s\-]?\d{2,6}[A-Z]?\b")
ESTRUTURA_CARGA = re.compile(
    r"(\d{2,3})\s*(h|h/a|horas|hrs|creditos|cr|cred)\b", re.IGNORECASE
)


def parece_disciplina(linha: str) -> bool:
    linha = linha.strip()
    if not (4 <= len(linha) <= 200):
        return False
    letras = [c for c in linha if c.isalpha()]
    if not letras:
        return False
    if len(linha) > 0 and sum(c.isdigit() for c in linha) / len(linha) > 0.5:
        return False
    return True
