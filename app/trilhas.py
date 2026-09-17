from typing import List, Optional

from .catalog import get as get_catalogo

TRILHAS: List[dict] = [
    {
        "id": "federalismo",
        "titulo": "Federalismo e organização da educação",
        "descricao": "Como se organiza a oferta educacional no Brasil: competências da União, Estados, "
        "Municípios e Distrito Federal, regime de colaboração e sistemas de ensino.",
        "perguntas": [
            "Quais são as competências da União, dos Estados e dos Municípios na educação?",
            "O que é o regime de colaboração entre os entes federados?",
            "Como a LDB organiza os sistemas de ensino?",
        ],
        "consulta": "organização da educação regime de colaboração sistemas de ensino",
        "documentos": ["cf-1988", "ldb-9394-1996", "pne-13005-2014"],
    },
    {
        "id": "financiamento",
        "titulo": "Financiamento e FUNDEB",
        "descricao": "Fontes de recursos, vinculação constitucional, FUNDEB e planejamento decenal.",
        "perguntas": [
            "De onde vêm os recursos da educação pública?",
            "Como funciona o FUNDEB e o que mudou com a Lei 14.113/2020?",
            "O que o PNE previa para o financiamento e qual o prazo?",
        ],
        "consulta": "financiamento da educação FUNDEB recursos vinculados",
        "documentos": ["cf-1988", "fundeb-14113-2020", "pne-13005-2014"],
    },
    {
        "id": "curriculo",
        "titulo": "Currículo e BNCC",
        "descricao": "Da organização por disciplinas à Base Nacional Comum Curricular: o que mudou e o "
        "que foi substituído.",
        "perguntas": [
            "O que é a BNCC e como ela se relaciona com os PCN?",
            "Quais documentos foram substituídos pela BNCC?",
            "Como a BNCC do Ensino Médio se organiza?",
        ],
        "consulta": "currículo BNCC diretrizes curriculares parâmetros",
        "documentos": [
            "bncc-ei-ef",
            "bncc-em",
            "res-cne-ceb-4-2010",
            "pcn-introducao-1997",
            "pcn-em-1999",
            "res-cne-ceb-2-2012",
            "res-cne-ceb-3-2018",
        ],
    },
    {
        "id": "formacao-docente",
        "titulo": "Formação inicial e continuada de docentes",
        "descricao": "Diretrizes para a formação de professores, BNC-Formação e BNC-Formação Continuada.",
        "perguntas": [
            "Quais são as atuais diretrizes para a formação inicial de docentes?",
            "O que é a BNC-Formação e a BNC-Formação Continuada?",
            "Como as políticas de formação de docentes evoluíram?",
        ],
        "consulta": "formação de professores diretrizes curriculares BNC-Formação",
        "documentos": [
            "res-cne-cp-2-2019",
            "res-cne-cp-1-2020",
            "res-cne-cp-2-2022",
            "parecer-cne-cp-22-2019",
            "parecer-cne-cp-14-2020",
            "parecer-cne-cp-4-2021",
        ],
    },
    {
        "id": "avaliacao",
        "titulo": "Avaliação e planejamento",
        "descricao": "Avaliação educacional, metas do Plano Nacional de Educação e monitoramento.",
        "perguntas": [
            "Quais são as metas do PNE e o que ele previa?",
            "Como a avaliação aparece na legislação educacional?",
            "O que acontece após o término do PNE 2014-2024?",
        ],
        "consulta": "avaliação educacional metas plano nacional de educação",
        "documentos": ["pne-13005-2014", "parecer-cne-ceb-7-2010"],
    },
    {
        "id": "tecnologia-ia",
        "titulo": "Tecnologia, educação digital e IA",
        "descricao": "Educação digital, computação na BNCC, uso de dispositivos, proteção de dados e "
        "diretrizes para inteligência artificial na educação.",
        "perguntas": [
            "O que propõe a Política Nacional de Educação Digital?",
            "Como se ensina Computação na educação básica?",
            "O que dizem as atuais diretrizes sobre o uso de IA na educação?",
            "Como regular o uso de celulares e proteger dados de estudantes?",
        ],
        "consulta": "educação digital inteligência artificial computação proteção de dados dispositivos",
        "documentos": [
            "pned-14533-2023",
            "decreto-11713-2023",
            "bncc-computacao",
            "res-cne-ceb-1-2022",
            "parecer-cne-ceb-2-2022",
            "parecer-cne-15-2026",
            "guia-ia-mec",
            "ebia",
            "estrategia-edu-midiatica",
            "lei-15100-2025",
            "res-cne-ceb-2-2025",
            "parecer-cne-ceb-4-2025",
            "curriculo-cieb-computacao",
            "referenciais-sbc-computacao",
            "marco-civil-12965-2014",
            "lgpd-13709-2018",
        ],
    },
    {
        "id": "direito-protecao",
        "titulo": "Direito à educação e proteção",
        "descricao": "O direito constitucional à educação e a proteção de crianças e adolescentes, "
        "inclusive no ambiente digital.",
        "perguntas": [
            "Como a Constituição garante o direito à educação?",
            "O que é o ECA Digital e o que ele muda?",
            "Como a LGPD se aplica a dados de estudantes?",
        ],
        "consulta": "direito à educação proteção criança adolescente dados pessoais",
        "documentos": [
            "cf-1988",
            "eca-8069-1990",
            "eca-digital-15211-2025",
            "lgpd-13709-2018",
            "lei-15100-2025",
        ],
    },
]


def listar() -> List[dict]:
    itens = []
    for trilha in TRILHAS:
        dados = dict(trilha)
        documentos = []
        for doc_id in trilha.get("documentos", []):
            item = get_catalogo(doc_id)
            if item is None:
                continue
            documentos.append(
                {
                    "id": item.id,
                    "titulo": item.titulo,
                    "categoria": item.categoria,
                    "ano": item.ano,
                    "vigente": item.vigente,
                    "situacao": item.situacao,
                    "substituido_por": item.substituido_por,
                }
            )
        dados["documentos"] = documentos
        itens.append(dados)
    return itens


def get(trilha_id: str) -> Optional[dict]:
    for trilha in listar():
        if trilha["id"] == trilha_id:
            return trilha
    return None
