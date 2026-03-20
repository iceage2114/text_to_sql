from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_key: str
    openai_base_url: str = "https://models.inference.ai.azure.com"
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o"
    mssql_conn_str: str
    chroma_path: str = "./chroma_data"
    row_limit: int = 500
    max_retries: int = 3
    critic_threshold: float = 0.6
    tool_timeout_seconds: int = 10
    retrospective_failure_limit: int = 100


settings = Settings()
