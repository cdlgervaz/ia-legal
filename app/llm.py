from typing import List, Optional

from .config import Settings


class LLMNotConfigured(RuntimeError):
    pass


SYSTEM_PROMPT = """Você é um assistente de ensino e pesquisa em Políticas Educacionais brasileiras, \
auxiliando estudantes de licenciatura e professores a compreender leis, pareceres, resoluções, \
bases curriculares e documentos orientadores da educação.

Regras:
1. Baseie-se SOMENTE no contexto fornecido (proposições legislativas e trechos de documentos \
oficiais). Não invente leis, números, datas ou conteúdos.
2. Quando o contexto não contiver a informação, diga explicitamente o que não foi encontrado.
3. Sempre cite as fontes usando os marcadores [1], [2], ... correspondentes ao contexto.
4. Ao final, liste as fontes citadas com identificação, página (quando houver) e link.
5. Utilize linguagem clara, didática e objetiva, adequada à formação inicial de professores.
6. Diferencie claramente o que é lei vigente, base curricular, parecer, documento orientador e \
projeto em tramitação.
7. Quando útil para a disciplina, organize a resposta em tópicos, explique os termos técnicos e \
destaque implicações para a prática escolar."""


def build_context(fontes: List) -> str:
    blocos = []
    for idx, hit in enumerate(fontes, start=1):
        prop = hit.proposicao
        if getattr(hit, "origem", "proposicao") == "documento":
            titulo = getattr(hit, "titulo", None) or prop.ementa
            cabecalho = f"[{idx}] {titulo} — {prop.tipo}, {prop.casa}"
            if getattr(hit, "pagina", None):
                cabecalho += f" (p. {hit.pagina})"
            linhas = [cabecalho]
            if prop.temas:
                linhas.append(f"Temas: {', '.join(prop.temas)}")
            if prop.url:
                linhas.append(f"Link: {prop.url}")
            if hit.trecho:
                linhas.append(f"Trecho: {hit.trecho}")
        else:
            cabecalho = f"[{idx}] {prop.tipo} {prop.numero}/{prop.ano} — {prop.casa}"
            linhas = [cabecalho, f"Ementa: {prop.ementa}"]
            if prop.temas:
                linhas.append(f"Temas: {', '.join(prop.temas)}")
            if prop.situacao:
                linhas.append(f"Situação atual: {prop.situacao}")
            if prop.orgao:
                linhas.append(f"Órgão atual: {prop.orgao}")
            if prop.autor:
                linhas.append(f"Autor: {prop.autor}")
            if prop.url:
                linhas.append(f"Link: {prop.url}")
            if hit.trecho:
                linhas.append(f"Trecho: {hit.trecho}")
        blocos.append("\n".join(linhas))
    return "\n\n".join(blocos)


def build_user_prompt(query: str, contexto: str) -> str:
    return (
        "Pergunta do usuário:\n"
        f"{query}\n\n"
        "Contexto recuperado (proposições e trechos de documentos oficiais):\n"
        f"{contexto}\n\n"
        "Responda em português, de forma didática, citando as fontes com [n]. "
        "Responda diretamente: não mostre etapas de raciocínio, rascunhos ou texto em inglês."
    )


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            base_url = self.settings.llm_base_url
            if not base_url and self.settings.llm_provider == "ollama":
                base_url = "http://localhost:11434/v1"
            self._client = OpenAI(
                api_key=self.settings.resolved_llm_key(),
                base_url=base_url,
            )
        return self._client

    def disponivel(self) -> bool:
        try:
            self.settings.resolved_llm_key()
        except Exception:
            return False
        return self.settings.llm_enabled()

    def chat(self, mensagens: List[dict], temperature: Optional[float] = None) -> str:
        if not self.settings.llm_enabled():
            raise LLMNotConfigured(
                "Nenhum provedor de LLM configurado. Defina LLM_API_KEY no arquivo .env "
                "ou use LLM_PROVIDER=ollama com um modelo local."
            )
        client = self._get_client()
        modelos = [self.settings.llm_model] + [
            m.strip()
            for m in (self.settings.llm_model_fallbacks or "").split(",")
            if m.strip()
        ]
        ultimo_erro: Optional[Exception] = None
        for modelo in modelos:
            try:
                resposta = client.chat.completions.create(
                    model=modelo,
                    messages=mensagens,
                    temperature=self.settings.llm_temperature
                    if temperature is None
                    else temperature,
                    max_tokens=self.settings.llm_max_tokens,
                )
                return (resposta.choices[0].message.content or "").strip()
            except Exception as exc:
                ultimo_erro = exc
                continue
        raise RuntimeError(f"Nenhum modelo respondeu. Último erro: {ultimo_erro}")

    def responder(self, query: str, fontes: List) -> str:
        contexto = build_context(fontes)
        mensagens = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(query, contexto)},
        ]
        return self.chat(mensagens)

    def resumir(self, proposicao, tramitacoes: List) -> str:
        linhas = [
            f"Identificação: {proposicao.tipo} {proposicao.numero}/{proposicao.ano} ({proposicao.casa})",
            f"Ementa: {proposicao.ementa}",
        ]
        if proposicao.temas:
            linhas.append(f"Temas: {', '.join(proposicao.temas)}")
        if proposicao.situacao:
            linhas.append(f"Situação atual: {proposicao.situacao}")
        if tramitacoes:
            linhas.append("Tramitação recente:")
            for t in tramitacoes[-10:]:
                desc = t.descricao or t.situacao or ""
                if desc:
                    linhas.append(f"- {t.data_hora or 's/ data'} {t.orgao or ''}: {desc}".strip())
        mensagens = [
            {
                "role": "system",
                "content": (
                    "Você é professor de Políticas Educacionais. Explique a proposição legislativa "
                    "a seguir de forma didática, em português, com: (1) resumo em até 3 parágrafos; "
                    "(2) pontos-chave em tópicos; (3) possível uso em sala de aula; (4) estágio atual "
                    "da tramitação. Baseie-se apenas nos dados fornecidos."
                ),
            },
            {"role": "user", "content": "\n".join(linhas)},
        ]
        return self.chat(mensagens)

    def resumir_documento(self, titulo: str, tipo: str, orgao: str, trechos: List[str]) -> str:
        partes_uteis = [t for t in trechos if t]
        if not partes_uteis:
            raise LLMNotConfigured("Nenhum trecho disponível para resumir.")
        texto = "\n\n".join(partes_uteis)
        if len(texto) > self.settings.max_context_chars:
            blocos: List[str] = []
            atual: List[str] = []
            tamanho = 0
            for trecho in partes_uteis:
                if tamanho + len(trecho) > 8000 and atual:
                    blocos.append("\n\n".join(atual))
                    atual, tamanho = [], 0
                atual.append(trecho)
                tamanho += len(trecho)
            if atual:
                blocos.append("\n\n".join(atual))
            parciais = []
            for bloco in blocos[:6]:
                parciais.append(
                    self.chat(
                        [
                            {
                                "role": "system",
                                "content": (
                                    "Você resume documentos oficiais de educação. Produza um resumo "
                                    "fiel e objetivo em tópicos, sem opiniões."
                                ),
                            },
                            {"role": "user", "content": bloco},
                        ]
                    )
                )
            texto = "\n\n".join(
                f"Resumo parcial {indice}:\n{parcial}"
                for indice, parcial in enumerate(parciais, start=1)
            )
        mensagens = [
            {
                "role": "system",
                "content": (
                    "Você é professor de Políticas Educacionais e prepara material para estudantes "
                    "de licenciatura. Com base APENAS nos trechos fornecidos, produza um resumo "
                    "didático em português com: (1) o que é o documento, quem o produziu e a quem se "
                    "destina; (2) principais conceitos e estrutura; (3) o que muda na prática escolar; "
                    "(4) três pontos para debate em sala. Indique páginas quando os trechos "
                    "trouxerem essa informação."
                ),
            },
            {
                "role": "user",
                "content": f"Documento: {titulo} ({tipo}, {orgao}).\n\nTrechos:\n{texto}",
            },
        ]
        return self.chat(mensagens)
