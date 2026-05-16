from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    api_base_url: str = "http://api:8000"
    pdf_engine_url: str = "http://pdf-engine:4000"
    classification_model: str = "claude-haiku-4-5-20251001"
    summarization_model: str = "claude-sonnet-4-6"
    report_model: str = "claude-opus-4-6"
    embedding_model: str = "text-embedding-3-large"
    embedding_dimensions: int = 1536


settings = Settings()
