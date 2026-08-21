from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Jrunmall AI Service"
    app_version: str = "0.2.0"
    app_env: str = Field("local", env="AI_SERVICE_ENV")
    host: str = Field("127.0.0.1", env="AI_SERVICE_HOST")
    port: int = Field(18080, env="AI_SERVICE_PORT")
    api_prefix: str = Field("/api", env="AI_SERVICE_API_PREFIX")
    log_level: str = Field("INFO", env="AI_SERVICE_LOG_LEVEL")
    mock_provider: str = Field("mock-product-copy-v1", env="AI_SERVICE_PROVIDER")
    ai_provider: str = Field("mock", env="AI_PROVIDER")
    ai_model_name: str = Field("mock-product-copy-v1", env="AI_MODEL_NAME")
    ai_fallback_provider: str = Field("mock", env="AI_FALLBACK_PROVIDER")
    ai_timeout_seconds: int = Field(30, env="AI_TIMEOUT_SECONDS")
    ai_rag_enabled: bool = Field(True, env="AI_RAG_ENABLED")
    ai_rag_top_k: int = Field(4, env="AI_RAG_TOP_K")
    ai_rag_cache_ttl_seconds: int = Field(300, env="AI_RAG_CACHE_TTL_SECONDS")
    rag_embedding_provider: str = Field(
        "",
        validation_alias=AliasChoices("RAG_EMBEDDING_PROVIDER", "rag_embedding_provider"),
    )
    rag_embedding_base_url: str = Field(
        "",
        validation_alias=AliasChoices("RAG_EMBEDDING_BASE_URL", "rag_embedding_base_url"),
    )
    rag_embedding_api_key: str = Field(
        "",
        validation_alias=AliasChoices("RAG_EMBEDDING_API_KEY", "rag_embedding_api_key"),
    )
    rag_embedding_model: str = Field(
        "",
        validation_alias=AliasChoices("RAG_EMBEDDING_MODEL", "rag_embedding_model"),
    )
    rag_embedding_dimension: str = Field(
        "",
        validation_alias=AliasChoices("RAG_EMBEDDING_DIMENSION", "rag_embedding_dimension"),
    )
    rag_chunk_size: int = Field(
        800,
        validation_alias=AliasChoices("RAG_CHUNK_SIZE", "rag_chunk_size"),
    )
    rag_chunk_overlap: int = Field(
        120,
        validation_alias=AliasChoices("RAG_CHUNK_OVERLAP", "rag_chunk_overlap"),
    )
    rag_top_k: int = Field(
        5,
        validation_alias=AliasChoices("RAG_TOP_K", "AI_RAG_TOP_K", "rag_top_k"),
    )
    rag_min_score: float = Field(
        0.0,
        validation_alias=AliasChoices("RAG_MIN_SCORE", "rag_min_score"),
    )
    deepseek_api_key: str = Field(
        "",
        validation_alias=AliasChoices(
            "deepseek_api_key",
            "DEEPSEEK_API_KEY",
            "JRUNMALL_AI_DEEPSEEK_API_KEY",
            "GULIMALL_AI_DEEPSEEK_API_KEY",
        ),
    )
    deepseek_base_url: str = Field(
        "https://api.deepseek.com",
        validation_alias=AliasChoices("DEEPSEEK_BASE_URL", "JRUNMALL_AI_DEEPSEEK_BASE_URL", "GULIMALL_AI_DEEPSEEK_BASE_URL"),
    )
    deepseek_model: str = Field(
        "deepseek-chat",
        validation_alias=AliasChoices("DEEPSEEK_MODEL", "JRUNMALL_AI_DEEPSEEK_MODEL", "GULIMALL_AI_DEEPSEEK_MODEL"),
    )
    qwen_api_key: str = Field(
        "",
        validation_alias=AliasChoices(
            "qwen_api_key",
            "QWEN_API_KEY",
            "JRUNMALL_AI_QWEN_API_KEY",
            "GULIMALL_AI_QWEN_API_KEY",
            "DASHSCOPE_API_KEY",
            "ALIYUN_API_KEY",
            "ALIBABA_CLOUD_API_KEY",
        ),
    )
    qwen_base_url: str = Field(
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
        validation_alias=AliasChoices("QWEN_BASE_URL", "JRUNMALL_AI_QWEN_BASE_URL", "GULIMALL_AI_QWEN_BASE_URL"),
    )
    qwen_chat_model: str = Field(
        "qwen-plus",
        validation_alias=AliasChoices("QWEN_CHAT_MODEL", "JRUNMALL_AI_QWEN_MODEL", "GULIMALL_AI_QWEN_MODEL"),
    )
    qwen_embedding_model: str = Field(
        "text-embedding-v4",
        validation_alias=AliasChoices(
            "QWEN_EMBEDDING_MODEL",
            "JRUNMALL_AI_QWEN_EMBEDDING_MODEL",
            "GULIMALL_AI_QWEN_EMBEDDING_MODEL",
        ),
    )
    redis_url: str = Field("", env="REDIS_URL")
    database_url: str = Field("", env="DATABASE_URL")
    database_engine: str = Field("postgresql", env="DATABASE_ENGINE")
    merchant_schema: str = Field("jmall_rag", env="MERCHANT_AI_SCHEMA")
    merchant_ai_data_file: str = Field(
        "data/merchant_ai_store.json",
        env="MERCHANT_AI_DATA_FILE",
    )
    # --- Agent orchestration settings ---
    tavily_api_key: str = Field(
        "",
        validation_alias=AliasChoices("TAVILY_API_KEY", "tavily_api_key"),
    )
    agent_default_provider: str = Field("", env="AGENT_DEFAULT_PROVIDER")
    # Per-tier provider overrides — when empty, fall back to agent_default_provider / ai_provider
    agent_strong_provider: str = Field("", env="AGENT_STRONG_PROVIDER")
    agent_medium_provider: str = Field("", env="AGENT_MEDIUM_PROVIDER")
    agent_cheap_provider: str = Field("", env="AGENT_CHEAP_PROVIDER")
    # Per-tier model overrides
    # Empty means choose from provider-aware tier defaults. A global default
    # such as qwen-plus is invalid when the selected provider is DeepSeek.
    agent_strong_model: str = Field("", env="AGENT_STRONG_MODEL")
    agent_medium_model: str = Field("", env="AGENT_MEDIUM_MODEL")
    agent_cheap_model: str = Field("", env="AGENT_CHEAP_MODEL")
    agent_cost_budget_daily: float = Field(5.0, env="AGENT_COST_BUDGET_DAILY")
    cost_tracking_enabled: bool = Field(True, env="COST_TRACKING_ENABLED")

    def resolved_embedding_dimension(self) -> int:
        raw = (self.rag_embedding_dimension or "").strip()
        if not raw:
            return 8
        try:
            value = int(raw)
        except ValueError:
            return 8
        return value if value > 0 else 8

    model_config = SettingsConfigDict(
        env_file=("../.env.local", ".env.local", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
