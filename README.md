# Agente de Conhecimento Areco

Aplicação demonstrativa para o desafio técnico de Analista de IA da Areco. Um orquestrador direciona perguntas a Financeiro, Informações Internas ou Ouvidoria, consulta bases sintéticas e retorna resposta, confiança, fontes e ID de execução.

Repositório: [github.com/Rafaeldeoliveira87/Desafio-tecnico-areco](https://github.com/Rafaeldeoliveira87/Desafio-tecnico-areco).

## Funcionalidades

- API FastAPI com schemas Pydantic e Swagger.
- Classificação com categoria normalizada, escore heurístico de confiança e justificativa.
- Agregações financeiras determinísticas com `Decimal`: filtros por centro de custo, departamento, categoria, status e método de pagamento; períodos (mês, intervalo, trimestre, semestre, ano); agrupamentos e rankings; indicadores de **execução orçamentária** e **inadimplência** conforme `indicadores_e_regras.json`. Todo filtro aplicado é declarado na resposta, e filtros desconhecidos (ex.: `CC999`) geram aviso em vez de resultado enganoso.
- Desempate de domínio por intenção (procedimento × consulta de valores) para perguntas mistas, como "Quero reembolso de uma despesa de viagem".
- Recuperação interna com reforço por tema do documento (ponderado por IDF) e resposta focada nos itens relevantes.
- Avaliação reprodutível: `python -m scripts.evaluate` roda os 12 casos de `testes/perguntas_avaliacao.json` e gera `logs/evaluation_report.md`.
- Recuperação textual BM25 local em políticas Markdown e FAQ, com filtro de domínio.
- Consulta exata de protocolo e status de Ouvidoria.
- Fallback sem chave externa; provider OpenAI-compatible opcional, desabilitado por padrão.
- Interface responsiva com fontes, indicadores, estados de carregamento e erros.
- Logs JSON estruturados sem o texto literal da pergunta.

## Inicialização rápida com Docker

Pré-requisitos: Docker Engine/Desktop e Docker Compose.

```bash
# opcional: crie configuração local a partir do exemplo
cp .env.example .env
# PowerShell: Copy-Item .env.example .env
docker compose up --build
```

Abra [http://localhost:8000](http://localhost:8000) e a documentação da API em [http://localhost:8000/docs](http://localhost:8000/docs). O Compose monta as bases em modo somente leitura e persiste logs em um volume nomeado. Para parar: `Ctrl+C` ou `docker compose down`.

A execução em Docker Desktop foi validada neste ambiente: o serviço `desafiotecnico-agente-1` ficou **healthy** na porta 8000. Prints e log sanitizado estão em [docs/evidencias/](docs/evidencias/).

A aplicação inicia em modo local sem credenciais. Nenhum provider externo é chamado, a menos que o processamento externo seja explicitamente habilitado.

## Execução local sem Docker

Requer Python 3.11+.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Em macOS/Linux, use `python3 -m venv .venv`, `source .venv/bin/activate` e os mesmos comandos de instalação/execução. Se `Activate.ps1` for bloqueado, execute `\.venv\Scripts\python.exe -m pip install -r requirements.txt` e `\.venv\Scripts\python.exe -m uvicorn app.main:app --reload`.

Para desenvolver/testar, instale `python -m pip install -r requirements-dev.txt`.

## Configuração

Copie `.env.example` para `.env` para o Compose. `.env` é ignorado pelo Git. Variáveis principais:

| Variável | Padrão | Uso |
|---|---|---|
| `APP_ENV` | `development` | Ambiente; desativa reindex em `production`. |
| `PORT` | `8000` | Porta publicada pelo Compose. |
| `CLASSIFICATION_CONFIDENCE_THRESHOLD` | `0.55` | Abaixo disso, o orquestrador pede esclarecimento. |
| `MAX_QUESTION_LENGTH` | `1500` | Comprimento máximo da pergunta. |
| `ALLOWED_ORIGINS` | vazio | Origens CORS externas permitidas; vazio é restritivo. |
| `REINDEX_ENABLED` | `true` | Permite reindex em desenvolvimento; produção sempre retorna 404. |
| `LLM_PROVIDER` | `none` | Use `openai_compatible` para habilitar provider. |
| `EXTERNAL_PROCESSING_ENABLED` | `false` | Opt-in obrigatório para envio a provider externo. |
| `LLM_API_KEY` | vazio | Chave do provider; nunca versionar. |
| `LLM_MODEL` | vazio | Modelo configurado no provider. |
| `LLM_BASE_URL` | endpoint OpenAI-compatible | Endpoint HTTPS do provider; HTTP permitido somente em loopback. |
| `LLM_TIMEOUT_SECONDS` | `12` | Timeout por chamada. |
| `LLM_MAX_RETRIES` | `1` | Repetições limitadas (0–3). |

O modo local funciona sem essas credenciais. Se habilitar o provider, perguntas e trechos recuperados podem sair do ambiente local; use apenas após avaliar privacidade e autorização.

## Bases e ingestão

As fontes originais estão nas pastas `financeiro/`, `informacoes_internas/` e `ouvidoria/`. O mapeamento de campos está em `documentacao/dicionario_de_dados.md`; regras de cálculo e enumerações ficam nos JSONs de referência. Os arquivos originais não são modificados.

Ao iniciar, a aplicação cria o índice textual local dos dez Markdown e do FAQ em `data/processed/knowledge_index.json`. Para reconstruir após adicionar/alterar documentos internos:

```powershell
python -m scripts.ingest
```

ou, em desenvolvimento, `POST /api/v1/knowledge/reindex`. O índice deriva somente Informações Internas. Financeiro e Ouvidoria consultam os CSV/JSON tabulares por operações controladas. No container, as três pastas de fonte são montadas como somente leitura.

## API

- `GET /health`: estado e versão.
- `GET /api/v1/agents`: lista categorias e agentes.
- `POST /api/v1/chat`: pergunta, `session_id` opcional; retorna execução, categoria, confidence score, justificativa, agente, resposta, fontes, duração e timestamp.
- `POST /api/v1/knowledge/reindex`: reconstrói índice em desenvolvimento; desabilitado em produção.

Exemplo:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"Qual o status do protocolo OUV-0002?"}'
```

Perguntas de exemplo (inclui as de maior valor demonstrativo):

- **Financeiro:** “Quanto foi gasto em despesas pagas no período de janeiro a março de 2025?”
- **Financeiro (avançado):** “Qual a execução orçamentária da Tecnologia em 2025?”, “Qual departamento mais gastou em 2025?”, “Despesas por categoria no primeiro trimestre de 2025”, “Qual a inadimplência de recebíveis?”
- **Informações internas:** “Como solicito férias?”
- **Ouvidoria:** “Qual o status do protocolo OUV-0002?”

## Testes, lint e formatação

```powershell
python -m pytest -q
python -m scripts.evaluate   # avaliação dos 12 casos do desafio
python -m pytest -q -m "not integration"
python -m pytest --cov=app --cov-report=term-missing
ruff check .
ruff format --check .
```

Veja [docs/TESTING.md](docs/TESTING.md) para a estratégia e o resultado real da última execução.

## Arquitetura e estrutura

```text
app/
  agents/       orquestrador e agentes de domínio
  api/routes/   endpoints HTTP versionados
  core/         configuração, logging e exceções
  knowledge/    loaders, chunking, índice e BM25
  llm/          contrato e provider opcional
  models/       schemas Pydantic
  services/     regras tabulares determinísticas
frontend/       HTML, CSS e JavaScript puro
financeiro/     CSV e JSON sintéticos
informacoes_internas/ Markdown e FAQ JSON
ouvidoria/      CSV e JSON sintéticos
scripts/        reconstrução do índice
 tests/         testes unitários e de integração
 docs/          arquitetura, decisões, testes, limites e interação com IA
 logs/          JSONL runtime (ignorado pelo Git)
```

Diagrama, fluxo e estratégia estão em [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Decisões e alternativas estão em [docs/DECISIONS.md](docs/DECISIONS.md).

## Logs e privacidade

`logs/interactions.jsonl` registra UUID de execução, timestamp, hash e tamanho da pergunta, domínio, confiança, agente, fontes, duração, status e classe do erro. Não registra o texto literal, segredos nem cabeçalhos. O arquivo é rotacionado e ignorado pelo Git. No Compose, os logs estão no volume `logs_data`; remova dados locais com `docker compose down -v` (isso apaga o volume de logs). Em execução local, pare o servidor e remova `logs/interactions.jsonl` e eventuais arquivos rotacionados.

As bases são sintéticas e não representam dados reais. Não envie informações pessoais ou segredos para o sistema. Não versionar `.env` ou chaves de API.

## Problemas comuns

- **`No module named 'fastapi'`:** instale `requirements.txt` no mesmo `.venv` que usará para executar Uvicorn; não rode `app/main.py` diretamente.
- **Porta 8000 ocupada:** pare o outro servidor ou defina `PORT=8001` no `.env` do Compose.
- **Docker não reconhecido:** instale/inicie Docker Desktop/Engine ou siga a execução local com Python.
- **Sem resposta semântica:** o modo local usa BM25 e regras; reformule com termos dos documentos. Ele não é um LLM.
- **Provider externo não ativo:** confirme opt-in, provider, modelo e credencial no ambiente; o fallback local continua disponível.

## Limitações e evolução

A classificação é baseada em regras lexicais e a confiança não é calibrada. BM25 melhora correspondência em relação a palavras-chave simples, mas não compreende todos os sinônimos. Consultas tabulares cobrem operações delimitadas, não perguntas arbitrárias. Não há autenticação, controle por perfil ou rate limiting; execute em ambiente local/confiável. O container foi validado neste ambiente; o provider LLM real permanece opcional e não foi chamado. Consulte [docs/LIMITATIONS.md](docs/LIMITATIONS.md) e [FINAL_REVIEW.md](FINAL_REVIEW.md).

## Registro do desenvolvimento

O desafio pede o histórico de uso de IA, não apenas o código. Este repositório entrega:

| Artefato | Função |
|---|---|
| [AGENTS.md](AGENTS.md) | Instruções permanentes ao agente de IA |
| [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) | Cronologia das fases, problemas e validações |
| [docs/AI_INTERACTIONS.md](docs/AI_INTERACTIONS.md) | Registro estruturado das sessões (solicitações, propostas, decisões, descartes) |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Decisões de arquitetura |
| [docs/evidencias/](docs/evidencias/) | Relatório dos 12 casos, log JSONL sanitizado e prints Docker/Swagger |

A ferramenta não disponibilizou exportação oficial completa das conversas. Os arquivos acima são o histórico estruturado, sem credenciais.
