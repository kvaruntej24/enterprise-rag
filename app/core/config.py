from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://rag:rag@localhost:5432/rag"
    llm_api_key: str = ""
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    chunk_size: int = 1000
    chunk_overlap: int = 150
    embedding_dim: int = 384
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "openai/gpt-oss-120b"
    llm_timeout_seconds: float = 30.0
    llm_max_tokens: int = 700
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"


settings = Settings()