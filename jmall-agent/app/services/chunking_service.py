from dataclasses import dataclass
from typing import Dict, List

from app.core.config import Settings


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    content: str
    char_count: int
    metadata: Dict[str, object]


class ChunkingService:
    def __init__(self, settings: Settings) -> None:
        self.chunk_size = max(1, int(settings.rag_chunk_size or 800))
        self.chunk_overlap = max(0, min(int(settings.rag_chunk_overlap or 0), self.chunk_size - 1))

    def chunk_text(self, content: str, source_filename: str, document_title: str, source_type: str) -> List[TextChunk]:
        normalized = self.clean_text(content)
        if not normalized:
            return []

        raw_chunks: List[str] = []
        current = ""
        for paragraph in self._paragraphs(normalized):
            if len(paragraph) > self.chunk_size:
                if current.strip():
                    raw_chunks.append(current.strip())
                    current = ""
                raw_chunks.extend(self._split_long_text(paragraph))
                continue

            candidate = paragraph if not current else f"{current}\n\n{paragraph}"
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current.strip():
                    raw_chunks.append(current.strip())
                current = paragraph

        if current.strip():
            raw_chunks.append(current.strip())

        chunks: List[TextChunk] = []
        for index, raw in enumerate(item.strip() for item in raw_chunks if item and item.strip()):
            metadata = {
                "source_filename": source_filename,
                "document_title": document_title,
                "chunk_index": index,
                "char_count": len(raw),
                "source_type": source_type,
            }
            chunks.append(
                TextChunk(
                    chunk_index=index,
                    content=raw,
                    char_count=len(raw),
                    metadata=metadata,
                )
            )
        return chunks

    def clean_text(self, content: str) -> str:
        text = (content or "").replace("\ufeff", "")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [" ".join(line.strip().split()) for line in text.split("\n")]
        normalized = "\n".join(lines)
        while "\n\n\n" in normalized:
            normalized = normalized.replace("\n\n\n", "\n\n")
        return normalized.strip()

    def _paragraphs(self, content: str) -> List[str]:
        paragraphs = [item.strip() for item in content.split("\n\n") if item.strip()]
        if len(paragraphs) <= 1:
            paragraphs = [item.strip() for item in content.split("\n") if item.strip()]
        return paragraphs

    def _split_long_text(self, text: str) -> List[str]:
        chunks: List[str] = []
        start = 0
        while start < len(text):
            end = min(len(text), start + self.chunk_size)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(text):
                break
            start = max(end - self.chunk_overlap, start + 1)
        return chunks
