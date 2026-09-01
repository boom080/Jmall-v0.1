from app.core.config import Settings
from app.llm.router import LLMRouter


def test_ai_service_defaults_to_postgresql_and_redis_boundary():
    settings = Settings(database_url="", redis_url="", _env_file=None)

    assert settings.database_engine == "postgresql"
    # Default merchant_schema changed from "jrunmall_merchant_ai" to "jmall_rag"
    assert settings.merchant_schema == "jmall_rag"
    assert settings.redis_url == ""


def test_ai_service_accepts_local_postgresql_database_url():
    settings = Settings(database_url="postgresql://jrunmall:secret@127.0.0.1:5432/jrunmall_merchant", _env_file=None)

    assert settings.database_url.startswith("postgresql://")


def test_ai_service_accepts_jrunmall_ai_key_alias(monkeypatch):
    # Clear any pre-existing env vars that might leak from docker-compose
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("JMALL_DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("JRUNMALL_AI_DEEPSEEK_API_KEY", "sk-test")

    settings = Settings(_env_file=None)

    assert settings.deepseek_api_key == "sk-test"


def test_ai_service_accepts_dashscope_qwen_key_alias(monkeypatch):
    # Clear any pre-existing env vars that might leak from docker-compose
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    monkeypatch.delenv("JMALL_QWEN_API_KEY", raising=False)
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-qwen-test")

    settings = Settings(_env_file=None)

    assert settings.qwen_api_key == "sk-qwen-test"


def test_image_search_accepts_lowercase_picture_base_alias(monkeypatch):
    monkeypatch.delenv("PICTURE_BASE", raising=False)
    monkeypatch.delenv("IMAGE_SEARCH_MODEL", raising=False)
    monkeypatch.setenv("picture_base", "qwen-plus-latest")

    settings = Settings(_env_file=None)

    assert settings.image_search_provider == "qwen"
    assert settings.image_search_model == "qwen-plus-latest"


def test_explicit_mock_provider_never_leaks_to_real_keys():
    settings = Settings(
        ai_provider="mock",
        agent_default_provider="mock",
        qwen_api_key="real-key-present",
        deepseek_api_key="another-real-key-present",
        agent_cheap_model="",
        _env_file=None,
    )

    assert LLMRouter(settings).route("market_research") == ("mock", "mock-product-copy-v1")


def test_empty_model_override_uses_selected_provider_defaults():
    qwen = Settings(
        ai_provider="qwen",
        agent_default_provider="",
        agent_cheap_provider="",
        qwen_api_key="configured",
        agent_cheap_model="",
        _env_file=None,
    )
    deepseek = Settings(
        ai_provider="deepseek",
        agent_default_provider="",
        agent_medium_provider="",
        deepseek_api_key="configured",
        agent_medium_model="",
        _env_file=None,
    )

    assert LLMRouter(qwen).route("market_research") == ("qwen", "qwen-turbo")
    assert LLMRouter(deepseek).route("style_adaptation") == ("deepseek", "deepseek-chat")
