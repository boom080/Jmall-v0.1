from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_product_copy_generate_returns_workflow_payload():
    response = client.post(
        "/api/product-copy/generate",
        json={
            "title": "轻薄羽绒服",
            "category": "服饰",
            "sellingPoints": ["轻量保暖"],
            "tone": "marketing",
            "knowledgeBaseId": "kb-missing",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "mock-product-copy-v1"
    assert payload["response_source"] == "no_rag_fallback"
    assert payload["usedChunks"] == []


def test_mock_product_copy_returns_predictable_payload():
    response = client.post(
        "/api/mock/product-copy",
        json={
            "title": "轻薄羽绒服",
            "category": "服饰",
            "sellingPoints": ["轻量保暖", "城市通勤", "冬季搭配"],
            "tone": "marketing",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "mock-product-copy-v1"
    assert payload["mock"] is True
    assert payload["success"] is True
    assert payload["message"] == "商品文案生成成功（Mock/LangGraph）"
    assert payload["generatedTitle"] == "爆款推荐 | 轻薄羽绒服 | 服饰"
    assert payload["highlights"] == ["轻量保暖", "城市通勤", "冬季搭配"]
    assert "轻薄羽绒服主打轻量保暖、城市通勤、冬季搭配" in payload["summary"]
    assert "知识库" in payload["summary"]


def test_mock_product_copy_rejects_invalid_tone():
    response = client.post(
        "/api/mock/product-copy",
        json={
            "title": "轻薄羽绒服",
            "category": "服饰",
            "sellingPoints": ["轻量保暖"],
            "tone": "aggressive",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["detail"][0]["loc"][-1] == "tone"


def test_mock_product_copy_supports_model_and_knowledge_base_selection():
    response = client.post(
        "/api/mock/product-copy",
        json={
            "title": "静音破壁机",
            "category": "厨房电器",
            "sellingPoints": ["低噪音", "一键清洗"],
            "tone": "warm",
            "modelProvider": "mock",
            "modelName": "mock-product-copy-v1",
            "knowledgeBaseId": "kb-missing",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "mock-product-copy-v1"
    assert payload["response_source"] == "no_rag_fallback"
    assert payload["usedChunks"] == []
