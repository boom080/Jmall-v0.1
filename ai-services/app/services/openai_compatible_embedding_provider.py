from typing import List

import httpx


class OpenAICompatibleEmbeddingProvider:
    provider_name = "openai-compatible"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: int = 30,
        dimension: int = 0,
    ) -> None:
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key or ""
        self.model = model or ""
        self.timeout_seconds = timeout_seconds
        self.dimension = max(0, int(dimension or 0))

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key.strip():
            raise RuntimeError("RAG_EMBEDDING_API_KEY 未配置，无法调用真实 embedding provider")
        if not self.base_url:
            raise RuntimeError("RAG_EMBEDDING_BASE_URL 未配置，无法调用真实 embedding provider")
        if not self.model:
            raise RuntimeError("RAG_EMBEDDING_MODEL 未配置，无法调用真实 embedding provider")

        body = {"model": self.model, "input": texts}
        if self.dimension > 0:
            body["dimensions"] = self.dimension

        response = httpx.post(
            f"{self.base_url}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key.strip()}"},
            json=body,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") or []
        sorted_data = sorted(data, key=lambda item: int(item.get("index", 0)))
        embeddings = [item.get("embedding") or [] for item in sorted_data]
        if len(embeddings) != len(texts):
            raise RuntimeError("embedding provider 返回数量与输入文本数量不一致")
        return embeddings
