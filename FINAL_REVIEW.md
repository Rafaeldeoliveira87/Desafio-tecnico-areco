# Revisão final — Agente de Conhecimento Areco

Entrega do desafio de Analista de IA. Repositório: [https://github.com/Rafaeldeoliveira87/Desafio-tecnico-areco](https://github.com/Rafaeldeoliveira87/Desafio-tecnico-areco).

## Checklist do enunciado

| Item pedido | Situação |
|---|---|
| 1. Link do repositório GitHub | `https://github.com/Rafaeldeoliveira87/Desafio-tecnico-areco` |
| 2. Execução via Docker, com instruções | `Dockerfile`, `docker-compose.yml`, `.env.example`; README com passo a passo. Container validado como **healthy** |
| 3. Frontend funcional | HTML/CSS/JS em `frontend/`, servido na mesma origem |
| 4. Orquestrador e agentes especializados | Financeiro, Informações internas e Ouvidoria, com classificação e confiança |
| 5. Scripts/bases de conhecimento | Pastas originais + `python -m scripts.ingest` |
| 6. Logs de interações com o agente | `docs/evidencias/interactions_docker.jsonl` (sem texto literal da pergunta) |
| 7. `AGENTS.md` e registro do processo | `AGENTS.md`, `DEVELOPMENT_LOG.md` |
| 8. Histórico das conversas com IA | `docs/AI_INTERACTIONS.md` (registro estruturado; a ferramenta não exporta transcrição integral) |
| 9. Documentação de arquitetura, decisões, limitações e testes | `docs/ARCHITECTURE.md`, `DECISIONS.md`, `LIMITATIONS.md`, `TESTING.md` |
| 10. Prazo | Desenvolvimento entre 29 e 31 de outubro de 2026 |

## Requisitos concluídos

- Inventário das bases e mapeamento dos três domínios.
- `AGENTS.md`, `DEVELOPMENT_LOG.md` e `docs/AI_INTERACTIONS.md` atualizados durante o trabalho.
- API FastAPI/Pydantic versionada, catálogo de agentes e health check.
- Orquestrador com categorias normalizadas, justificativa, confidence score heurístico e esclarecimento de baixa confiança.
- Especialistas com fontes: Financeiro determinístico com `Decimal`, Interno com BM25 e Ouvidoria com protocolo exato.
- Índice reconstruível; originais preservados.
- Provider OpenAI-compatible opcional, desabilitado por padrão.
- UI com metadados, loading, erros, fontes e histórico em memória.
- Logging JSON com execution ID, hash da pergunta (sem texto), domínio, confiança, agente, fontes, latência e status.
- Docker não-root, healthcheck, Compose, evidências de execução healthy.
- README, ADRs, limitações e testes documentados.

## Requisitos parciais

- **Provider externo:** cliente e fallback testados com mocks. Nenhuma chamada real a serviço pago.
- **RAG:** BM25 local, não embeddings. Limitações de sinônimo documentadas.
- **T010:** recusa credenciais via `informacoes_internas`, não via rótulo especial do fixture.
- **Histórico de IA:** registro estruturado contínuo, não exportação binária da ferramenta.

## Testes e evidências

- `python -m pytest -q`: **36 passed** (2026-10-30), aviso de depreciação Starlette/AnyIO.
- Cobertura: **88%** em `app`.
- `ruff check .` e `ruff format --check .`: passaram.
- `python -m scripts.evaluate`: **12/12** roteamentos e **12/12** fontes (`docs/evidencias/evaluation_report.md`).
- Docker Desktop 29.9.2: container `desafiotecnico-agente-1` healthy na porta 8000.
- Prints: `docs/evidencias/docker-healthy.png`, `swagger-health-executado.png`, `swagger-chat-executado.png`.

## Riscos conhecidos

- Confidence score e BM25 são heurísticos.
- Sem autenticação nem rate limiting; não expor publicamente.
- Modo LLM, se habilitado, pode extrapolar trechos; permanece desligado por padrão.

## Como o avaliador sobe o projeto

```bash
git clone https://github.com/Rafaeldeoliveira87/Desafio-tecnico-areco.git
cd Desafio-tecnico-areco
docker compose up --build
```

Abrir http://localhost:8000 e http://localhost:8000/docs. Exemplos: “Como solicito férias?”, “Quanto foi gasto em despesas pagas no período de janeiro a março de 2025?”, “Qual o status do protocolo OUV-0002?”.
