-- Jmall RAG 知识库 schema
-- Target: PostgreSQL 16 + pgvector
-- Based on resource/db/5.7-rag-pgvector-1024.sql

CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS jmall_rag;

CREATE TABLE IF NOT EXISTS jmall_rag.knowledge_bases (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    label VARCHAR(120),
    description VARCHAR(240) NOT NULL DEFAULT '',
    domain VARCHAR(64) NOT NULL DEFAULT '',
    source VARCHAR(32) NOT NULL DEFAULT 'database',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS jmall_rag.knowledge_documents (
    id VARCHAR(64) PRIMARY KEY,
    knowledge_base_id VARCHAR(64) NOT NULL REFERENCES jmall_rag.knowledge_bases(id) ON DELETE CASCADE,
    title VARCHAR(120) NOT NULL,
    source_type VARCHAR(32) NOT NULL DEFAULT 'text',
    source_filename VARCHAR(255) NOT NULL DEFAULT '',
    content_hash VARCHAR(64) NOT NULL DEFAULT '',
    status VARCHAR(32) NOT NULL DEFAULT 'ready',
    content TEXT NOT NULL DEFAULT '',
    chunk_count INTEGER NOT NULL DEFAULT 0,
    embedding_status VARCHAR(96) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS jmall_rag.knowledge_chunks (
    id VARCHAR(64) PRIMARY KEY,
    knowledge_base_id VARCHAR(64) NOT NULL REFERENCES jmall_rag.knowledge_bases(id) ON DELETE CASCADE,
    document_id VARCHAR(64) NOT NULL REFERENCES jmall_rag.knowledge_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    char_count INTEGER NOT NULL DEFAULT 0,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(1024),
    embedding_provider VARCHAR(96) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, chunk_index)
);

CREATE UNIQUE INDEX IF NOT EXISTS uk_knowledge_documents_kb_hash
    ON jmall_rag.knowledge_documents (knowledge_base_id, content_hash)
    WHERE content_hash <> '';

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_kb
    ON jmall_rag.knowledge_chunks (knowledge_base_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_document
    ON jmall_rag.knowledge_chunks (document_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding_hnsw
    ON jmall_rag.knowledge_chunks
    USING hnsw (embedding vector_cosine_ops)
    WHERE embedding IS NOT NULL;

-- AI 请求日志
CREATE TABLE IF NOT EXISTS jmall_rag.ai_request_logs (
    id BIGSERIAL PRIMARY KEY,
    agent_type VARCHAR(64) NOT NULL DEFAULT 'copywriter',
    provider VARCHAR(64) NOT NULL,
    model_name VARCHAR(120) NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost_estimate DOUBLE PRECISION DEFAULT 0.0,
    knowledge_base_id VARCHAR(64) DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_request_logs_created
    ON jmall_rag.ai_request_logs (created_at);
