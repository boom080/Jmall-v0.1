from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_models_endpoint_returns_configured_model_entries():
    response = client.get("/api/models")

    assert response.status_code == 200
    payload = response.json()
    ids = [item["id"] for item in payload]
    assert "mock:mock-product-copy-v1" in ids
    assert all(item["provider"] in {"mock", "deepseek", "qwen"} for item in payload)


def test_knowledge_bases_endpoint_returns_valid_list():
    response = client.get("/api/knowledge-bases")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    # Each entry should have required fields with correct types
    for item in payload:
        assert "id" in item
        assert "label" in item
        assert isinstance(item.get("documentCount"), int)
        assert isinstance(item.get("chunkCount"), int)
