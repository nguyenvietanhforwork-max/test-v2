# Atlas worker — runs Celery + LangGraph pipeline.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PYTHONPATH=/workspace:/workspace/apps/api

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

COPY . /workspace/

# Install api + agents + automation after source is present so local packages resolve.
RUN pip install --upgrade pip && \
    pip install /workspace/apps/api /workspace/packages/agents /workspace/packages/automation

CMD ["celery", "-A", "packages.automation.worker.app", "worker", "--loglevel=info", "--concurrency=4"]
