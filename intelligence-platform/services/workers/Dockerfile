FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev \
  && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e .
COPY . .
CMD ["celery", "-A", "workers.app", "worker", "-l", "info", "-Q", "ingest,classify,report,pdf,sync"]
