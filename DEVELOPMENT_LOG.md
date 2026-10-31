# Registro de desenvolvimento

Cronologia das fases do desafio de Analista de IA (Areco). Atualizado ao longo do trabalho, não apenas ao final.

Cada fase registra objetivo, arquivos, validação realmente executada e pendências. Afirmações de teste, build ou cobertura só aparecem quando o comando correspondente foi rodado.

Ferramentas de IA: ver `docs/AI_INTERACTIONS.md`. Decisões de arquitetura: ver `docs/DECISIONS.md`.

---

## Fase 1 — Descoberta (2026-10-29 / 2026-10-30)

**Objetivo.** Inventariar as bases sintéticas, mapear domínios e definir riscos antes de reescrever o código.

**Arquivos.** `AGENTS.md`, `docs/AI_INTERACTIONS.md`, este log. Bases originais não foram alteradas.

**Validação.** Inspeção de manifesto, dicionário, CSV, JSON, Markdown e `testes/perguntas_avaliacao.json`. Contagens: 300 lançamentos, 144 linhas de orçamento, 180 manifestações, 10 políticas, 7 FAQs, 12 casos de avaliação.

**Resultado.** Mapeamento Financeiro / Informações internas / Ouvidoria confirmado. Período financeiro 2025-01-01 a 2026-12-28.

**Pendência à época.** API ainda era `/api/chat`, sem versão, confiança, execution ID nem testes.

---

## Fase 2 — Arquitetura (2026-10-30)

**Objetivo.** Congelar o fluxo e as fronteiras.

**Arquivos.** `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`.

**Validação.** Revisão documental. Sem teste de código.

**Resultado.** ADRs: originais imutáveis; agregações com `Decimal`; BM25 local; LLM opcional; log sem pergunta literal; API versionada.

---

## Fase 3 — Estrutura da aplicação (2026-10-30)

**Objetivo.** Configuração, schemas, logging e health.

**Arquivos.** `app/core/*`, `app/models/schemas.py`, `app/main.py`, `requirements-dev.txt`.

**Problema.** TestClient exigia `httpx`; health async gerou aviso sem event loop.

**Correção.** Health síncrono; HTTPX/pytest/Ruff declarados em desenvolvimento.

**Validação.** Import OK; `/health` → `{status: ok, version: 1.0.0}`; path presente no OpenAPI.

---

## Fase 4 — Ingestão e recuperação (2026-10-30)

**Objetivo.** Indexar Informações Internas com artefato reconstruível.

**Arquivos.** `app/knowledge/*`, `scripts/ingest.py`.

**Problemas.** `python scripts/ingest.py` não encontrava o pacote `app`. BM25 sem normalização de plural invertia ranking de compras vs. acessos.

**Correção.** `python -m scripts.ingest`; redução simples de plurais.

**Validação.** 11 fontes, 22 chunks; filtro de domínio `ouvidoria` retornou zero documentos internos.

---

## Fase 5 — Orquestrador e agentes (2026-10-30)

**Objetivo.** Classificar e despachar para três especialistas.

**Arquivos.** `app/services/classifier.py`, `finance.py`, `ombudsman.py`; `app/agents/*`; `app/llm/*`.

**Problemas.** Plural “receitas” fora de escopo; substring “maio” dentro de “maior”.

**Correção.** Termos no plural e extração de mês com limite de palavra.

**Validação.** 12 casos no domínio esperado; T007 = janeiro de 2026; T011 = receitas de 2025; OUV-9999 não encontrado; OUV-0002 com status exato.

---

## Fase 6 — API versionada (2026-10-30)

**Objetivo.** Contrato HTTP rastreável.

**Arquivos.** `app/agents/orchestrator.py`, `app/api/routes/*`, `app/main.py`.

**Problema.** Import eager de `httpx` quebrava o modo local.

**Correção.** Factory com import preguiçoso.

**Validação.** OpenAPI com `/health`, `/api/v1/agents`, `/api/v1/chat`, `/api/v1/knowledge/reindex`.

---

## Fase 7 — Frontend (2026-10-30)

**Objetivo.** Interface demonstrativa sem framework.

**Arquivos.** `frontend/index.html`, `styles.css`, `app.js`.

**Validação.** `node --check frontend/app.js` (exit 0). Sem E2E de navegador nesta fase.

---

## Fase 8 — Docker (2026-10-30, evidência em 2026-10-31)

**Objetivo.** Execução reproduzível em container.

**Arquivos.** `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.env.example`.

**Validação em 2026-10-30.** YAML válido; Docker CLI ainda indisponível para o agente.

**Validação em 2026-10-31.** Docker Desktop 29.9.2. Container `desafiotecnico-agente-1`, imagem `desafiotecnico-agente`, porta `8000`, status **healthy**. Prints: `docs/evidencias/docker-healthy.png`, `swagger-health-executado.png`, `swagger-chat-executado.png`. Log sanitizado: `docs/evidencias/interactions_docker.jsonl`.

---

## Fase 9 — Testes (2026-10-30)

**Objetivo.** pytest e Ruff sem rede/serviço pago.

**Arquivos.** `tests/*`, `pyproject.toml`, `docs/TESTING.md`.

**Problema.** Sandbox Windows bloqueou `socketpair` do TestClient.

**Validação (execução autorizada).** `python -m pytest -q` → 36 passed; unitários 28 passed / 8 deselected; cobertura 88%; `ruff check .` e `ruff format --check .` OK.

---

## Fase 10 — Documentação e auditoria (2026-10-30)

**Objetivo.** Alinhar README e revisão final às evidências.

**Arquivos.** `README.md`, `docs/LIMITATIONS.md`, `FINAL_REVIEW.md`, `.gitignore`.

**Validação.** Teste de rejeição de symlink fora da raiz de conhecimento; 36 passed / 88%; ausência de `.env` versionado.

**Pendência à época.** GitHub e exportação literal da conversa.

---

## Fase 11 — Revisão crítica (2026-10-31)

**Objetivo.** Corrigir falhas que alteravam o significado da resposta.

**Arquivos.** `app/services/finance.py`, `classifier.py`, `app/knowledge/retrieval.py`, `app/agents/internal_information.py`, `scripts/evaluate.py`, `tests/test_finance_filters.py`, `.github/workflows/ci.yml`.

**Problemas.** Centro de custo ignorado; pergunta mista de reembolso fora de escopo; T012 com fonte errada.

**Descarte.** Reforço de título com peso constante (regrediu T001).

**Validação.** Recálculo independente em Python; `python -m scripts.evaluate` → 12/12 roteamentos e 12/12 fontes (`docs/evidencias/evaluation_report.md`).

---

## Fase 12 — Entrega no GitHub (2026-10-31)

**Objetivo.** Profissionalizar o registro de IA, refletir o Docker validado e publicar o código em repositório próprio.

**Arquivos.** `docs/AI_INTERACTIONS.md`, `DEVELOPMENT_LOG.md`, `README.md`, `FINAL_REVIEW.md`, `docs/LIMITATIONS.md`, `docs/TESTING.md`.

**Método de validação.** Conferir evidências em `docs/evidencias/`; `docker ps` com status healthy; inicializar Git **somente** nesta pasta; enviar para `https://github.com/Rafaeldeoliveira87/Desafio-tecnico-areco.git`.

**Risco evitado.** Não commitar o desafio no repositório Git da home (`C:\Users\rafag`, remote Automanager).
