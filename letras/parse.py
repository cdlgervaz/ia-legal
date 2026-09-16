import re

from .keywords import (
    ESTRUTURA_CARGA,
    ESTRUTURA_CODIGO,
    INDICIOS_DISCIPLINA,
    normalizar,
    palavras_encontradas,
)

RE_REF_ANO = re.compile(r"\((?:19|20)\d{2}[a-z]?\)")
RE_IN = re.compile(r"\bIn\s*:")
RE_EDITORA = re.compile(
    r"\b(editora|ed\.|publishers|press|parabola|vozes|cortez|atica|"
    r"companhia das letras|contexto|pontes|mercado de letras|scipione|"
    r"jorge zahar|ao livro|unb|edusp|uel|edufrgs|edunicamp)\b",
    re.IGNORECASE,
)
RE_VOL = re.compile(r"\bv\.\s*\d+")
RE_PAG = re.compile(r"\bp+p?\.\s*\d+")
RE_ORG = re.compile(r"\b(orgs?\.?|et al\.?)\b", re.IGNORECASE)
RE_AUTOR_SOBRENOME = re.compile(r"^[A-ZÀ-Ý][A-ZÀ-Ý'’.\-]+(?:\s+[A-ZÀ-Ý'’.\-]+)*,")
RE_AUTOR = re.compile(r"^[A-ZÀ-Ý][a-zà-ÿ]+,\s*[A-ZÀ-Ý](\.|\s)")
RE_CIDADE = re.compile(
    r"\b(São Paulo|Rio de Janeiro|Belo Horizonte|Porto Alegre|Campinas|Salvador|"
    r"Recife|Curitiba|Florianópolis|João Pessoa|Natal|Fortaleza|Brasília|Goiânia|"
    r"Manaus|Belém|Vitória|Uberlândia|Londrina|Maringá|Araraquara|Petrópolis|"
    r"Juiz de Fora|São José do Rio Preto)\b\s*[:,]"
)
RE_DISPONIVEL = re.compile(r"\b(dispon[íi]vel em|acesso em)\b", re.IGNORECASE)
RE_ANAIS = re.compile(
    r"\b(anais|revista|cadernos|semin[áa]rio|simp[óo]sio|col[óo]quio|congresso|"
    r"grupo de estudos)\b",
    re.IGNORECASE,
)
RE_EDICAO = re.compile(r"\b\d+\.?\s*ed\.|\bedi[çc][ãa]o\b", re.IGNORECASE)
RE_ANO_FIM = re.compile(r"(?:19|20)\d{2}\.?\s*$")
RE_TRABALHO = re.compile(
    r"\b(tese|disserta[çc][ãa]o|monografia|trabalho de conclus)\b", re.IGNORECASE
)
RE_INST = re.compile(
    r"\b(UFMG|UFRJ|UFSC|UFRGS|UNICAMP|USP|UFPB|UFPE|UnB|PUC|Fundação|Instituto)\b"
)
RE_CITACAO = re.compile(r"[‘’“”]")
RE_MARKER = re.compile(r"^(\d+[\).\]]|[a-z][\)]|[-•*])\s")
RE_URL = re.compile(r"https?://|www\.", re.IGNORECASE)
RE_REVISTA = re.compile(r"\bRevista\b", re.IGNORECASE)
RE_EARLY = re.compile(r"\b(primeira|segunda|terceira|quarta|quinta|sexta)\s+unidade\b", re.IGNORECASE)
RE_EMENTA = re.compile(r"^\s*ementa\b", re.IGNORECASE)
RE_SECAO_REF = re.compile(
    r"^\s*(refer[êe]ncias?|bibliografia|obras consultadas|fontes)\b", re.IGNORECASE
)
RE_ROW_FIM = re.compile(r"\s\d{1,3}(?:\s+\d{1,3}){0,3}\s*$")
RE_FRASE_CONT = re.compile(r"\.\s+[a-zà-ÿ]")
RE_CODIGO_NUM = re.compile(r"^\d{3,6}\s*[-–—.:]?\s*")
RE_RUIDO = re.compile(
    r"\b(diploma|certificado|hist[óo]rico|matr[íi]cula|calend[áa]rio|publica[çc]"
    r"|pr[ée]-requisito|prerequisito|requisito|bibliografia|refer[êe]ncia"
    r"|fluxograma|fluxo curricular|quadro|ementa|endere[çc]o|semestre|bancada"
    r"|disp[õo]e|disp[õo]em|turma|hor[áa]rio|alimentos|nutri[çc][ãa]o|enfermagem"
    r"|medicina|agronomia|zootecnia|odontologia|fisioterapia|engenharia"
    r"|pr[ée]-?req|fonte|parque|per[íi]odo)\b",
    re.IGNORECASE,
)
RE_URL_BR = re.compile(r"\.(gov|org|com|edu|net)\.br\b", re.IGNORECASE)
RE_ADMIN = re.compile(
    r"\b(n[úu]cleo|laborat[óo]rio|departamento|coordena[çc][ãa]o|coordenadoria"
    r"|reitoria|pr[óo]-?reitoria|secretaria|divis[ãa]o|setor|ger[êe]ncia"
    r"|superintend[êe]ncia|centro|diretoria|assessoria)\s+(de|da|do|das|dos)\b",
    re.IGNORECASE,
)
RE_ADMIN_INICIO = re.compile(
    r"^(n[úu]cleo|departamento|coordena[çc][ãa]o|coordenadoria|reitoria"
    r"|pr[óo]-?reitoria|secretaria|divis[ãa]o|setor|diretoria|eixo|m[óo]dulo"
    r"|modalidade|turno|programa|projeto pedag[óo]gico|matriz|grade|fluxograma"
    r"|endere[çc]o|semestre|desde|bancada|alunos?|discentes?|docentes?|turma"
    r"|oferta|hor[áa]rio|instituto|comit[êe]|objetivos?|se[çc][ãa]o|cap[íi]tulo"
    r"|anexo|ap[êe]ndice|tabela|figura|gr[áa]fico|sum[áa]rio|apresenta[çc][ãa]o"
    r"|carga hor|ement[áa]rio)\b",
    re.IGNORECASE,
)
RE_LABEL = re.compile(r"^([A-ZÀ-Ý]{1,8}\s*[:.]\s*){2,}")
CONECTORES = {
    "de", "da", "do", "das", "dos", "e", "em", "para", "com", "a", "o",
    "as", "os", "à", "às", "no", "na", "nos", "nas", "por", "sobre",
}


def _fundir_linhas(linhas: list[str]) -> list[str]:
    fundidas: list[str] = []
    buffer = ""
    for linha in linhas:
        buffer = f"{buffer} {linha}".strip() if buffer else linha
        tokens = buffer.split()
        ultimo = normalizar(tokens[-1]).strip(".,;:") if tokens else ""
        if ultimo in CONECTORES or buffer.rstrip().endswith(","):
            continue
        fundidas.append(buffer)
        buffer = ""
    if buffer:
        fundidas.append(buffer)
    return fundidas

STOPWORDS_FRASE = {
    "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas", "um",
    "uma", "os", "as", "que", "com", "para", "por", "se", "ao", "à", "como",
    "sao", "ser", "foi", "é", "sua", "seu", "suas", "seus", "pela", "pelo",
    "a", "o", "e",
}


def _parece_frase(linha: str) -> bool:
    if ESTRUTURA_CODIGO.match(linha.strip()):
        return False
    if RE_FRASE_CONT.search(linha):
        return True
    if linha.rstrip().endswith(","):
        return True
    tokens = re.findall(r"\w+", normalizar(linha))
    if len(tokens) >= 5:
        stops = sum(1 for t in tokens if t in STOPWORDS_FRASE)
        if stops >= 4 and stops / len(tokens) > 0.25:
            return True
    if len(tokens) > 14:
        return True
    if linha.count("(") != linha.count(")"):
        return True
    if ")" in linha and not linha.rstrip().endswith(")"):
        return True
    return False


def limpar_nome(linha: str) -> str:
    linha = re.sub(r"\s+", " ", linha).strip()
    linha = ESTRUTURA_CODIGO.sub("", linha).strip()
    linha = RE_CODIGO_NUM.sub("", linha).strip()
    linha = re.sub(r"^(C[ÓO]DIGO|DISCIPLINA|COMPONENTE CURRICULAR)\b[:\s]*", "",
                   linha, flags=re.IGNORECASE)
    linha = re.sub(r"(C\.?H\.?|C\.?R\.?|CR[ÉE]DITOS?|CARGA HOR[ÁA]RIA)\s*:.*$", "",
                   linha, flags=re.IGNORECASE)
    linha = ESTRUTURA_CARGA.sub("", linha).strip()
    linha = re.sub(r"[\s\-–—]*(?:\d+[\s\-–—]*){2,}$", "", linha)
    linha = re.sub(r"\s*[-–—]\s*(\d+\s*)+$", "", linha)
    linha = re.sub(r"^[\-–—:.\s]+", "", linha)
    linha = re.sub(r"[\-–—:.\s]+$", "", linha)
    linha = re.sub(r"\s*\|\s*$", "", linha)
    return linha[:200]


def _parece_referencia(linha: str) -> bool:
    return any(
        p.search(linha)
        for p in (RE_REF_ANO, RE_IN, RE_EDITORA, RE_VOL, RE_PAG, RE_ORG,
                  RE_AUTOR_SOBRENOME, RE_AUTOR, RE_CIDADE, RE_DISPONIVEL,
                  RE_ANAIS, RE_EDICAO, RE_ANO_FIM, RE_TRABALHO, RE_INST,
                  RE_CITACAO, RE_URL, RE_URL_BR, RE_REVISTA, RE_EARLY)
    )


def _parece_titulo_disciplina(linha: str) -> bool:
    linha = linha.strip()
    if len(linha) < 5:
        return False
    if _parece_referencia(linha):
        return False
    if RE_MARKER.match(linha) or RE_SECAO_REF.match(linha):
        return False
    if RE_LABEL.match(linha):
        return False
    if RE_RUIDO.search(linha) or RE_ADMIN.search(linha) or RE_ADMIN_INICIO.match(linha):
        return False
    if normalizar(linha).startswith("ementa"):
        return False
    base = limpar_nome(linha)
    if not (5 <= len(base) <= 140):
        return False
    if not base[0].isupper():
        return False
    if len(base.split()) > 14:
        return False
    if _parece_frase(base):
        return False
    if sum(c.isalpha() for c in base) < 4:
        return False
    if base.count(";") > 2:
        return False
    return True


def _tem_suporte(linha: str, linhas: list[str], i: int) -> bool:
    if ESTRUTURA_CODIGO.match(linha.strip()) or RE_CODIGO_NUM.match(linha.strip()):
        return True
    if ESTRUTURA_CARGA.search(linha):
        return True
    if RE_ROW_FIM.search(linha):
        return True
    janela = " ".join(linhas[max(0, i - 2): i + 3])
    if ESTRUTURA_CARGA.search(janela):
        return True
    janela_norm = normalizar(janela)
    return any(ind in janela_norm for ind in INDICIOS_DISCIPLINA)


def _score(linha: str, contexto: str, kws: list[str]) -> int:
    score = len(kws) * 2
    if ESTRUTURA_CODIGO.match(linha.strip()) or RE_CODIGO_NUM.match(linha.strip()):
        score += 3
    if ESTRUTURA_CARGA.search(linha):
        score += 2
    ctx_norm = normalizar(contexto)
    if any(ind in ctx_norm for ind in INDICIOS_DISCIPLINA):
        score += 2
    if RE_EMENTA.match(linha):
        score += 1
    return score


def _pagina_de_lista(linhas: list[str]) -> bool:
    curtos = 0
    for linha in linhas:
        if not (5 <= len(linha) <= 70) or len(linha.split()) > 8:
            continue
        if not linha[0].isupper():
            continue
        if _parece_referencia(linha):
            continue
        if RE_MARKER.match(linha) or RE_RUIDO.search(linha) or RE_ADMIN.search(linha):
            continue
        if RE_ADMIN_INICIO.match(linha):
            continue
        curtos += 1
        if curtos >= 5:
            return True
    return False


def _contexto(linhas: list[str], i: int, janela: int = 2) -> str:
    inicio = max(0, i - janela)
    fim = min(len(linhas), i + janela + 1)
    return " ".join(linhas[inicio:fim])


def _adicionar(candidatos: dict, chave: str, nome: str, trecho: str,
               kws: list[str], score: int, pagina: int) -> None:
    if len(nome) < 4:
        return
    if chave not in candidatos or score > candidatos[chave]["score"]:
        candidatos[chave] = {
            "nome": nome,
            "trecho": trecho[:600],
            "palavras_chave": sorted(set(kws)),
            "score": score,
            "pagina": pagina,
        }


def encontrar_disciplinas(paginas: list[tuple[int, str]]) -> list[dict]:
    candidatos: dict[str, dict] = {}
    for pagina, texto in paginas:
        linhas = [ln.strip() for ln in texto.splitlines()]
        linhas = [ln for ln in linhas if ln]
        linhas = _fundir_linhas(linhas)
        pagina_lista = _pagina_de_lista(linhas)

        for i, linha in enumerate(linhas):
            if RE_SECAO_REF.match(linha):
                break

            if RE_EMENTA.match(linha):
                bloco = " ".join(linhas[i: i + 10])
                kws = palavras_encontradas(bloco)
                if kws:
                    for j in range(i - 1, max(-1, i - 4), -1):
                        if _parece_titulo_disciplina(linhas[j]):
                            nome = limpar_nome(linhas[j])
                            chave = normalizar(nome)[:160]
                            _adicionar(candidatos, chave, nome, bloco,
                                       kws, _score(linhas[j], bloco, kws) + 2, pagina)
                            break

            kws = palavras_encontradas(linha)
            if not kws:
                continue
            if not _parece_titulo_disciplina(linha):
                continue
            suporte = _tem_suporte(linha, linhas, i)
            if not suporte and not (
                pagina_lista and len(linha) <= 70 and len(linha.split()) <= 8
            ):
                continue
            nome = limpar_nome(linha)
            chave = normalizar(nome)[:160]
            _adicionar(candidatos, chave, nome, _contexto(linhas, i), kws,
                       _score(linha, _contexto(linhas, i), kws), pagina)

    return sorted(candidatos.values(), key=lambda c: c["score"], reverse=True)
