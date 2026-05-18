from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    vault_path: str = "/data/vault"
    vault_raw_dir: str = "raw"
    vault_archive_dir: str = "raw/old news"
    api_base_url: str = "http://api:8000"
    redis_url: str = "redis://redis:6379/0"


settings = Settings()
