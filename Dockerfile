FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --system --gid 10001 agent \
    && useradd --system --uid 10001 --gid agent --home-dir /app agent
WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=agent:agent app ./app
COPY --chown=agent:agent frontend ./frontend
COPY --chown=agent:agent scripts ./scripts
COPY --chown=agent:agent financeiro ./financeiro
COPY --chown=agent:agent informacoes_internas ./informacoes_internas
COPY --chown=agent:agent ouvidoria ./ouvidoria
RUN mkdir -p /app/data/processed /app/logs \
    && chown -R agent:agent /app/data /app/logs

USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
