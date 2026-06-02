from app.core.config import Settings
from app.services.chunking_service import ChunkingService


def test_long_chinese_text_splits_into_multiple_chunks_with_indexes():
    settings = Settings(rag_chunk_size=120, rag_chunk_overlap=20, _env_file=None)
    service = ChunkingService(settings)
    text = "\n\n".join([f"第{i}段：这是一段用于测试中文切分的内容，强调商品卖点、使用场景和合规表达。" for i in range(12)])

    chunks = service.chunk_text(text, source_filename="demo.txt", document_title="中文资料", source_type="txt")

    assert len(chunks) > 1
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    assert all(chunk.content.strip() for chunk in chunks)
    assert all(chunk.metadata["source_filename"] == "demo.txt" for chunk in chunks)


def test_overlap_for_long_paragraph_keeps_content_continuity():
    settings = Settings(rag_chunk_size=20, rag_chunk_overlap=5, _env_file=None)
    service = ChunkingService(settings)
    text = "一二三四五六七八九十" * 6

    chunks = service.chunk_text(text, source_filename="long.txt", document_title="长段落", source_type="txt")

    assert len(chunks) > 1
    assert chunks[0].content[-5:] == chunks[1].content[:5]
