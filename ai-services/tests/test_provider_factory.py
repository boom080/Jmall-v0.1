from app.core.config import Settings
from app.providers.factory import ProviderFactory


def test_provider_factory_lists_mock_only_without_remote_keys():
    factory = ProviderFactory(Settings(_env_file=None))
    models = factory.list_available_models()

    ids = [item.id for item in models]
    assert ids == ["mock:mock-product-copy-v1"]


def test_provider_factory_lists_key_backed_remote_models():
    settings = Settings(deepseek_api_key="sk-deepseek", qwen_api_key="sk-qwen", _env_file=None)
    factory = ProviderFactory(settings)
    models = factory.list_available_models()

    assert any(item.provider == "deepseek" for item in models)
    assert any(item.provider == "qwen" for item in models)


def test_provider_factory_returns_mock_provider_by_default():
    settings = Settings(ai_provider="mock", _env_file=None)
    factory = ProviderFactory(settings)
    provider = factory.get_product_copy_provider("mock")

    assert provider.provider_name == "mock"
    assert provider.mock is True
