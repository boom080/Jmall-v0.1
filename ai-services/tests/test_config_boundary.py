from app.core.config import Settings


def test_ai_service_defaults_to_postgresql_and_redis_boundary():
    settings = Settings(_env_file=None)

    assert settings.database_engine == "postgresql"
    assert settings.merchant_schema == "jrunmall_merchant_ai"
    assert settings.redis_url == ""


def test_ai_service_accepts_local_postgresql_database_url():
    settings = Settings(database_url="postgresql://jrunmall:secret@127.0.0.1:5432/jrunmall_merchant", _env_file=None)

    assert settings.database_url.startswith("postgresql://")


def test_ai_service_accepts_jrunmall_ai_key_alias(monkeypatch):
    monkeypatch.setenv("JRUNMALL_AI_DEEPSEEK_API_KEY", "sk-test")

    settings = Settings(_env_file=None)

    assert settings.deepseek_api_key == "sk-test"


def test_ai_service_accepts_dashscope_qwen_key_alias(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-qwen-test")

    settings = Settings(_env_file=None)

    assert settings.qwen_api_key == "sk-qwen-test"
