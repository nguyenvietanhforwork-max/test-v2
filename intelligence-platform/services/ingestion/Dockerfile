FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e .
COPY . .
CMD ["python", "-m", "ingestion.main"]
