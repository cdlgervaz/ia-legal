from typing import Dict, List

from .texto import contem_termo, normalizar

TEMAS: Dict[str, dict] = {
    "curriculo": {
        "rotulo": "Currículo",
        "descricao": "BNCC, currículos, competências, organização da educação básica",
        "palavras": [
            "curriculo",
            "curriculos",
            "base nacional comum curricular",
            "bncc",
            "bncc computacao",
            "diretrizes curriculares",
            "competencias",
            "habilidades",
            "itinerario formativo",
            "organizacao curricular",
            "componente curricular",
            "area de conhecimento",
            "educacao infantil",
            "ensino fundamental",
            "ensino medio",
            "anos iniciais",
            "anos finais",
            "educacao basica",
            "projeto politico pedagogico",
            "parte diversificada",
            "temas contemporaneos",
        ],
    },
    "gestao": {
        "rotulo": "Gestão",
        "descricao": "Gestão escolar e democrática, direção, sistemas e planejamento",
        "palavras": [
            "gestao",
            "gestao escolar",
            "gestao democratica",
            "diretor",
            "diretor escolar",
            "diretores escolares",
            "coordenacao pedagogica",
            "conselho escolar",
            "conselhos de educacao",
            "conselho nacional de educacao",
            "sistema nacional de educacao",
            "regime de colaboracao",
            "autonomia escolar",
            "autonomia universitaria",
            "planejamento educacional",
            "plano nacional de educacao",
            "plano estadual de educacao",
            "plano municipal de educacao",
            "pne",
            "censo escolar",
            "governanca",
            "instituicao de ensino",
            "rede publica de ensino",
            "secretaria de educacao",
        ],
    },
    "formacao_docente": {
        "rotulo": "Formação docente",
        "descricao": "BNC-Formação, licenciaturas, formação inicial e continuada",
        "palavras": [
            "formacao de professores",
            "formacao de docentes",
            "formacao inicial",
            "formacao continuada",
            "formacao docente",
            "bnc formacao",
            "base nacional comum de formacao",
            "diretrizes curriculares nacionais para a formacao",
            "licenciatura",
            "licenciaturas",
            "pedagogia",
            "docencia",
            "docente",
            "professor",
            "professores",
            "estagio supervisionado",
            "pratica de ensino",
            "residencia pedagogica",
            "pibid",
            "plano de carreira do magisterio",
            "valorizacao dos profissionais da educacao",
            "saberes docentes",
        ],
    },
    "avaliacao": {
        "rotulo": "Avaliação",
        "descricao": "Avaliação da aprendizagem, avaliações externas e indicadores",
        "palavras": [
            "avaliacao",
            "avaliacao da aprendizagem",
            "avaliacao institucional",
            "avaliacoes externas",
            "instrumentos de avaliacao",
            "recuperacao",
            "saeb",
            "ideb",
            "censo escolar",
            "enade",
            "exame nacional",
            "indicadores educacionais",
            "qualidade da educacao",
            "rendimento escolar",
            "fluxo escolar",
        ],
    },
    "financiamento": {
        "rotulo": "Financiamento",
        "descricao": "FUNDEB, PNE, custo aluno e orçamento da educação",
        "palavras": [
            "financiamento",
            "financiamento da educacao",
            "fundeb",
            "fundo de manutencao e desenvolvimento",
            "custo aluno",
            "custo aluno qualidade",
            "caqi",
            "caq",
            "orcamento",
            "recursos publicos",
            "salario educacao",
            "vinculacao constitucional",
            "manutencao e desenvolvimento do ensino",
            "gasto publico",
            "arrecadacao",
            "precatórios",
        ],
    },
    "tecnologia": {
        "rotulo": "Tecnologia e educação digital",
        "descricao": "Educação digital, computação, conectividade e dispositivos",
        "palavras": [
            "tecnologia",
            "tecnologias",
            "tecnologia da informacao",
            "tic",
            "tics",
            "tdic",
            "tdics",
            "educacao digital",
            "cultura digital",
            "letramento digital",
            "inclusao digital",
            "computacao",
            "pensamento computacional",
            "programacao",
            "robotica",
            "plataforma digital",
            "ambiente virtual",
            "ambientes virtuais de aprendizagem",
            "ensino hibrido",
            "educacao a distancia",
            "ensino remoto",
            "dispositivos digitais",
            "celular",
            "smartphone",
            "internet",
            "conectividade",
            "banda larga",
            "jogos digitais",
            "midia",
            "redes sociais",
            "nuvem",
            "software",
            "dados abertos",
            "governo digital",
            "transformacao digital",
        ],
    },
    "ia_educacao": {
        "rotulo": "IA na educação",
        "descricao": "Uso pedagógico da IA, marcos regulatórios e planos de IA",
        "palavras": [
            "inteligencia artificial",
            "ia generativa",
            "aprendizado de maquina",
            "machine learning",
            "algoritmo",
            "algoritmos",
            "chatbot",
            "chatgpt",
            "tutoria inteligente",
            "sistemas de tutoria",
            "plano brasileiro de inteligencia artificial",
            "pbia",
            "estrategia brasileira de inteligencia artificial",
            "ebia",
            "marco legal da inteligencia artificial",
            "projeto de lei 2338",
            "automacao",
            "dados pessoais",
            "lgpd",
            "protecao de dados",
            "vies algoritmico",
            "supervisao humana",
        ],
    },
    "inclusao": {
        "rotulo": "Inclusão e diversidade",
        "descricao": "Educação especial, acessibilidade e educação para a diversidade",
        "palavras": [
            "inclusao",
            "inclusiva",
            "educacao especial",
            "pessoas com deficiencia",
            "deficiencia",
            "acessibilidade",
            "educacao indigena",
            "educacao quilombola",
            "educacao do campo",
            "educacao escolar indigena",
            "diversidade",
            "equidade",
            "direitos humanos",
            "relacoes etnico raciais",
            "educacao antirracista",
            "genero",
            "educacao ambiental",
        ],
    },
}


def lista_temas() -> List[dict]:
    return [
        {"id": tema, "rotulo": dados["rotulo"], "descricao": dados.get("descricao", "")}
        for tema, dados in TEMAS.items()
    ]


def rotulo(tema: str) -> str:
    dados = TEMAS.get(tema)
    return dados["rotulo"] if dados else tema


def classificar(texto: str, maximo: int = 3) -> List[str]:
    if not texto:
        return []
    normalizado = normalizar(texto)
    if not normalizado:
        return []
    pontuacao: List[tuple] = []
    for tema, dados in TEMAS.items():
        pontos = 0.0
        for palavra in dados["palavras"]:
            if contem_termo(normalizado, palavra):
                pontos += 1.0 + (0.5 if " " in palavra else 0.0)
        if pontos > 0:
            pontuacao.append((tema, pontos))
    pontuacao.sort(key=lambda par: par[1], reverse=True)
    return [tema for tema, _ in pontuacao[:maximo]]
