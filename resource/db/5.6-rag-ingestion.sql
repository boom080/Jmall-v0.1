-- 5.6 RAG ingestion schema
-- Target: PostgreSQL + pgvector for merchant-side AI/RAG data.

create extension if not exists vector;

create schema if not exists jrunmall_merchant_ai;

create table if not exists jrunmall_merchant_ai.knowledge_bases (
    id varchar(64) primary key,
    name varchar(120) not null,
    label varchar(120),
    description varchar(240) default '',
    domain varchar(64) default '',
    source varchar(32) not null default 'database',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table jrunmall_merchant_ai.knowledge_bases add column if not exists name varchar(120);
alter table jrunmall_merchant_ai.knowledge_bases add column if not exists label varchar(120);
alter table jrunmall_merchant_ai.knowledge_bases add column if not exists domain varchar(64) default '';
update jrunmall_merchant_ai.knowledge_bases
set name = coalesce(nullif(name, ''), nullif(label, ''), id)
where name is null or name = '';
update jrunmall_merchant_ai.knowledge_bases
set label = coalesce(nullif(label, ''), name)
where label is null or label = '';
alter table jrunmall_merchant_ai.knowledge_bases alter column name set not null;

create table if not exists jrunmall_merchant_ai.knowledge_documents (
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

alter table jrunmall_merchant_ai.knowledge_documents add column if not exists source_type varchar(32) not null default 'text';
alter table jrunmall_merchant_ai.knowledge_documents add column if not exists source_filename varchar(255) not null default '';
alter table jrunmall_merchant_ai.knowledge_documents add column if not exists content_hash varchar(64) not null default '';
alter table jrunmall_merchant_ai.knowledge_documents add column if not exists status varchar(32) not null default 'ready';
alter table jrunmall_merchant_ai.knowledge_documents add column if not exists content text not null default '';
alter table jrunmall_merchant_ai.knowledge_documents add column if not exists chunk_count integer not null default 0;
alter table jrunmall_merchant_ai.knowledge_documents add column if not exists embedding_status varchar(96) not null default 'pending';

create unique index if not exists uk_knowledge_documents_kb_hash
    on jrunmall_merchant_ai.knowledge_documents (knowledge_base_id, content_hash)
    where content_hash <> '';

create table if not exists jrunmall_merchant_ai.knowledge_chunks (
    id varchar(64) primary key,
    knowledge_base_id varchar(64) not null references jrunmall_merchant_ai.knowledge_bases(id) on delete cascade,
    document_id varchar(64) not null references jrunmall_merchant_ai.knowledge_documents(id) on delete cascade,
    chunk_index integer not null,
    content text not null,
    char_count integer not null default 0,
    token_count integer,
    metadata jsonb not null default '{}'::jsonb,
    embedding vector,
    embedding_provider varchar(96) not null default '',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (document_id, chunk_index)
);

alter table jrunmall_merchant_ai.knowledge_chunks add column if not exists char_count integer not null default 0;
alter table jrunmall_merchant_ai.knowledge_chunks add column if not exists token_count integer;
alter table jrunmall_merchant_ai.knowledge_chunks add column if not exists metadata jsonb not null default '{}'::jsonb;
alter table jrunmall_merchant_ai.knowledge_chunks add column if not exists embedding vector;
alter table jrunmall_merchant_ai.knowledge_chunks add column if not exists embedding_provider varchar(96) not null default '';

create index if not exists idx_knowledge_chunks_kb
    on jrunmall_merchant_ai.knowledge_chunks (knowledge_base_id);

create index if not exists idx_knowledge_chunks_document
    on jrunmall_merchant_ai.knowledge_chunks (document_id);

create table if not exists jrunmall_merchant_ai.ai_request_logs (
    id bigserial primary key,
    title varchar(120) not null,
    provider varchar(64) not null,
    model_name varchar(120) not null,
    knowledge_base_id varchar(64) default '',
    created_at timestamptz not null default now()
);

create table if not exists jrunmall_merchant_ai.ai_model_configs (
    id bigserial primary key,
    provider varchar(64) not null,
    model_name varchar(120) not null,
    enabled boolean not null default true,
    metadata_json text not null default '{}',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
