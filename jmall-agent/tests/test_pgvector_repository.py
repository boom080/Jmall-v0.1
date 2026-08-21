from pathlib import Path

from app.core.config import Settings
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.services.chunking_service import TextChunk


class FakeResult:
    def __init__(self, row=None, rows=None):
        self.row = row or {}
        self.rows = rows or []

    def first(self):
        return (1,)

    def mappings(self):
        return self

    def one(self):
        return self.row

    def all(self):
        return self.rows


class FakeConnection:
    def __init__(self):
        self.calls = []

    def execute(self, statement, params=None):
        sql = str(statement)
        params = params or {}
        self.calls.append((sql, params))
        if "returning id, knowledge_base_id" in sql:
            return FakeResult(
                row={
                    "id": "doc-1",
                    "knowledge_base_id": params["knowledge_base_id"],
                    "title": params["title"],
                    "content": "content",
                    "chunk_count": 1,
                    "embedding_status": "embedded:mock-embedding",
                    "updated_at": None,
                }
            )
        return FakeResult()


class FakeEngine:
    def __init__(self, connection):
        self.connection = connection

    def begin(self):
        return self

    def connect(self):
        return self

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, traceback):
        return False


def build_database_repository():
    settings = Settings(database_url="", _env_file=None)
    repository = KnowledgeBaseRepository(settings)
    connection = FakeConnection()
    repository.engine = FakeEngine(connection)
    return repository, connection


def test_database_ingest_writes_pgvector_embedding_column():
    repository, connection = build_database_repository()
    embedding = [0.1] * 1024

    repository._save_document_with_chunks_in_database(
        knowledge_base_id="kb-1",
        title="doc.txt",
        content="content",
        chunks=[
            TextChunk(
                content="content",
                chunk_index=0,
                char_count=7,
                metadata={"source_filename": "doc.txt"},
            )
        ],
        embeddings=[embedding],
        embedding_provider="mock-embedding",
        content_hash="hash",
        source_type="txt",
        source_filename="doc.txt",
    )

    chunk_inserts = [call for call in connection.calls if "insert into jmall_rag.knowledge_chunks" in call[0]]
    assert chunk_inserts
    sql, params = chunk_inserts[0]
    assert "embedding" in sql
    assert "cast(:embedding as vector)" in sql
    assert params["embedding"].startswith("[0.1,0.1")
    assert params["embedding_provider"] == "mock-embedding"


def test_database_retriever_uses_pgvector_and_limits_knowledge_base_id():
    repository, connection = build_database_repository()

    repository.search_chunks("kb-1", [0.1] * 1024, top_k=3)

    sql, params = connection.calls[0]
    assert "chunk.embedding <=> cast(:query_embedding as vector)" in sql
    assert "chunk.knowledge_base_id = :knowledge_base_id" in sql
    assert params["knowledge_base_id"] == "kb-1"
    assert params["top_k"] == 3


def test_pgvector_migration_only_rebuilds_rag_tables():
    script = Path(__file__).resolve().parents[1] / "resource" / "db" / "5.7-rag-pgvector-1024.sql"
    sql = script.read_text(encoding="utf-8").lower()

    assert "create extension if not exists vector" in sql
    assert "embedding vector(1024)" in sql
    assert "drop table if exists jrunmall_merchant_ai.knowledge_chunks" in sql
    assert "drop table if exists jrunmall_merchant_ai.knowledge_documents" in sql
    assert "drop table if exists jrunmall_merchant_ai.knowledge_bases" in sql
    assert "jrunmall_pms" not in sql
    assert "jrunmall_ums" not in sql
    assert "jrunmall_commerce" not in sql
