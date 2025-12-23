"""
Application configuration powered by Pydantic Settings.
"""

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application configuration."""

    api_prefix: str = "/api"
    app_name: str = "TARA Backend"
    environment: str = Field(default="local", pattern="^(local|dev|staging|prod)$")

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")
    pg_pool_min_size: int = 5  # Increased for better connection availability
    pg_pool_max_size: int = 20  # Increased for better concurrency

    # OpenAI / OpenRouter
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    # openai_model: str = "gpt-4o-mini"  # Fixed: was "gpt-4.1" which doesn't exist
    openai_model: str = "google/gemini-3-flash-preview"
    # openai_model: str = "google/gemini-3-flash-preview"
    openai_embedding_model: str = "text-embedding-3-large"
    openai_timeout_seconds: int = 60  # Increased for RAG operations
    
    # OpenRouter (for Gemini and other models)
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    use_openrouter: bool = Field(default=True, alias="USE_OPENROUTER")  # Default to True to use OpenRouter
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Retrieval
    max_retrieval_chunks: int = 25  # Reduced from 12 for faster retrieval
    min_similarity_score: float = 0.3  # Lowered from 0.3 for better matching
    min_similarity_score_chat: float = 0.3  # Lowered for faster retrieval
    ivfflat_probes: int = 1  # Reduced from 10 to 1 for maximum speed (accuracy tradeoff acceptable)

    # Specialty agents
    specialty_agents: List[str] = ["Cardiology", "Endocrinology", "Nephrology"]

    # CORS
    cors_origins: List[AnyHttpUrl] = Field(
        default_factory=lambda: [
            AnyHttpUrl("http://localhost:8080"),
            AnyHttpUrl("http://127.0.0.1:8080"),
        ]
    )

    # Observability
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()  # type: ignore[call-arg]

