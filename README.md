# IA Legal - Legislação brasileira de tecnologia

Ferramenta de busca e acompanhamento de **projetos de lei, leis e pareceres** relacionados a
tecnologia no Brasil. Foi pensada para **professores, pesquisadores e estudantes** que precisam
localizar rapidamente a legislação para preparar aulas, escrever artigos e fundamentar pesquisas.

## O que a ferramenta faz

- **Busca semântica** (IA) sobre proposições legislativas: pergunte em linguagem natural
  ("projetos sobre inteligência artificial", "regulação de dados pessoais") e receba os itens
  mais relevantes.
- **Perguntas com resposta fundamentada (RAG)**: um LLM responde usando apenas os textos
  legislativos recuperados e cita as fontes com `[1]`, `[2]`, etc.
- **Acompanhamento de tramitação**: situação atual, órgão e histórico recente de movimentações.
- **Resumo para aula**: gera resumo didático de uma proposição (resumo, pontos-chave, uso em sala
  e estágio da tramitação).
- **Citação pronta (ABNT)**: botão para copiar a referência formatada, útil para artigos.

## Fontes de dados

- **Câmara dos Deputados** - API de Dados Abertos (`dadosabertos.camara.leg.br`), filtrando pelo
  tema *Ciência, Tecnologia e Inovação* e, opcionalmente, *Comunicações*.
- **Senado Federal** - API de Dados Abertos (`legis.senado.leg.br`), com filtro por palavras-chave
  de tecnologia na ementa.

> Os dados são públicos e atualizados. Para fundamentar trabalhos acadêmicos, confirme sempre o
> texto oficial no portal da Câmara ou do Senado.

## Arquitetura

```
app/
  main.py            API FastAPI e rotas
  config.py          Configuração via .env
  models.py          Modelos de dados (Pydantic)
  db.py              Armazenamento SQLite (proposições e tramitações)
  sources/camara.py  Cliente da API da Câmara
  sources/senado.py  Cliente da API do Senado
  keywords.py        Filtro de temas de tecnologia
  ingest.py          Pipeline de sincronização e indexação
  rag.py             Embeddings + ChromaDB (busca semântica)
  llm.py             Integração com LLM (OpenAI-compatível/Ollama) e prompts
  static/            Interface web (HTML/CSS/JS)
scripts/sync.py      Sincronização via linha de comando
run.sh               Sobe o servidor local
share.sh             Sobe o servidor + link público (cloudflared)
Dockerfile           Imagem para deploy
data/                Banco SQLite e índice vetorial (gerados)
```

Fluxo: `APIs oficiais -> normalização -> SQLite -> embeddings -> ChromaDB -> busca/RAG`.

## Instalação

Requisitos: Python 3.10+.

```bash
./run.sh
```

O script cria o ambiente virtual, instala as dependências, gera o `.env` e sobe o servidor em
`http://127.0.0.1:8000`.

Alternativa manual:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/python -m uvicorn app.main:app --reload
```

## Configuração da IA

Edite o `.env`:

```env
LLM_PROVIDER=openai
LLM_BASE_URL=
LLM_API_KEY=sua-chave
LLM_MODEL=gpt-4o-mini
EMBEDDING_PROVIDER=auto
```

Funciona com qualquer provedor compatível com a API da OpenAI:

| Provedor | LLM_BASE_URL | Observação |
| --- | --- | --- |
| OpenAI | (vazio) | padrão |
| Groq | `https://api.groq.com/openai/v1` | rápido e gratuito em parte |
| Gemini | `https://generativelanguage.googleapis.com/v1beta/openai/` | via compatibilidade OpenAI |
| Ollama (local) | `http://localhost:11434/v1` | `LLM_PROVIDER=ollama`, sem custo |

- `EMBEDDING_PROVIDER=auto` usa embeddings da OpenAI quando há chave; caso contrário usa o modelo
  local do ChromaDB (gratuito, funciona offline após o primeiro download).
- Sem chave de LLM a ferramenta continua útil: a busca semântica e a listagem funcionam, apenas a
  geração de texto e o resumo ficam desativados.

## Uso

1. Abra `http://127.0.0.1:8000`.
2. Vá em **Configurações** e clique em **Iniciar sincronização** (comece com poucos anos e
   `Máx. por ano` baixo para testar; depois amplie).
3. Use as abas:
   - **Buscar legislação**: busca semântica com filtros por casa, tipo e ano.
   - **Perguntar à IA**: perguntas em linguagem natural com resposta fundamentada e fontes.
   - **Acompanhar andamento**: lista com a situação atual das proposições.
   - **Configurações**: sincronização e estado do sistema.

### Sincronização por linha de comando

```bash
.venv/bin/python scripts/sync.py --anos 2024 2023 --max 200
.venv/bin/python scripts/sync.py --anos 2022 --tipos PL PEC --sem-senado
```

Opções: `--anos`, `--tipos`, `--max`, `--sem-camara`, `--sem-senado`, `--sem-tramitacoes`,
`--sem-comunicacoes`.

## API

| Método | Rota | Descrição |
| --- | --- | --- |
| GET | `/api/health` | Estado do sistema e estatísticas |
| GET | `/api/stats` | Estatísticas da base |
| POST | `/api/search` | Busca semântica |
| POST | `/api/chat` | Pergunta com resposta (RAG) |
| GET | `/api/proposicoes` | Lista com filtros e paginação |
| GET | `/api/proposicoes/{id}` | Detalhe + tramitações |
| POST | `/api/proposicoes/{id}/resumo` | Resumo didático (IA) |
| POST | `/api/sync` | Sincronização síncrona |
| POST | `/api/sync/background` | Sincronização em segundo plano |
| GET | `/api/sync/status` | Progresso da sincronização |

Documentação interativa: `http://127.0.0.1:8000/docs`.

## Compartilhar para outra pessoa testar

O app é servido com caminhos relativos, então funciona por qualquer túnel ou host.

```bash
./share.sh                 # sobe o servidor + link público (cloudflared)
./share.sh --no-tunnel     # apenas rede local
./share.sh --port=9000     # porta diferente
```

O `share.sh` cria o `.venv`/`.env` se necessário, baixa o `cloudflared` em `.tools/` e imprime
um link `https://...trycloudflare.com` para enviar a quem vai testar. O link fica ativo enquanto o
terminal estiver aberto (use `tmux` ou `nohup` para manter). Na rede local, acesse
`http://SEU-IP:8000`.

> Sem `LLM_API_KEY` no `.env`, a aba "Perguntar à IA" apenas recupera trechos, sem gerar texto.
> O app não possui autenticação e expõe `/api/sync`; para deixar no ar por muito tempo, restrinja
> o acesso (token, VPN ou proxy reverso com senha).

## Deploy com Docker

```bash
cp .env.example .env   # configure as chaves
docker compose up --build -d
# http://localhost:8000
```

O `Dockerfile` usa Python 3.12 slim, roda como usuário não-root e persiste o banco/índice no volume
`/app/data`. Em plataformas como Render, Railway ou Fly.io, monte um disco persistente nesse caminho
para não perder a base sincronizada a cada deploy.

## Publicar na nuvem com link fixo (Render)

O repositório já inclui `render.yaml` e uma imagem Docker que embute a base de 496 proposições e
o modelo de embeddings. Assim funciona no plano gratuito do [Render](https://render.com), mesmo sem
disco persistente.

1. Envie o código para o GitHub:
   ```bash
   ./.tools/gh auth login        # GitHub.com > HTTPS > Login with a web browser
   ./publicar.sh                 # cria o repositório e envia
   ```
2. No Render: **New** > **Blueprint** > conecte o repositório `ia-legal`.
3. Quando pedir, informe a variável `LLM_API_KEY`. O `render.yaml` já vem pré-configurado para o
   **Groq** (plano gratuito): crie uma chave em https://console.groq.com/keys e cole aqui. Para usar
   OpenAI, troque `LLM_BASE_URL`, `LLM_MODEL` e a chave.
4. Clique em **Apply**. Ao terminar, o Render gera um link fixo
   `https://ia-legal.onrender.com`.

Observações do plano gratuito:

- O serviço "dorme" após alguns minutos sem uso; a primeira visita depois disso leva ~30–60 s.
- O sistema de arquivos é temporário: novas sincronizações feitas no site se perdem ao reiniciar.
  A base embutida permanece. Para persistir, use um disco pago montado em `/app/data`.
- As buscas usam embeddings locais (`EMBEDDING_PROVIDER=chroma`), compatíveis com o índice embutido;
  o `LLM_API_KEY` é usado apenas para gerar respostas e resumos.

## Personalização

- **Palavras-chave de tecnologia**: edite `app/keywords.py` (`TECH_KEYWORDS`).
- **Temas da Câmara**: constantes `TEMA_CIENCIA_TECNOLOGIA` e `TEMA_COMUNICACOES` em
  `app/sources/camara.py`.
- **Modelo de embeddings local**: `EMBEDDING_MODEL` (ex.: um modelo multilíngue melhora a busca
  em português).

## Limitações e boas práticas

- As APIs do Senado usam endpoints que estão sendo migrados para
  `/dadosabertos/processo/{idProcesso}`; o projeto trata falhas e continua com as demais fontes.
- A sincronização respeita um intervalo entre requisições (`HTTP_DELAY`) para não sobrecarregar as
  APIs públicas. Sincronizações grandes podem demorar.
- As respostas da IA são apoio à pesquisa, não substituem a leitura do texto legal oficial.
