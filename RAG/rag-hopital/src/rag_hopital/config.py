from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root: ~/formation/RAG/rag-hopital
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Connection settings, read from the .env file."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env"
    )

    # PostgreSQL
    postgres_url: str
    postgres_password: str

    # Servers
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    embeddings_url: str = "http://localhost:8001/v1"
    rerank_url: str = "http://localhost:8002/rerank"
    llm_url: str = "http://localhost:8000/v1"

    # Models
    embedder_path: str

    # Paths
    corpus_path: Path = PROJECT_ROOT / "data" / "hopital"


settings = Settings()