import hashlib
from typing import List


class MockEmbeddingProvider:
    provider_name = "mock-embedding"

    def __init__(self, dimension: int = 8) -> None:
        self.dimension = max(1, dimension)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_text(text) for text in texts]

    def _embed_text(self, text: str) -> List[float]:
        values: List[float] = []
        seed = text.encode("utf-8")
        counter = 0
        while len(values) < self.dimension:
            digest = hashlib.sha256(seed + counter.to_bytes(4, byteorder="big")).digest()
            for index in range(0, len(digest), 4):
                if len(values) >= self.dimension:
                    break
                chunk = digest[index:index + 4]
                integer = int.from_bytes(chunk, byteorder="big", signed=False)
                values.append(round(((integer % 2000) / 1000.0) - 1.0, 6))
            counter += 1
        return values
