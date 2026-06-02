from app.core.config import Settings
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.knowledge_base_service import KnowledgeBaseService


def build_service(tmp_path) -> KnowledgeBaseService:
    settings = Settings(
        merchant_ai_data_file=str(tmp_path / "merchant_ai_store.json"),
        rag_chunk_size=60,
        rag_chunk_overlap=10,
        _env_file=None,
    )
    return KnowledgeBaseService(
        KnowledgeBaseRepository(settings),
        EmbeddingService(settings),
        ChunkingService(settings),
    )


def test_upload_txt_creates_knowledge_base_document_and_chunks(tmp_path):
    service = build_service(tmp_path)

    result = service.upload_txt_create_knowledge_base(
        "中文商品知识库",
        "用于中文测试",
        "phone.txt",
        "Jrun X1 主打长续航。\n\n适合通勤和轻办公，注意避免绝对化用语。".encode("utf-8"),
    )
    summaries = service.list_knowledge_bases()
    documents = service.list_documents(result.knowledgeBaseId)

    assert result.knowledgeBaseId.startswith("kb-")
    assert result.documentId.startswith("doc-")
    assert result.chunkCount >= 1
    assert summaries[0].label == "中文商品知识库"
    assert documents[0].title == "phone.txt"
    assert "长续航" in documents[0].contentPreview


def test_content_hash_prevents_duplicate_documents(tmp_path):
    service = build_service(tmp_path)
    created = service.create_knowledge_base("重复测试", "")
    text = "同一份中文资料不会重复创建文档。"

    first = service.import_text_document(created.id, "doc.txt", text, source_type="txt", source_filename="doc.txt")
    second = service.import_text_document(created.id, "doc.txt", text, source_type="txt", source_filename="doc.txt")

    assert first.id == second.id
    assert len(service.list_documents(created.id)) == 1


def test_upload_txt_rejects_non_utf8_bytes(tmp_path):
    service = build_service(tmp_path)

    try:
        service.upload_txt_create_knowledge_base("乱码测试", "", "bad.txt", b"\xff\xfe\x00")
    except ValueError as exc:
        assert "UTF-8" in str(exc)
    else:
        raise AssertionError("expected UTF-8 validation error")
