from app.core.config import Settings
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.retrieval.rag_retriever import RagRetriever
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.knowledge_base_service import KnowledgeBaseService


def build_stack(tmp_path):
    settings = Settings(
        merchant_ai_data_file=str(tmp_path / "merchant_ai_store.json"),
        rag_chunk_size=80,
        rag_top_k=1,
        rag_embedding_provider="mock",
        rag_embedding_api_key="",
        database_url="",
        redis_url="",
        _env_file=None,
    )
    repository = KnowledgeBaseRepository(settings)
    embedding_service = EmbeddingService(settings)
    knowledge_service = KnowledgeBaseService(repository, embedding_service, ChunkingService(settings))
    retriever = RagRetriever(settings, repository, embedding_service)
    return knowledge_service, retriever


def test_retriever_filters_by_knowledge_base_id_and_top_k(tmp_path):
    knowledge_service, retriever = build_stack(tmp_path)
    first = knowledge_service.create_knowledge_base("手机知识库", "")
    second = knowledge_service.create_knowledge_base("家电知识库", "")
    knowledge_service.import_text_document(first.id, "手机资料", "手机长续航轻办公，适合通勤。")
    knowledge_service.import_text_document(second.id, "家电资料", "家电静音节能，适合厨房。")

    chunks = retriever.retrieve(first.id, "静音节能长续航", top_k=1)

    assert len(chunks) == 1
    assert chunks[0]["knowledgeBaseId"] == first.id
    assert "家电" not in chunks[0]["content"]
