# Estratégia e execução dos testes

## Comandos

Instale dependências de desenvolvimento com `python -m pip install -r requirements-dev.txt`.

```powershell
# Todos os testes (unitários e integração)
python -m pytest -q

# Somente unitários
python -m pytest -q -m "not integration"

# Todos os testes com cobertura
python -m pytest --cov=app --cov-report=term-missing

# Lint e verificação de formatação
ruff check .
ruff format --check .
```

Para aplicar a formatação, use `ruff format .`.

## Cobertura

- Unitários: classificação, evidências e chunking, cálculo financeiro, protocolos da Ouvidoria, provider falso, timeout, resposta inválida e fallback.
- Integração: `/health`, catálogo de agentes, chat, fontes/ID/latência, baixa confiança, fora do escopo, recusa de credenciais, prompt injection, validação de entrada, logs sem pergunta literal e reconstrução do índice.
- Dados usados são as bases sintéticas fornecidas; testes não chamam serviços externos.

## Última execução registrada

- **Data:** 2026-10-30.
- `python -m pytest -q`: **36 passed**, 1 aviso de depreciação de `BlockingPortal` em Starlette/AnyIO.
- `python -m pytest -q -m "not integration"`: **28 passed, 8 deselected**, 1 aviso de depreciação.
- `python -m pytest -q --cov=app --cov-report=term-missing`: **36 passed; cobertura total 88%** incluindo `app/main.py`.
- `ruff check .`: **All checks passed!**
- `ruff format --check .`: **61 files already formatted**.
- A suíte HTTP precisou ser executada fora do sandbox, pois a criação do socketpair do Windows ficou bloqueada no sandbox. A execução autorizada fora dele passou.
- Execução local manual (2026-10-30): Uvicorn em `127.0.0.1:8000`; `GET /health` HTTP 200; pergunta sintética de férias retornou Informações Internas com três fontes.
- Docker (2026-10-31): `docker compose up --build` no Docker Desktop 29.9.2; container `desafiotecnico-agente-1` **healthy** em `0.0.0.0:8000`. Prints em `docs/evidencias/docker-healthy.png`, `swagger-health-executado.png` e `swagger-chat-executado.png`. Interações sanitizadas em `docs/evidencias/interactions_docker.jsonl`.
- Avaliação automática (2026-10-31): `python -m scripts.evaluate` → 12/12 roteamentos e 12/12 fontes (`docs/evidencias/evaluation_report.md`).
