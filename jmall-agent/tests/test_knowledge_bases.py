from app.core.config import Settings
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.knowledge_base_service import KnowledgeBaseService


def build_service(tmp_path) -> KnowledgeBaseService:
    settings = Settings(
        merchant_ai_data_file=str(tmp_path / "merchant_ai_store.json"),
        rag_embedding_provider="mock",
        rag_embedding_api_key="",
        database_url="",
        redis_url="",
        _env_file=None,
    )
    repository = KnowledgeBaseRepository(settings)
    return KnowledgeBaseService(repository, EmbeddingService(settings), ChunkingService(settings))


def test_new_file_store_starts_without_fallback_knowledge_bases(tmp_path):
    service = build_service(tmp_path)

    assert service.list_knowledge_bases() == []


def test_create_knowledge_base(tmp_path):
    service = build_service(tmp_path)

    created = service.create_knowledge_base("服饰知识库", "用于服饰卖点测试")

    assert created.id.startswith("kb-")
    assert created.label == "服饰知识库"
    assert created.embeddingStatus == "empty"
    assert created.source == "manual"


def test_create_knowledge_base_reuses_normalized_duplicate_name(tmp_path):
    service = build_service(tmp_path)

    first = service.create_knowledge_base("家电知识库", "第一版")
    second = service.create_knowledge_base("  家电知识库  ", "重复创建")

    assert second.id == first.id
    assert len(service.list_knowledge_bases()) == 1


def test_delete_knowledge_base_removes_documents_and_chunks(tmp_path):
    service = build_service(tmp_path)
    created = service.create_knowledge_base("待删除知识库", "")
    service.import_text_document(created.id, "资料", "待删除的知识库文本内容。")

    service.delete_knowledge_base(created.id)

    assert service.list_knowledge_bases() == []
    assert service.list_documents(created.id) == []


def test_import_text_document_chunks_and_embeds(tmp_path):
    service = build_service(tmp_path)
    created = service.create_knowledge_base("家电知识库", "文本导入测试")

    document = service.import_text_document(
        created.id,
        "空气炸锅卖点",
        "第一段：强调少油健康。\n第二段：强调一键清洗与小户型收纳便利。",
    )
    documents = service.list_documents(created.id)
    summaries = service.list_knowledge_bases()

    assert document.chunkCount >= 1
    assert document.embeddingStatus.startswith("embedded:")
    assert len(documents) == 1
    assert summaries[-1].chunkCount >= 1


def test_repository_reads_json_with_utf8_bom(tmp_path):
    settings = Settings(merchant_ai_data_file=str(tmp_path / "merchant_ai_store.json"), database_url="", redis_url="", _env_file=None)
    repository = KnowledgeBaseRepository(settings)
    content = repository.data_file.read_text(encoding="utf-8")
    repository.data_file.write_text(content, encoding="utf-8-sig")
    service = KnowledgeBaseService(repository, EmbeddingService(settings), ChunkingService(settings))

    summaries = service.list_knowledge_bases()

    assert summaries == []


def test_import_pdf_document_extracts_text_chunks_and_embeds(tmp_path):
    service = build_service(tmp_path)
    created = service.create_knowledge_base("PDF 知识库", "PDF 导入测试")

    document = service.import_pdf_document(
        created.id,
        "PDF 卖点",
        "demo.pdf",
        build_minimal_pdf("Jrun PDF RAG text"),
    )

    documents = service.list_documents(created.id)
    assert document.chunkCount >= 1
    assert document.embeddingStatus.startswith("embedded:")
    assert "Jrun PDF RAG text" in documents[0].contentPreview


def build_minimal_pdf(text: str) -> bytes:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(f'BT /F1 24 Tf 100 700 Td ({escaped}) Tj ET'.encode('utf-8'))} >>\nstream\nBT /F1 24 Tf 100 700 Td ({escaped}) Tj ET\nendstream".encode("utf-8"),
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)
