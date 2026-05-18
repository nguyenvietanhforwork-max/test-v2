# Atlas watcher — file-system observer feeding the Redis Stream.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PYTHONPATH=/workspace

WORKDIR /workspace

COPY packages/automation/pyproject.toml /workspace/packages/automation/pyproject.toml

RUN pip install --upgrade pip && \
    pip install watchdog==4.0.2 redis==5.0.8 structlog==24.4.0 \
                python-frontmatter==1.1.0

COPY packages /workspace/packages

CMD ["python", "-m", "packages.automation.watcher.observer"]
