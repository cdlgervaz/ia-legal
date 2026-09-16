from typing import List, Optional

from .config import Settings


class LLMNotConfigured(RuntimeError):
    pass


SYSTEM_PROMPT = """Você é um assistente de pesquisa legislativa brasileira especializado em \
tecnologia, auxiliando professores, pesquisadores e estudantes a preparar aulas, artigos e \
projetos de pesquisa.

Regras:
1. Baseie-se SOMENTE no contexto legislativo fornecido. Não invente leis, números, datas ou \
tramitações.
2. Quando o contexto não contiver a informação, diga explicitamente o que não foi encontrado.
3. Sempre cite as fontes usando os marcadores [1], [2], ... correspondentes ao contexto.
4. Ao final, liste as fontes citadas com identificação e link quando disponível.
5. Utilize linguagem clara, didática e objetiva, adequada ao ambiente acadêmico.
6. Diferencie claramente o que é texto de lei vigente, o que é projeto em tramitação e o que é \
parecer ou manifestação.
7. Quando útil para uma aula, organize a resposta em tópicos e destaque a relevância prática."""


def build_context(fontes: List) -> str:
    blocos = []
    for idx, hit in enumerate(fontes, start=1):
        prop = hit.proposicao
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
        blocos.append("\n".join(linhas))
    return "\n\n".join(blocos)


def build_user_prompt(query: str, contexto: str) -> str:
    return (
        "Pergunta do usuário:\n"
        f"{query}\n\n"
        "Contexto legislativo recuperado:\n"
        f"{contexto}\n\n"
        "Responda em português, de forma didática, citando as fontes com [n]."
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
        resposta = client.chat.completions.create(
            model=self.settings.llm_model,
            messages=mensagens,
            temperature=self.settings.llm_temperature if temperature is None else temperature,
        )
        return (resposta.choices[0].message.content or "").strip()

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
                    "Você é um professor de direito e tecnologia. Explique a proposição "
                    "legislativa a seguir de forma didática, em português, com: (1) resumo em "
                    "até 3 parágrafos; (2) pontos-chave em tópicos; (3) possível uso em sala de "
                    "aula; (4) estágio atual da tramitação. Baseie-se apenas nos dados fornecidos."
                ),
            },
            {"role": "user", "content": "\n".join(linhas)},
        ]
        return self.chat(mensagens)
