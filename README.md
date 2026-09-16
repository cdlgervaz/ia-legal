# IAgora, profe? — Acervo inteligente de Políticas Educacionais

Ferramenta de busca e estudo de **leis, bases curriculares, pareceres e documentos
orientadores da educação brasileira**, pensada para professores e estudantes de licenciatura
da disciplina de Políticas Educacionais. Reúne um acervo curado, permite consultar **por tema
ou por documento**, **buscar palavras-chave dentro de um texto específico**, **perguntar à IA**
com resposta fundamentada e **gerar resumos didáticos**.

## O que a ferramenta faz

- **Consulta por tema**: currículo, gestão, formação docente, avaliação, financiamento,
  tecnologia e educação digital, IA na educação e inclusão.
- **Consulta por documento**: BNCC, BNCC Computação, BNC-Formação, LDB, PNE, PBIA etc.
- **Buscar dentro do documento**: palavra-chave com trecho e número de página, ou busca
  semântica (IA) restrita àquele documento.
- **Perguntar à IA (RAG)**: respostas baseadas apenas nos trechos recuperados, com citação das
  fontes `[1]`, `[2]`, além de página e link quando disponíveis.
- **Resumo para aula**: resumo didático de um documento inteiro ou de uma proposição
  legislativa (o que é, pontos-chave, o que muda na prática escolar, temas para debate).
- **Acompanhamento de tramitação**: proposições da Câmara, do Senado, pareceres do CNE e atos do
  Diário Oficial, incluindo o Marco Legal da IA (PL 2338/2023, em tramitação).
- **Citação pronta (ABNT)** para trabalhos acadêmicos.

## Acervo padrão (catálogo)

| Documento | Tipo | Temas |
| --- | --- | --- |
| Constituição Federal de 1988 (arts. 205-214) | Constituição | gestão, financiamento, currículo |
| Lei nº 9.394/1996 - LDB | Lei | currículo, gestão, formação docente, avaliação |
| Lei nº 13.005/2014 - PNE 2014-2024 | Lei | financiamento, gestão, formação docente, avaliação |
| Lei nº 14.533/2023 - Política Nacional de Educação Digital | Lei | tecnologia, IA, formação docente, currículo |
| Lei nº 13.709/2018 - LGPD | Lei | IA, tecnologia |
| Lei nº 14.113/2020 - FUNDEB | Lei | financiamento, gestão |
| Lei nº 15.100/2025 - Dispositivos digitais na educação básica | Lei | tecnologia, currículo, gestão |
| BNCC - Educação Infantil e Ensino Fundamental | Base Nacional | currículo, avaliação |
| BNCC - Ensino Médio | Base Nacional | currículo, avaliação |
| BNCC Computação (anexo ao Parecer CNE/CEB 2/2022) | Base Nacional | tecnologia, currículo, IA |
| Resolução CNE/CEB 1/2022 - Computação na Educação Básica | Resolução | tecnologia, currículo |
| Parecer CNE/CEB 2/2022 - BNCC Computação | Parecer | tecnologia, currículo |
| Resolução CNE/CP 2/2017 - Implantação da BNCC | Resolução | currículo, gestão |
| Resolução CNE/CEB 2/2025 - Dispositivos digitais nos espaços escolares | Resolução | tecnologia, currículo, gestão |
| Parecer CNE/CEB 4/2025 - Uso de dispositivos digitais | Parecer | tecnologia, currículo |
| Resolução CNE/CP 2/2019 - BNC-Formação | Resolução | formação docente, currículo |
| Resolução CNE/CP 1/2020 - BNC-Formação Continuada | Resolução | formação docente, currículo |
| Resolução CNE/CP 2/2022 - Alteração da BNC-Formação | Resolução | formação docente, currículo |
| Parecer CNE/CP 4/2021 - BNC Diretor Escolar | Parecer | gestão, formação docente |
| Estratégia Brasileira de Inteligência Artificial (EBIA) | Estratégia | IA, tecnologia, formação docente |
| Plano Brasileiro de IA (PBIA 2024-2028) | Plano | IA, tecnologia |
| PL 2338/2023 - Marco Legal da IA (em tramitação) | Proposição | IA, tecnologia |

O catálogo fica em `app/catalog.py` e pode ser editado livremente. PBIA e PL 2338 aparecem como
links oficiais; o PL é capturado também pela sincronização (Câmara/Senado).

### Categoria e vigência (1990+)

Cada documento tem uma **categoria**, usada no filtro da busca — **Lei**, **Parecer** ou
**Documento norteador** — e um campo de **vigência** (Vigente / Substituído), indicando quando foi
superado e por qual norma. Foram incluídos, a partir de 1990:

- **Leis e decretos:** LDB (9.394/1996), Lei 13.415/2017 e Lei 14.945/2024 (ensino médio), Marco
  Civil da Internet (12.965/2014), LGPD (13.709/2018), PNED (14.533/2023), Decreto 9.057/2017
  (EaD), Decreto 11.713/2023 (regulamenta a PNED).
- **Pareceres:** Parecer CNE nº 15/2026 (diretrizes para uso da IA na educação), CNE/CP 22/2019 e
  14/2020 (formação de professores), CNE/CEB 7/2010 (DCN da Educação Básica) e 5/2011 (DCNEM,
  substituído), CNE/CEB 2/2022 (BNCC Computação) e CNE/CEB 4/2025 (dispositivos digitais).
- **Documentos norteadores:** BNCC (EI/EF e EM), BNCC Computação, DCN da Educação Básica e do
  Ensino Médio, PCNs (substituídos pela BNCC), EBIA e Estratégia Brasileira de Educação Midiática.

No filtro **"Tipo de documento"** da busca, a resposta inclui **apenas** a categoria selecionada, e
cada resultado mostra um selo **Vigente** ou **Substituído/Revogado** (com a norma que o
substituiu, quando houver). Observe que o Parecer CNE nº 15/2026 está como *parecer relatado*
(set/2026), ainda em revisão técnica antes da publicação no Diário Oficial da União.

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

## Primeiro uso

1. Abra `http://127.0.0.1:8000` e vá em **Documentos** → **Importar catálogo**.
   O download e a indexação rodam em segundo plano; acompanhe pelo status na mesma tela.
   - A primeira importação baixa os arquivos oficiais para `data/documentos/` e indexa os
     trechos. Você só precisa fazer isso uma vez; depois as consultas são instantâneas.
   - Sem internet no momento, coloque os arquivos em `data/documentos/` manualmente e importe
     com `--sem-baixar` (veja abaixo).
2. (Opcional, mas recomendado) Configure uma chave de LLM no `.env` para respostas e resumos.
   Sem chave, a busca, a busca dentro do documento e a listagem continuam funcionando.

### Importação por linha de comando

```bash
.venv/bin/python scripts/importar_documentos.py --listar          # catálogo e status
.venv/bin/python scripts/importar_documentos.py --todos           # importa todo o catálogo
.venv/bin/python scripts/importar_documentos.py --ids ldb-9394-1996 bncc-computacao
.venv/bin/python scripts/importar_documentos.py --ids bncc-ei-ef --forcar   # reimporta
.venv/bin/python scripts/importar_documentos.py --todos --sem-baixar        # usa arquivos locais
```

### Adicionar documentos próprios (ex.: Matriz de Saberes)

Use um PDF/HTML baixado oficialmente:

```bash
.venv/bin/python scripts/importar_documentos.py \
  --arquivo data/documentos/matriz-saberes.pdf \
  --id matriz-saberes \
  --titulo "Matriz de Saberes Docentes" \
  --tipo Matriz --ano 2025 --orgao "Sua instituição" \
  --temas formacao_docente curriculo
```

O documento passa a aparecer na aba **Documentos** com busca interna e resumo. Se preferir, edite
`app/catalog.py` para incluí-lo no catálogo padrão.

## Uso

### Buscar

- Digite a consulta e refine por **tema**, **documento**, casa, tipo e ano. A busca combina
  semântica (IA) com palavra-chave — em português, com ou sem acento.
- Resultados de documentos mostram o trecho e a página; a busca também alcança proposições
  legislativas.

### Documentos

- **Importar catálogo**: baixa e indexa os documentos oficiais.
- **Abrir e buscar no documento**: abre a ficha e habilita a busca interna.
  - *Palavra-chave*: retorna trechos exatos com página (funciona offline e sem LLM).
  - *Semântica (IA)*: encontra trechos por significado.
- **Gerar resumo para aula (IA)**: resumo didático do documento inteiro.
- **Perguntar**: leva a dúvida para o chat já filtrado por aquele documento.

### Perguntar à IA

- Sem filtro: responde usando todo o acervo (documentos + proposições).
- Com filtro de tema/documento: restringe a resposta àqueles itens.
- Toda resposta cita as fontes `[n]` e lista documento, página e link.

## Configuração da IA

O projeto usa **apenas modelos de código aberto**. Por padrão roda local com o Ollama:

```bash
# 1. Instale o Ollama (https://ollama.com) e baixe um modelo aberto:
ollama pull qwen2.5:1.5b   # mais rapido (recomendado em CPU)
ollama pull qwen2.5:3b     # opcional: melhor qualidade, mais lento
```

```env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:1.5b
LLM_MAX_TOKENS=500
EMBEDDING_PROVIDER=chroma
```

**Desempenho**: em CPU sem GPU, o `qwen2.5:1.5b` gera ~8 tokens/s e o `qwen2.5:3b` ~4–5 tokens/s
(uma resposta de ~500 tokens leva ~1 min no 1.5b). Para respostas rápidas sem sair do código aberto, use um serviço que hospeda modelos
abertos (protocolo compatível), mantendo `EMBEDDING_PROVIDER=chroma`:

| Serviço | LLM_BASE_URL | Modelo aberto sugerido |
| --- | --- | --- |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| OpenRouter | `https://openrouter.ai/api/v1` | modelos `:free` |
| Together | `https://api.together.xyz/v1` | Llama / Qwen |

Nesses casos use `LLM_PROVIDER=openrouter` (rótulo genérico de API compatível; não tem relação com
a empresa OpenAI) e coloque a `LLM_API_KEY` do serviço. Para desligar a geração: `LLM_PROVIDER=none`.

- `EMBEDDING_PROVIDER=chroma` mantém os embeddings no modelo local do ChromaDB (aberto, offline).
  **Mantenha esse valor** para continuar compatível com o índice já construído.
- Sem LLM, a busca continua funcionando; apenas a geração de texto e os resumos ficam desativados.

## Compartilhar com os alunos (autenticação)

O app **não tem cadastro de usuários**, mas você pode proteger o acesso com usuário e senha
(HTTP Basic) definindo no `.env`:

```env
APP_USER=professor
APP_PASSWORD=uma-senha-combinada-com-a-turma
```

Com `APP_PASSWORD` preenchido, todo o site — inclusive as rotas de importação e sincronização —
passa a exigir a senha. Em deploys na nuvem, defina essas variáveis no painel do serviço
(no Render, `APP_PASSWORD` está no `render.yaml` como variável secreta).

```bash
./share.sh                 # servidor + link público (cloudflared)
./share.sh --no-tunnel     # apenas rede local
./share.sh --port=9000     # outra porta
```

## Deploy com Docker

```bash
cp .env.example .env   # configure as chaves e a senha
docker compose up --build -d
# http://localhost:8000
```

O `Dockerfile` usa Python 3.12 slim e persiste banco/índice no volume `/app/data`. Em
plataformas como Render, Railway ou Fly.io, monte um disco persistente nesse caminho para não
perder importações feitas no site.

## Publicar na nuvem com link fixo (Render)

O repositório já inclui `render.yaml` e a imagem embute o índice em `data/` (banco SQLite,
chunks e Chroma). Assim funciona no plano gratuito do Render, mesmo sem disco persistente.

1. Envie o código para o GitHub:
   ```bash
   ./.tools/gh auth login        # GitHub.com > HTTPS > Login with a web browser
   ./publicar.sh                 # cria o repositório e envia
   ```
2. No Render: **New** > **Blueprint** > conecte o repositório.
3. Informe `LLM_API_KEY` e `APP_PASSWORD` quando pedir. O `render.yaml` já vem pré-configurado
   para o **Groq** (plano gratuito): crie uma chave em https://console.groq.com/keys.
4. Clique em **Apply**. O Render gera um link fixo `https://<servico>.onrender.com`.

Observações do plano gratuito:

- O serviço "dorme" após alguns minutos sem uso; a primeira visita leva ~30–60 s.
- O sistema de arquivos é temporário: importações/sincronizações feitas no site se perdem ao
  reiniciar. A base embutida no deploy permanece. Para persistir, use um disco pago em `/app/data`.
- As buscas usam embeddings locais (`EMBEDDING_PROVIDER=chroma`), compatíveis com o índice
  embutido; `LLM_API_KEY` é usado apenas para respostas e resumos.

## API

| Método | Rota | Descrição |
| --- | --- | --- |
| GET | `/api/health` | Estado do sistema e estatísticas |
| GET | `/api/stats` | Estatísticas da base |
| GET | `/api/temas` | Lista de temas |
| POST | `/api/search` | Busca híbrida (semântica + palavra-chave) com filtros |
| POST | `/api/chat` | Pergunta com resposta fundamentada (RAG) |
| GET | `/api/documentos` | Catálogo com status de importação |
| GET | `/api/documentos/{id}` | Ficha do documento |
| GET | `/api/documentos/{id}/busca?q=` | Busca dentro do documento (`modo=chave` ou `semantica`) |
| GET | `/api/documentos/{id}/conteudo` | Trechos indexados (leitura paginada) |
| POST | `/api/documentos/{id}/resumo` | Resumo didático do documento (IA) |
| POST | `/api/documentos/importar` | Importação síncrona do catálogo |
| POST | `/api/documentos/importar/background` | Importação em segundo plano |
| GET | `/api/documentos/importar/status` | Progresso da importação |
| GET | `/api/proposicoes` | Lista com filtros e paginação |
| GET | `/api/proposicoes/{id}` | Detalhe + tramitações |
| POST | `/api/proposicoes/{id}/resumo` | Resumo didático (IA) |
| POST | `/api/sync` | Sincronização síncrona |
| POST | `/api/sync/background` | Sincronização em segundo plano |
| GET | `/api/sync/status` | Progresso da sincronização |

Documentação interativa: `http://127.0.0.1:8000/docs`.

## Arquitetura

```
app/
  main.py               API FastAPI, rotas e autenticação opcional
  config.py             Configuração via .env
  models.py             Modelos de dados (Pydantic)
  catalog.py            Catálogo curado de documentos oficiais
  temas.py              Taxonomia de temas e classificação
  documentos.py         Download, extração PDF/HTML, chunking e importação
  db.py                 SQLite (proposições, documentos e chunks)
  rag.py                Embeddings + ChromaDB (busca híbrida)
  llm.py                Integração com LLM e prompts didáticos
  ingest.py             Sincronização de proposições (Câmara/Senado/CNE/DOU)
  sources/              Clientes das APIs oficiais
  texto.py              Normalização de texto (acentos, trechos)
  static/               Interface web (HTML/CSS/JS)
scripts/
  importar_documentos.py  Importa o catálogo ou arquivos locais
  sync.py                 Sincroniza proposições via linha de comando
data/
  documentos/         PDFs/HTML baixados (não versionados)
  chroma/             Índice vetorial
  ialegal.db          Banco SQLite (proposições, documentos, chunks)
```

Fluxo: `catálogo/APIs oficiais -> download -> extração -> chunking -> SQLite + ChromaDB ->
busca híbrida/RAG -> interface`.

## Personalização

- **Acervo**: edite `app/catalog.py` (documentos, links, temas).
- **Temas**: edite `app/temas.py` (palavras-chave por tema).
- **Palavras-chave de tecnologia/educação** (usadas na sincronização): `app/keywords.py`.
- **Temas da Câmara**: constantes em `app/sources/camara.py`.
- **Trechos**: `CHUNK_SIZE` e `CHUNK_OVERLAP` no `.env` (padrão 1400/250 caracteres).

## Licença e uso

**© Camila Gervaz — todos os direitos reservados.**

- **Situação:** versão em desenvolvimento (**fase de testes**).
- **Uso permitido:** estudo, ensino e pesquisa. **Uso comercial proibido** sem autorização.
- **Citação obrigatória** ao utilizar o acervo ou as respostas (ver `CREDITOS.md`).
- **Licença do conteúdo:** Creative Commons **CC BY-NC-ND 4.0** (Atribuição — NãoComercial —
  **SemDerivadas**). Permite copiar e distribuir **sem alterações**, sem fins comerciais e com
  citação. **Não permite adaptações** — pelo menos por ora. Texto integral em [`LICENSE`](LICENSE).
- **Software e dependências:** mantêm suas próprias licenças. Os modelos de IA usados são de
  código aberto (Qwen 2.5, Gemma, NVIDIA Nemotron, Z-AI GLM) e os embeddings são locais
  (`all-MiniLM-L6-v2`).
- **Documentos oficiais:** textos de leis e atos oficiais não são protegidos por direitos
  autorais (Lei nº 9.610/1998, art. 8º, IV); a compilação e a interface são.
- **Privacidade:** não há cadastro; não insira dados pessoais nas perguntas. Detalhes em
  [`POLITICA_DE_PRIVACIDADE.md`](POLITICA_DE_PRIVACIDADE.md) e
  [`TERMOS_DE_USO.md`](TERMOS_DE_USO.md).

> Observação: o Creative Commons **não é recomendado para o código-fonte**. Para o software,
> escolha uma licença de software (ex.: MIT, GPL, Apache 2.0 ou PolyForm Noncommercial); a
> CC BY-NC-ND 4.0 vale para o **conteúdo** (textos, descrições, materiais).

## Limitações e boas práticas

- As respostas da IA são apoio ao estudo, não substituem a leitura do texto oficial.
- Alguns PDFs do MEC têm extração de texto imperfeita em tabelas (palavras coladas); nesses
  casos prefira a busca por palavra-chave simples ou consulte o PDF oficial.
- Links antigos do `portal.mec.gov.br` podem estar indisponíveis durante a migração para
  `gov.br`; os documentos do catálogo usam os endereços atuais.
- A sincronização respeita um intervalo entre requisições (`HTTP_DELAY`) para não sobrecarregar
  as APIs públicas.
- O PL 2338/2023 (Marco Legal da IA) e o PBIA são acompanhados por link/proposição; confirme
  sempre a versão mais recente nos portais oficiais.
