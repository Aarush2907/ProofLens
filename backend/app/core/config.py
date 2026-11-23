from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> repository root is three levels up.
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime configuration loaded from the environment and the root .env file.

    Environment variables win over the file, which is what lets tests point at
    a temporary database without editing a developer's local .env.
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ProofLens"
    app_version: str = "0.5.0"
    environment: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    database_url: str = (
        "postgresql+psycopg://prooflens:prooflens@localhost:5432/prooflens"
    )
    openai_api_key: str = ""
    # When true, a run only uses keys sent by the visitor. The keys above are ignored.
    require_user_keys: bool = False
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = ""
    openai_timeout_seconds: float = 40
    # Approximate published prices for gpt-4o-mini, in USD per million tokens.
    # They are an estimate for the cost cap, not a provider invoice.
    prompt_price_per_million: float = 0.15
    completion_price_per_million: float = 0.60
    max_run_cost_usd: float = 1.0
    max_concurrent_runs: int = 3
    max_run_starts: int = 40
    run_start_window_seconds: int = 600
    qdrant_health_timeout_seconds: float = 2
    search_provider: str = "tavily"
    search_api_key: str = ""
    agent_max_attempts: int = 2
    max_sources: int = 5
    max_search_results: int = 5
    max_claims: int = 8
    graph_recursion_limit: int = 25
    source_content_chars: int = 4000
    # Embedding settings are separate from the chat model. A live run uses
    # fastembed. Tests set EMBEDDING_PROVIDER=hash so they do not download a model.
    embedding_provider: str = "fastembed"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    qdrant_url: str = ""
    qdrant_path: str = ""
    qdrant_collection: str = "prooflens_evidence"
    mcp_tool_timeout_seconds: float = 45
    memory_fresh_days: int = 14
    retrieval_min_score: float = 0.2
    memory_min_score: float = 0.35
    chunk_size: int = 700
    chunk_overlap: int = 80

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
