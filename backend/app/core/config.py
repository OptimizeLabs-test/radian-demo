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
    # openai_model: str = "gpt-4o-mini" 
    openai_model: str = "google/gemini-3-flash-preview"
    openai_embedding_model: str = "text-embedding-3-large"
    openai_timeout_seconds: int = 60  # Increased for RAG operations
    
    # OpenRouter (for Gemini and other models)
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    use_openrouter: bool = Field(default=True, alias="USE_OPENROUTER")  # Default to True to use OpenRouter
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Retrieval
    max_retrieval_chunks_chat: int = 15  # Maximum chunks to retrieve for chat queries (for accuracy)
    max_retrieval_chunks_summary: int = 8  # Maximum chunks to retrieve for summaries (for speed)
    min_similarity_score: float = 0.3  # Minimum similarity threshold for matching
    min_similarity_score_chat: float = 0.25  # Lower threshold for chat to capture more relevant chunks
    ivfflat_probes: int = 10  # Increased from 1 to 10 for better search accuracy (speed vs accuracy tradeoff)
    
    # Re-ranking (top-n, top-k strategy)
    rerank_enabled: bool = True  # Enable re-ranking
    rerank_top_n: int = 50  # Retrieve top-N chunks before re-ranking (should be > max_retrieval_chunks_chat)
    rerank_top_k: int = 15  # Keep top-K chunks after re-ranking (typically equals max_retrieval_chunks_chat)
    rerank_similarity_weight: float = 0.6  # Weight for semantic similarity in re-ranking score (increased from 0.5)
    rerank_keyword_weight: float = 0.25  # Weight for keyword matching in re-ranking score (decreased from 0.3)
    rerank_recency_weight: float = 0.15  # Weight for recency in re-ranking score (decreased from 0.2)

    # Specialty agents
    specialty_agents: List[str] = ["Cardiology", "Endocrinology", "Nephrology"]

    # CORS
    cors_origins: List[AnyHttpUrl] = Field(
        default_factory=lambda: [
            AnyHttpUrl("http://localhost:8080"),  # Vite dev server (configured in vite.config.ts)
            AnyHttpUrl("http://127.0.0.1:8080"),  # Same as above, using IP address
        ]
    )
    # Set CORS_ALLOW_ALL_ORIGINS=true to allow all origins (NOT RECOMMENDED for production)
    # Default is False for security - only allow specific origins
    cors_allow_all_origins: bool = Field(default=False, alias="CORS_ALLOW_ALL_ORIGINS")
    
    # Additional allowed origins from environment variable (comma-separated)
    # Example: CORS_ADDITIONAL_ORIGINS=https://app.vercel.app,https://custom-domain.com
    cors_additional_origins: str | None = Field(default=None, alias="CORS_ADDITIONAL_ORIGINS")

    # Observability
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()  # type: ignore[call-arg]

