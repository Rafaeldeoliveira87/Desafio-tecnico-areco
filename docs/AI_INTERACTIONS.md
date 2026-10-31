# Registro de interações com ferramentas de IA

Documento exigido pelo desafio técnico da Areco. Descreve como as ferramentas de IA foram usadas para projetar, implementar, validar e corrigir a solução.

## Escopo e método

| Item | Registro |
|---|---|
| Ferramenta principal | Cursor (agente de código no workspace do desafio) |
| Período | 29 a 31 de outubro de 2026 |
| Natureza deste arquivo | Síntese estruturada das sessões relevantes, atualizada ao longo do desenvolvimento |
| O que não é | Transcrição literal completa da ferramenta; a exportação nativa integral nem sempre está disponível |
| Dados omitidos | Chaves de API, tokens, senhas, cabeçalhos de autorização e dados pessoais |
| Complementos | `AGENTS.md` (instruções ao agente), `DEVELOPMENT_LOG.md` (cronologia de fases), `docs/DECISIONS.md` (ADRs) |

Convenções usadas em cada sessão:

- **Solicitação:** pedido efetivo (resumido, sem reproduzir mensagens informais).
- **Proposta da IA:** solução sugerida.
- **Decisão:** aceita, aceita com alteração ou descartada, e o motivo.
- **Validação:** comando ou inspeção realmente executados, ou limitação declarada.

## Visão geral do processo

| Data | Fase | Resultado |
|---|---|---|
| 2026-10-29 | Leitura do enunciado e primeira versão executável | API mínima, frontend simples, Docker inicial; avaliação dos 12 casos ainda não executada |
| 2026-10-29 | Diagnóstico de ambiente | `ModuleNotFoundError: fastapi` ao executar `app/main.py` no Python global; correção via `.venv` e Uvicorn |
| 2026-10-30 | Fases 1–10 (descoberta até auditoria) | Arquitetura modular, RAG lexical, agentes, API `/api/v1`, testes, documentação |
| 2026-10-31 | Revisão crítica | Correção de filtros financeiros, desempate de intenção e recuperação interna |
| 2026-10-31 | Empacotamento da entrega | Evidências Docker, profissionalização deste registro e publicação no GitHub |

## Sessões

### S01 — 2026-10-29 — Interpretação do enunciado

| Campo | Registro |
|---|---|
| Solicitação | Analisar o e-mail do desafio e identificar requisitos de entrega. |
| Proposta da IA | Aplicação FastAPI com frontend HTML/CSS/JS, orquestrador para três domínios, uso das bases anexadas, Docker, README e registro contínuo do desenvolvimento. |
| Decisão | **Aceita.** O escopo do enunciado foi adotado como contrato da entrega. |
| Artefatos | `AGENTS.md` (criação), início de `DEVELOPMENT_LOG.md`. |
| Validação | Inspeção estática do manifesto, dicionário de dados, CSV/JSON/Markdown e conjunto de avaliação. Sem teste funcional nesta sessão. |

### S02 — 2026-10-29 — Primeira implementação

| Campo | Registro |
|---|---|
| Solicitação | Construir a solução do desafio. |
| Proposta da IA | Modo local sem chave de API; roteamento por regras; cálculos com `Decimal`; protocolo de Ouvidoria exato; recuperação lexical; frontend simples; Docker. |
| Decisão | **Aceita.** Provider externo ficou opcional para a demonstração ser reproduzível após o clone. |
| Descarte | Não exigir LLM pago para a aplicação subir. Motivo: o avaliador precisa clonar e executar sem credenciais. |
| Artefatos | `app/main.py`, `frontend/`, Dockerfile inicial, `.env.example`, README. |
| Validação | Não houve execução dos 12 casos de avaliação nesta sessão; a lacuna foi registrada. |

### S03 — 2026-10-29 — Falha de inicialização

| Campo | Registro |
|---|---|
| Solicitação | Diagnosticar `ModuleNotFoundError: No module named 'fastapi'` ao executar `app/main.py`. |
| Proposta da IA | Criar e ativar `.venv`, instalar `requirements.txt` e iniciar com `python -m uvicorn app.main:app --reload`. |
| Decisão | **Aceita.** A execução direta do módulo foi desaconselhada. |
| Validação | Em 2026-10-30 o ambiente virtual continha FastAPI e Uvicorn. Isso ainda não comprovava health check HTTP. |

### S04 — 2026-10-30 — Fase 1, descoberta

| Campo | Registro |
|---|---|
| Solicitação | Reorganizar o projeto em fases, com arquitetura modular, confiança, fontes, execution ID, testes e auditoria. Iniciar pela descoberta, sem implementar ainda. |
| Proposta da IA | Inventariar bases sem alterá-las; mapear os três domínios; registrar riscos de log e de cálculo. |
| Decisão | **Aceita.** |
| Inventário | 300 lançamentos, 144 linhas de orçamento, 180 manifestações, 10 políticas Markdown, 7 itens de FAQ, 12 casos de avaliação. |
| Validação | Contagens e cabeçalhos conferidos com Python do `.venv`. Inspeção estática, não funcional. |

### S05 — 2026-10-30 — Fase 2, arquitetura

| Campo | Registro |
|---|---|
| Solicitação | Definir fluxo, fronteiras e ADRs antes da implementação. |
| Proposta da IA | CSV/JSON tabulares determinísticos; BM25 local para Markdown/FAQ; LLM opcional com opt-in; log sem pergunta literal; API em `/api/v1`. |
| Alternativas consideradas | SQL gerado por LLM; Postgres; embeddings; provider obrigatório; log com texto integral; CORS aberto. |
| Decisão | **Aceita** a proposta lexical/determinística. Provider e hospedagem externa **não** foram escolhidos pelo desenvolvedor. |
| Artefatos | `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`. |
| Validação | Revisão documental contra os formatos reais. Sem alteração de código de runtime. |

### S06 — 2026-10-30 — Fase 3, estrutura da API

| Campo | Registro |
|---|---|
| Solicitação | Modularizar configuração, schemas, logging e health. |
| Proposta da IA | Pydantic, CORS restritivo, erros sem stack trace, health síncrono. |
| Problema | `TestClient` exigia `httpx`, ainda ausente; chamada async sem event loop gerou aviso. |
| Decisão | **Aceita com alteração:** health passou a síncrono; `httpx` foi declarado em desenvolvimento. |
| Validação | Import da app OK; `/health` retornou `status=ok`, `version=1.0.0`; OpenAPI listou o endpoint. TestClient ainda não executado. |

### S07 — 2026-10-30 — Fase 4, ingestão e recuperação

| Campo | Registro |
|---|---|
| Solicitação | Indexar Informações Internas sem modificar originais. |
| Proposta da IA | Chunking por seção, índice em `data/processed/`, BM25 com filtro de domínio. |
| Problema 1 | `python scripts/ingest.py` falhou com `ModuleNotFoundError: app`. |
| Correção | Execução via `python -m scripts.ingest`. |
| Problema 2 | FAQ de acessos superava política de compras em consulta no plural. |
| Correção | Normalização simples de plurais em português. |
| Decisão | **Aceita com alteração** (script como módulo + normalização). Embeddings **descartados** nesta etapa pelo volume pequeno e pela necessidade de execução offline. |
| Validação | 11 fontes, 22 chunks; consultas internas recuperaram documentos esperados; filtro `ouvidoria` retornou 0 chunks internos. |

### S08 — 2026-10-30 — Fase 5, orquestrador e agentes

| Campo | Registro |
|---|---|
| Solicitação | Classificar com confiança/justificativa e especializar os três agentes. |
| Proposta da IA | Regras ponderadas; protocolo `OUV-*` como sinal forte; `Decimal` no financeiro; protocolo exato na Ouvidoria; LLM OpenAI-compatible opcional. |
| Problema | T011 (“receitas”) fora de escopo; T007 interpretava “maior” como mês “maio”. |
| Correção | Plurais financeiros e extração de mês com limite de palavra. |
| Decisão | **Aceita com correção.** Pedido de senha (T010) roteado a Informações Internas para recusa, em vez de `fora_do_escopo`, porque o contrato da API tem quatro categorias. |
| Validação | 12/12 classificações no domínio esperado; cálculos T006/T007/T011 conferidos; OUV-9999, status e OUV-0002 conferidos. Sem chamada a provider real. |

### S09 — 2026-10-30 — Fase 6, contrato HTTP

| Campo | Registro |
|---|---|
| Solicitação | Publicar `/api/v1` com rastreabilidade. |
| Proposta da IA | Chat com UUID, fontes, latência; log JSON sem texto da pergunta; reindex desligado em produção. |
| Problema | Import eager de `httpx` derrubava o modo local. |
| Correção | Importação preguiçosa do provider. |
| Decisão | **Aceita com alteração.** |
| Validação | OpenAPI: `/health`, `/api/v1/agents`, `/api/v1/chat`, `/api/v1/knowledge/reindex`. |

### S10 — 2026-10-30 — Fase 7, frontend

| Campo | Registro |
|---|---|
| Solicitação | Interface simples exibindo metadados da resposta. |
| Proposta da IA | HTML/CSS/JS na mesma origem; `textContent` para conteúdo da API; histórico só em memória. |
| Decisão | **Aceita.** Persistência em `localStorage` **descartada** para reduzir retenção de perguntas. |
| Validação | `node --check frontend/app.js` com código de saída 0. Inspeção visual de navegador ainda não havia ocorrido nesta fase. |

### S11 — 2026-10-30 — Fase 8, Docker

| Campo | Registro |
|---|---|
| Solicitação | Entregar execução em container. |
| Proposta da IA | Usuário não-root, healthcheck HTTP, bases montadas somente leitura, volume de logs, `.dockerignore`. |
| Decisão | **Aceita.** |
| Validação nesta data | Compose parseado com PyYAML. `docker` ainda não estava disponível no ambiente de desenvolvimento do agente. |
| Atualização posterior | Em 2026-10-31 o Docker Desktop executou `desafiotecnico-agente-1` com status healthy. Evidências em `docs/evidencias/`. |

### S12 — 2026-10-30 — Fase 9, testes

| Campo | Registro |
|---|---|
| Solicitação | pytest, cobertura e Ruff, sem dependência de serviço pago. |
| Problema | Sandbox Windows bloqueou `socketpair` do TestClient. |
| Correção | Reexecução autorizada fora do sandbox. |
| Validação | 36 testes passando; cobertura 88%; `ruff check .` e `ruff format --check .` passando. Aviso de depreciação Starlette/AnyIO, sem falha. |

### S13 — 2026-10-30 — Fase 10, documentação e auditoria

| Campo | Registro |
|---|---|
| Solicitação | Alinhar README, limitações e revisão final à evidência real. |
| Proposta da IA | Não afirmar Docker, GitHub ou provider real sem comando correspondente. |
| Decisão | **Aceita.** Loader passou a rejeitar symlink fora da raiz de conhecimento. |
| Validação | Varredura estática sem `.env` real; pytest 36 passed / 88% após o teste de symlink. |

### S14 — 2026-10-31 — Revisão crítica

| Campo | Registro |
|---|---|
| Solicitação | Avaliar a entrega e corrigir falhas relevantes. |
| Achados | Filtro financeiro ignorado (CC100 em 2025 somava todas as despesas); “reembolso de viagem” caía fora de escopo; T012 recuperava política geral em vez do fluxo de incidentes. |
| Proposta da IA | Reescrever filtros/períodos/indicadores; desempate por intenção; reforço de título no BM25. |
| Descarte | Reforço de título com peso constante. Motivo: piorou T001 ao promover seção irrelevante. Substituído por reforço ponderado por IDF, incluindo FAQ. |
| Decisão | **Aceita com iteração** após o descarte acima. |
| Validação | Recálculo independente (CC100, Viagens, execução de Tecnologia 28,4%); avaliador 12/12 roteamentos e 12/12 fontes. |

### S15 — 2026-10-31 — Empacotamento da entrega

| Campo | Registro |
|---|---|
| Solicitação | Tratar o Docker como validado (prints em `docs/evidencias`), profissionalizar este registro e publicar em `https://github.com/Rafaeldeoliveira87/Desafio-tecnico-areco.git`. |
| Proposta da IA | Reescrever os MDs de processo; atualizar README/revisão final; criar repositório Git apenas nesta pasta (isolado do repositório da home) e enviar ao GitHub informado. |
| Decisão | **Aceita.** |
| Validação | Git próprio nesta pasta; push de `main` para o repositório informado (commit inicial `597f2b4`). Docker Desktop: container `desafiotecnico-agente-1` healthy. |
| Observação de ambiente | O Git da home (`C:\Users\rafag`, remote Automanager) não recebeu este código. |

## Sugestões da IA por destino

| Destino | Exemplos |
|---|---|
| Aceitas | Modo local sem chave; `Decimal`; protocolo exato; BM25 com filtro de domínio; CORS restritivo; log sem pergunta literal; Docker não-root. |
| Aceitas com alteração | Health síncrono; ingestão como módulo; import preguiçoso do provider; recusa de senha via agente interno; reforço BM25 com IDF. |
| Descartadas | Provider obrigatório; SQL gerado por modelo; embeddings nesta versão; log com texto integral da pergunta; reforço de título com peso constante. |

## Limitações deste registro

A ferramenta não disponibilizou exportação oficial completa de todas as sessões. Este arquivo, junto de `DEVELOPMENT_LOG.md`, é o histórico estruturado entregue no lugar da transcrição literal. Nenhuma credencial foi copiada para o repositório.
