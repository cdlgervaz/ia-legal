from typing import List, Optional

from .models import DocumentoCatalogo

CATALOGO: List[DocumentoCatalogo] = [
    DocumentoCatalogo(
        id="cf-1988",
        titulo="Constituição da República Federativa do Brasil de 1988",
        tipo="Constituição",
        ano=1988,
        orgao="Congresso Nacional",
        descricao=(
            "Texto constitucional completo. Para esta disciplina interessam os artigos 205 a 214 "
            "(educação, dever do Estado, princípios do ensino e vinculação de recursos)."
        ),
        url="https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm",
        formato="html",
        temas=["gestao", "financiamento", "curriculo"],
    ),
    DocumentoCatalogo(
        id="ldb-9394-1996",
        titulo="Lei nº 9.394/1996 - Lei de Diretrizes e Bases da Educação Nacional (LDB)",
        tipo="Lei",
        ano=1996,
        orgao="Congresso Nacional",
        descricao="Organização da educação nacional, níveis e modalidades, currículo e formação docente.",
        url="https://www.planalto.gov.br/ccivil_03/leis/l9394.htm",
        formato="html",
        temas=["curriculo", "gestao", "formacao_docente", "avaliacao"],
        vigente=True,
        situacao=(
            "Vigente, com inúmeras alterações — entre elas a Lei nº 13.415/2017 e a "
            "Lei nº 14.945/2024 (ensino médio) e a Lei nº 14.533/2023 (educação digital)."
        ),
    ),
    DocumentoCatalogo(
        id="pne-13005-2014",
        titulo="Lei nº 13.005/2014 - Plano Nacional de Educação (PNE 2014-2024)",
        tipo="Lei",
        ano=2014,
        orgao="Congresso Nacional",
        descricao="Metas e estratégias do PNE, incluindo financiamento, formação docente e avaliação.",
        url="https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l13005.htm",
        formato="html",
        temas=["financiamento", "gestao", "formacao_docente", "avaliacao"],
        vigente=False,
        situacao="Plano decenal encerrado em 2024.",
        substituido_por="Novo Plano Nacional de Educação (em tramitação no Congresso Nacional)",
    ),
    DocumentoCatalogo(
        id="pned-14533-2023",
        titulo="Lei nº 14.533/2023 - Política Nacional de Educação Digital (PNED)",
        tipo="Lei",
        ano=2023,
        orgao="Congresso Nacional",
        descricao=(
            "Institui a Política Nacional de Educação Digital, com eixos de inclusão digital, "
            "educação digital escolar, capacitação docente e especialização em tecnologia."
        ),
        url="https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/lei/l14533.htm",
        formato="html",
        temas=["tecnologia", "ia_educacao", "formacao_docente", "curriculo"],
    ),
    DocumentoCatalogo(
        id="lgpd-13709-2018",
        titulo="Lei nº 13.709/2018 - Lei Geral de Proteção de Dados Pessoais (LGPD)",
        tipo="Lei",
        ano=2018,
        orgao="Congresso Nacional",
        descricao="Bases legais, direitos dos titulares e tratamento de dados no ambiente escolar.",
        url="https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm",
        formato="html",
        temas=["ia_educacao", "tecnologia"],
    ),
    DocumentoCatalogo(
        id="fundeb-14113-2020",
        titulo="Lei nº 14.113/2020 - FUNDEB",
        tipo="Lei",
        ano=2020,
        orgao="Congresso Nacional",
        descricao="Fundo de Manutenção e Desenvolvimento da Educação Básica e de Valorização dos Profissionais da Educação.",
        url="https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/lei/l14113.htm",
        formato="html",
        temas=["financiamento", "gestao", "formacao_docente"],
    ),
    DocumentoCatalogo(
        id="lei-15100-2025",
        titulo="Lei nº 15.100/2025 - Uso de dispositivos digitais na educação básica",
        tipo="Lei",
        ano=2025,
        orgao="Congresso Nacional",
        descricao="Dispõe sobre o uso de celulares e outros dispositivos digitais em escolas de educação básica.",
        url="https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15100.htm",
        formato="html",
        temas=["tecnologia", "curriculo", "gestao"],
    ),
    DocumentoCatalogo(
        id="bncc-ei-ef",
        titulo="BNCC - Educação Infantil e Ensino Fundamental",
        tipo="Base Nacional",
        ano=2017,
        orgao="Ministério da Educação",
        descricao="Base Nacional Comum Curricular: competências gerais, direitos de aprendizagem e habilidades.",
        url="http://basenacionalcomum.mec.gov.br/images/BNCC_EI_EF_110518_versaofinal_site.pdf",
        formato="pdf",
        temas=["curriculo", "avaliacao"],
    ),
    DocumentoCatalogo(
        id="bncc-em",
        titulo="BNCC - Ensino Médio",
        tipo="Base Nacional",
        ano=2018,
        orgao="Ministério da Educação",
        descricao="Base Nacional Comum Curricular do Ensino Médio: formações geral e itinerários formativos.",
        url="http://basenacionalcomum.mec.gov.br/images/historico/BNCC_EnsinoMedio_embaixa_site_110518.pdf",
        formato="pdf",
        temas=["curriculo", "avaliacao"],
    ),
    DocumentoCatalogo(
        id="bncc-computacao",
        titulo="BNCC Computação - Complemento à BNCC",
        tipo="Base Nacional",
        ano=2022,
        orgao="Conselho Nacional de Educação",
        descricao="Normas sobre Computação na Educação Básica: pensamento computacional, mundo digital e cultura digital.",
        url=(
            "https://www.gov.br/mec/pt-br/cne/pdf/normas-classificadas-por-assunto/"
            "base-nacional-comum-curricular-bncc/anexo-ao-parecer-cneceb-no-2-2022-bncc-computacao.pdf"
        ),
        formato="pdf",
        temas=["tecnologia", "curriculo", "ia_educacao"],
    ),
    DocumentoCatalogo(
        id="res-cne-ceb-1-2022",
        titulo="Resolução CNE/CEB nº 1/2022 - Computação na Educação Básica",
        tipo="Resolução",
        ano=2022,
        orgao="Conselho Nacional de Educação",
        descricao="Normas sobre Computação na Educação Básica - Complemento à BNCC.",
        url=(
            "https://www.gov.br/mec/pt-br/cne/pdf/normas-classificadas-por-assunto/"
            "base-nacional-comum-curricular-bncc/rceb001_22.pdf"
        ),
        formato="pdf",
        temas=["tecnologia", "curriculo"],
    ),
    DocumentoCatalogo(
        id="parecer-cne-ceb-2-2022",
        titulo="Parecer CNE/CEB nº 2/2022 - BNCC Computação",
        tipo="Parecer",
        ano=2022,
        orgao="Conselho Nacional de Educação",
        descricao="Parecer que fundamenta as normas de Computação na Educação Básica.",
        url=(
            "https://www.gov.br/mec/pt-br/cne/pdf/normas-classificadas-por-assunto/"
            "base-nacional-comum-curricular-bncc/pceb002_22.pdf"
        ),
        formato="pdf",
        temas=["tecnologia", "curriculo"],
    ),
    DocumentoCatalogo(
        id="res-cne-cp-2-2017",
        titulo="Resolução CNE/CP nº 2/2017 - Implantação da BNCC",
        tipo="Resolução",
        ano=2017,
        orgao="Conselho Nacional de Educação",
        descricao="Institui e orienta a implantação da Base Nacional Comum Curricular.",
        url=(
            "https://www.gov.br/mec/pt-br/cne/pdf/normas-classificadas-por-assunto/"
            "base-nacional-comum-curricular-bncc/rcp002_17.pdf"
        ),
        formato="pdf",
        temas=["curriculo", "gestao"],
    ),
    DocumentoCatalogo(
        id="res-cne-ceb-2-2025",
        titulo="Resolução CNE/CEB nº 2/2025 - Dispositivos digitais nos espaços escolares",
        tipo="Resolução",
        ano=2025,
        orgao="Conselho Nacional de Educação",
        descricao=(
            "Diretrizes operacionais nacionais sobre o uso de dispositivos digitais nos espaços "
            "escolares e integração curricular (regulamenta a Lei nº 15.100/2025)."
        ),
        url=(
            "https://www.gov.br/mec/pt-br/cne/pdf/normas-classificadas-por-assunto/"
            "dispositivos-digitais/rceb002_25.pdf"
        ),
        formato="pdf",
        temas=["tecnologia", "curriculo", "gestao"],
    ),
    DocumentoCatalogo(
        id="parecer-cne-ceb-4-2025",
        titulo="Parecer CNE/CEB nº 4/2025 - Uso de dispositivos digitais na escola",
        tipo="Parecer",
        ano=2025,
        orgao="Conselho Nacional de Educação",
        descricao="Fundamenta as diretrizes sobre dispositivos digitais em espaços escolares.",
        url=(
            "https://www.gov.br/mec/pt-br/cne/pdf/normas-classificadas-por-assunto/"
            "dispositivos-digitais/pceb004_25.pdf"
        ),
        formato="pdf",
        temas=["tecnologia", "curriculo"],
    ),
    DocumentoCatalogo(
        id="res-cne-cp-2-2019",
        titulo="Resolução CNE/CP nº 2/2019 - BNC-Formação",
        tipo="Resolução",
        ano=2019,
        orgao="Conselho Nacional de Educação",
        descricao=(
            "Define as Diretrizes Curriculares Nacionais para a Formação Inicial de Professores "
            "para a Educação Básica e institui a Base Nacional Comum para a Formação Inicial "
            "de Professores da Educação Básica (BNC-Formação)."
        ),
        url="https://www.gov.br/mec/pt-br/cne/pdf/resolucoes-do-cne/cp/2019/rcp002_19.pdf",
        formato="pdf",
        temas=["formacao_docente", "curriculo"],
    ),
    DocumentoCatalogo(
        id="res-cne-cp-1-2020",
        titulo="Resolução CNE/CP nº 1/2020 - BNC-Formação Continuada",
        tipo="Resolução",
        ano=2020,
        orgao="Conselho Nacional de Educação",
        descricao=(
            "Diretrizes Curriculares Nacionais para a Formação Continuada de Professores e "
            "Base Nacional Comum para a Formação Continuada (BNC-Formação Continuada)."
        ),
        url="https://www.gov.br/mec/pt-br/cne/pdf/resolucoes-do-cne/cp/2020/rcp001_20.pdf",
        formato="pdf",
        temas=["formacao_docente", "curriculo"],
    ),
    DocumentoCatalogo(
        id="res-cne-cp-2-2022",
        titulo="Resolução CNE/CP nº 2/2022 - Alteração da BNC-Formação",
        tipo="Resolução",
        ano=2022,
        orgao="Conselho Nacional de Educação",
        descricao="Altera o art. 27 da Resolução CNE/CP nº 2/2019 (BNC-Formação), sobre carga horária e prática.",
        url="https://www.gov.br/mec/pt-br/cne/pdf/resolucoes-do-cne/cp/2022/rcp002_22.pdf",
        formato="pdf",
        temas=["formacao_docente", "curriculo"],
    ),
    DocumentoCatalogo(
        id="parecer-cne-cp-4-2021",
        titulo="Parecer CNE/CP nº 4/2021 - BNC Diretor Escolar",
        tipo="Parecer",
        ano=2021,
        orgao="Conselho Nacional de Educação",
        descricao=(
            "Base Nacional Comum de Competências do Diretor Escolar (BNC-Diretor Escolar): "
            "competências profissionais da gestão escolar."
        ),
        url="https://www.gov.br/mec/pt-br/cne/pdf/pareceres-do-cne/cp/2021/pcp004_21.pdf",
        formato="pdf",
        temas=["gestao", "formacao_docente"],
    ),
    DocumentoCatalogo(
        id="ebia",
        titulo="Estratégia Brasileira de Inteligência Artificial (EBIA)",
        tipo="Estratégia",
        ano=2021,
        orgao="Ministério da Ciência, Tecnologia e Inovação",
        descricao="Eixos da estratégia nacional de IA, incluindo educação e capacitação.",
        url="https://www.gov.br/mcti/pt-br/acompanhe-o-mcti/transformacaodigital/ebia.pdf",
        formato="pdf",
        temas=["ia_educacao", "tecnologia", "formacao_docente"],
    ),
    DocumentoCatalogo(
        id="pbia-2024-2028",
        titulo="Plano Brasileiro de Inteligência Artificial (PBIA 2024-2028)",
        tipo="Plano",
        ano=2024,
        orgao="Ministério da Ciência, Tecnologia e Inovação",
        descricao=(
            "Plano nacional de IA com ações de formação, pesquisa e uso da IA em políticas públicas, "
            "incluindo educação."
        ),
        url="https://www.gov.br/mcti/pt-br/acompanhe-o-mcti/transformacaodigital/plano-brasileiro-de-inteligencia-artificial",
        formato="html",
        importavel=False,
        observacao=(
            "O PDF oficial fica nesta página: baixe-o e importe com "
            "`./scripts/importar_documentos.py --arquivo caminho/pbia.pdf --id pbia-2024-2028 ...`."
        ),
    ),
    DocumentoCatalogo(
        id="pl-2338-2023",
        titulo="PL nº 2338/2023 - Marco Legal da Inteligência Artificial",
        tipo="Proposição",
        ano=2023,
        orgao="Congresso Nacional",
        descricao=(
            "Projeto de lei sobre desenvolvimento, fomento e uso ético da IA no Brasil. "
            "Acompanhe a tramitação atualizada na busca e na aba de andamento (a proposição é "
            "capturada pela sincronização do Senado e da Câmara)."
        ),
        url="https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao=2487262",
        formato="html",
        importavel=False,
        observacao="Em tramitação; consulte o texto mais recente no portal oficial.",
    ),
    DocumentoCatalogo(
        id="lei-13415-2017",
        titulo="Lei nº 13.415/2017 - Reforma do Ensino Médio (Novo Ensino Médio)",
        tipo="Lei",
        ano=2017,
        orgao="Congresso Nacional",
        descricao=(
            "Altera a LDB para instituir a política de fomento à implementação de escolas de "
            "ensino médio em tempo integral e a organização do ensino médio por itinerários."
        ),
        url="https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2017/lei/l13415.htm",
        formato="html",
        temas=["curriculo", "gestao"],
        vigente=True,
        situacao="Vigente, com alterações introduzidas pela Lei nº 14.945/2024.",
    ),
    DocumentoCatalogo(
        id="lei-14945-2024",
        titulo="Lei nº 14.945/2024 - Ajustes ao Novo Ensino Médio",
        tipo="Lei",
        ano=2024,
        orgao="Congresso Nacional",
        descricao=(
            "Altera a LDB (Lei nº 9.394/1996) quanto à organização do ensino médio, ajustando a "
            "carga horária, a formação geral básica e os itinerários formativos."
        ),
        url="https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/lei/l14945.htm",
        formato="html",
        temas=["curriculo", "gestao"],
        vigente=True,
        situacao="Vigente; modifica dispositivos da reforma do ensino médio (Lei nº 13.415/2017).",
    ),
    DocumentoCatalogo(
        id="marco-civil-12965-2014",
        titulo="Lei nº 12.965/2014 - Marco Civil da Internet",
        tipo="Lei",
        ano=2014,
        orgao="Congresso Nacional",
        descricao=(
            "Princípios, garantias, direitos e deveres para o uso da internet no Brasil: "
            "neutralidade da rede, privacidade e responsabilidades."
        ),
        url="https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l12965.htm",
        formato="html",
        temas=["tecnologia", "ia_educacao"],
        vigente=True,
        situacao="Vigente.",
    ),
    DocumentoCatalogo(
        id="decreto-9057-2017",
        titulo="Decreto nº 9.057/2017 - Educação a Distância",
        tipo="Decreto",
        ano=2017,
        orgao="Presidência da República",
        descricao=(
            "Regulamenta o art. 80 da LDB para estabelecer as normas da educação a distância "
            "(EaD) na educação básica e superior."
        ),
        url="https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2017/decreto/d9057.htm",
        formato="html",
        temas=["tecnologia", "curriculo"],
        vigente=True,
        situacao="Vigente; revogou o Decreto nº 5.622/2005.",
    ),
    DocumentoCatalogo(
        id="decreto-11713-2023",
        titulo="Decreto nº 11.713/2023 - Regulamenta a Política Nacional de Educação Digital",
        tipo="Decreto",
        ano=2023,
        orgao="Presidência da República",
        descricao=(
            "Regulamenta a Lei nº 14.533/2023 (PNED), dispondo sobre sua governança e eixos de "
            "implementação, incluindo formação de professores em tecnologia."
        ),
        url="https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/decreto/d11713.htm",
        formato="html",
        temas=["tecnologia", "ia_educacao", "formacao_docente"],
        vigente=True,
        situacao="Vigente; regulamenta a Lei nº 14.533/2023.",
    ),
    DocumentoCatalogo(
        id="parecer-cne-15-2026",
        titulo=(
            "Parecer CNE nº 15/2026 - Diretrizes Orientadoras para o uso da Inteligência "
            "Artificial na Educação Brasileira"
        ),
        tipo="Parecer",
        ano=2026,
        orgao="Conselho Nacional de Educação (Conselho Pleno)",
        descricao=(
            "Parecer relatado por Celso Niskier (processo 23001.001062/2024-18) com diretrizes "
            "orientadoras para o uso da IA na educação brasileira. Reunião ordinária de setembro "
            "de 2026."
        ),
        url="https://www.gov.br/mec/pt-br/cne/2026/setembro-2026/prel09_2026.pdf",
        formato="pdf",
        temas=["ia_educacao", "tecnologia", "curriculo"],
        vigente=None,
        situacao=(
            "Parecer relatado em 1º/9/2026; encontra-se em fase de revisão técnica, antes da "
            "publicação da súmula no Diário Oficial da União."
        ),
    ),
    DocumentoCatalogo(
        id="parecer-cne-cp-22-2019",
        titulo="Parecer CNE/CP nº 22/2019 - Diretrizes para a Formação Inicial de Professores (BNC-Formação)",
        tipo="Parecer",
        ano=2019,
        orgao="Conselho Nacional de Educação",
        descricao=(
            "Fundamenta as Diretrizes Curriculares Nacionais para a Formação Inicial de "
            "Professores e a BNC-Formação."
        ),
        url="https://www.gov.br/mec/pt-br/cne/pdf/pareceres-do-cne/cp/2019/pcp022_19.pdf",
        formato="pdf",
        temas=["formacao_docente", "curriculo"],
        vigente=True,
        situacao="Vigente; dá base à Resolução CNE/CP nº 2/2019.",
    ),
    DocumentoCatalogo(
        id="parecer-cne-cp-14-2020",
        titulo="Parecer CNE/CP nº 14/2020 - Formação Continuada de Professores (BNC-Formação Continuada)",
        tipo="Parecer",
        ano=2020,
        orgao="Conselho Nacional de Educação",
        descricao=(
            "Fundamenta as Diretrizes Curriculares Nacionais para a Formação Continuada de "
            "Professores e a BNC-Formação Continuada."
        ),
        url="https://www.gov.br/mec/pt-br/cne/pdf/pareceres-do-cne/cp/2020/pcp014_20.pdf",
        formato="pdf",
        temas=["formacao_docente", "curriculo"],
        vigente=True,
        situacao="Vigente; dá base à Resolução CNE/CP nº 1/2020.",
    ),
    DocumentoCatalogo(
        id="parecer-cne-ceb-7-2010",
        titulo="Parecer CNE/CEB nº 7/2010 - Diretrizes Curriculares Nacionais Gerais para a Educação Básica",
        tipo="Parecer",
        ano=2010,
        orgao="Conselho Nacional de Educação",
        descricao=(
            "Diretrizes Curriculares Nacionais Gerais para a Educação Básica: organização, "
            "currículo e avaliação."
        ),
        url="https://www.gov.br/mec/pt-br/cne/pdf/pareceres-do-cne/ceb/2010/pceb007_10.pdf",
        formato="pdf",
        temas=["curriculo", "gestao"],
        vigente=True,
        situacao="Vigente; dá base à Resolução CNE/CEB nº 4/2010.",
    ),
    DocumentoCatalogo(
        id="parecer-cne-ceb-5-2011",
        titulo="Parecer CNE/CEB nº 5/2011 - Diretrizes Curriculares Nacionais para o Ensino Médio",
        tipo="Parecer",
        ano=2011,
        orgao="Conselho Nacional de Educação",
        descricao=(
            "Diretrizes Curriculares Nacionais para o Ensino Médio, que embasaram a Resolução "
            "CNE/CEB nº 2/2012."
        ),
        url="https://www.gov.br/mec/pt-br/cne/pdf/pareceres-do-cne/ceb/2011/pceb005_11.pdf",
        formato="pdf",
        temas=["curriculo"],
        vigente=False,
        situacao="Superado pela reforma do ensino médio.",
        substituido_por="Lei nº 13.415/2017 e Resolução CNE/CEB nº 3/2018",
    ),
    DocumentoCatalogo(
        id="pcn-introducao-1997",
        titulo="Parâmetros Curriculares Nacionais (PCN) - Introdução",
        tipo="Documento norteador",
        ano=1997,
        orgao="Ministério da Educação (SEF)",
        descricao=(
            "Introdução aos Parâmetros Curriculares Nacionais do ensino fundamental, com "
            "fundamentos e organização curricular por áreas."
        ),
        url="https://web.archive.org/web/2018id_/http://portal.mec.gov.br/seb/arquivos/pdf/livro01.pdf",
        formato="pdf",
        temas=["curriculo"],
        vigente=False,
        situacao="Substituído pela BNCC.",
        substituido_por="BNCC (Resolução CNE/CP nº 2/2017)",
    ),
    DocumentoCatalogo(
        id="pcn-em-1999",
        titulo="PCN do Ensino Médio - Ciências da Natureza, Matemática e suas Tecnologias",
        tipo="Documento norteador",
        ano=1999,
        orgao="Ministério da Educação (SEMTEC)",
        descricao=(
            "Parâmetros Curriculares Nacionais do Ensino Médio para a área de Ciências da "
            "Natureza, Matemática e suas Tecnologias."
        ),
        url="https://web.archive.org/web/2018id_/http://portal.mec.gov.br/seb/arquivos/pdf/ciencian.pdf",
        formato="pdf",
        temas=["curriculo", "tecnologia"],
        vigente=False,
        situacao="Substituído pela BNCC do Ensino Médio.",
        substituido_por="BNCC - Ensino Médio (2018)",
    ),
    DocumentoCatalogo(
        id="res-cne-ceb-4-2010",
        titulo="Resolução CNE/CEB nº 4/2010 - Diretrizes Curriculares Nacionais Gerais da Educação Básica",
        tipo="Resolução",
        ano=2010,
        orgao="Conselho Nacional de Educação",
        descricao="Estabelece as Diretrizes Curriculares Nacionais Gerais para a Educação Básica.",
        url="https://www.gov.br/mec/pt-br/cne/pdf/resolucoes-do-cne/ceb/2010/rceb004_10.pdf",
        formato="pdf",
        temas=["curriculo", "gestao"],
        vigente=True,
        situacao="Vigente.",
    ),
    DocumentoCatalogo(
        id="res-cne-ceb-2-2012",
        titulo="Resolução CNE/CEB nº 2/2012 - Diretrizes Curriculares Nacionais para o Ensino Médio",
        tipo="Resolução",
        ano=2012,
        orgao="Conselho Nacional de Educação",
        descricao="Define as Diretrizes Curriculares Nacionais para o Ensino Médio (DCNEM).",
        url="https://www.gov.br/mec/pt-br/cne/pdf/resolucoes-do-cne/ceb/2012/rceb002_12.pdf",
        formato="pdf",
        temas=["curriculo"],
        vigente=False,
        situacao="Substituída pelas DCNEM de 2018.",
        substituido_por="Lei nº 13.415/2017 e Resolução CNE/CEB nº 3/2018",
    ),
    DocumentoCatalogo(
        id="res-cne-ceb-3-2018",
        titulo="Resolução CNE/CEB nº 3/2018 - DCNEM (Novo Ensino Médio)",
        tipo="Resolução",
        ano=2018,
        orgao="Conselho Nacional de Educação",
        descricao=(
            "Atualiza as Diretrizes Curriculares Nacionais para o Ensino Médio, alinhando-as à "
            "BNCC e à reforma do ensino médio."
        ),
        url="https://www.gov.br/mec/pt-br/cne/pdf/resolucoes-do-cne/ceb/2018/rceb003_18.pdf",
        formato="pdf",
        temas=["curriculo"],
        vigente=True,
        situacao="Vigente, com impactos da Lei nº 14.945/2024.",
    ),
    DocumentoCatalogo(
        id="estrategia-edu-midiatica",
        titulo="Estratégia Brasileira de Educação Midiática",
        tipo="Estratégia",
        ano=2023,
        orgao="Secretaria de Comunicação Social da Presidência da República (Secom)",
        descricao=(
            "Política pública para fortalecer o uso crítico e responsável da informação e das "
            "mídias, incluindo letramento midiático na educação."
        ),
        url=(
            "https://www.gov.br/secom/pt-br/assuntos/educacao-midiatica/documentos/defeso/"
            "2023_secompr_estrategia-de-edmidiatica_defeso.pdf"
        ),
        formato="pdf",
        temas=["tecnologia", "curriculo", "ia_educacao"],
        vigente=True,
        situacao="Vigente.",
    ),
]


def categoria_de(tipo: str) -> str:
    t = (tipo or "").strip().lower()
    if t in (
        "lei",
        "lei complementar",
        "decreto",
        "constituição",
        "constituicao",
        "medida provisória",
        "medida provisoria",
        "emenda constitucional",
    ):
        return "Lei"
    if t == "parecer":
        return "Parecer"
    if t in (
        "resolução",
        "resolucao",
        "base nacional",
        "estratégia",
        "estrategia",
        "plano",
        "diretriz",
        "documento norteador",
    ):
        return "Documento norteador"
    return ""


for _item in CATALOGO:
    if not _item.categoria:
        _item.categoria = categoria_de(_item.tipo)
    if (
        _item.vigente is None
        and _item.categoria
        and not _item.substituido_por
        and _item.id != "parecer-cne-15-2026"
    ):
        _item.vigente = True
        if not _item.situacao:
            _item.situacao = "Vigente."


def listar(tema: Optional[str] = None, tipo: Optional[str] = None) -> List[DocumentoCatalogo]:
    itens = list(CATALOGO)
    if tema:
        itens = [i for i in itens if tema in i.temas]
    if tipo:
        itens = [i for i in itens if i.tipo == tipo]
    return itens


def get(documento_id: str) -> Optional[DocumentoCatalogo]:
    for item in CATALOGO:
        if item.id == documento_id:
            return item
    return None
