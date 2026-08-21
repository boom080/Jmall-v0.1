-- 5.7 RAG pgvector 1024 migration
-- Scope: local PostgreSQL only, schema jrunmall_merchant_ai only.
-- This intentionally clears local mock RAG data because mock 8-d vectors
-- cannot be reused with text-embedding-v4 1024-d vectors.

create extension if not exists vector;

create schema if not exists jrunmall_merchant_ai;

drop table if exists jrunmall_merchant_ai.knowledge_chunks cascade;
drop table if exists jrunmall_merchant_ai.knowledge_documents cascade;
drop table if exists jrunmall_merchant_ai.knowledge_bases cascade;

create table jrunmall_merchant_ai.knowledge_bases (
    id varchar(64) primary key,
    name varchar(120) not null,
    label varchar(120),
    description varchar(240) not null default '',
    domain varchar(64) not null default '',
    source varchar(32) not null default 'database',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table jrunmall_merchant_ai.knowledge_documents (
    id varchar(64) primary key,
    knowledge_base_id varchar(64) not null references jrunmall_merchant_ai.knowledge_bases(id) on delete cascade,
    title varchar(120) not null,
    source_type varchar(32) not null default 'text',
    source_filename varchar(255) not null default '',
    content_hash varchar(64) not null default '',
    status varchar(32) not null default 'ready',
    content text not null default '',
    chunk_count integer not null default 0,
    embedding_status varchar(96) not null default 'pending',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table jrunmall_merchant_ai.knowledge_chunks (
    id varchar(64) primary key,
    knowledge_base_id varchar(64) not null references jrunmall_merchant_ai.knowledge_bases(id) on delete cascade,
    document_id varchar(64) not null references jrunmall_merchant_ai.knowledge_documents(id) on delete cascade,
    chunk_index integer not null,
    content text not null,
    char_count integer not null default 0,
    metadata jsonb not null default '{}'::jsonb,
    embedding vector(1024),
    embedding_provider varchar(96) not null default '',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (document_id, chunk_index)
);

create unique index uk_knowledge_documents_kb_hash
    on jrunmall_merchant_ai.knowledge_documents (knowledge_base_id, content_hash)
    where content_hash <> '';

create index idx_knowledge_chunks_kb
    on jrunmall_merchant_ai.knowledge_chunks (knowledge_base_id);

create index idx_knowledge_chunks_document
    on jrunmall_merchant_ai.knowledge_chunks (document_id);

-- HNSW does not require training data and is a reasonable pgvector index
-- once local RAG data grows. The query still filters by knowledge_base_id.
create index idx_knowledge_chunks_embedding_hnsw
    on jrunmall_merchant_ai.knowledge_chunks
    using hnsw (embedding vector_cosine_ops)
    where embedding is not null;
