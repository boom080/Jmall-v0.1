import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.core.config import Settings
from app.models.responses import (
    KnowledgeBaseCreateResponse,
    KnowledgeBaseOptionResponse,
    KnowledgeBaseSummaryResponse,
    KnowledgeDocumentResponse,
)
from app.services.chunking_service import TextChunk


FAKE_KNOWLEDGE_BASE_IDS = {
    "kb-product-baseline",
    "kb-appliance-style",
    "kb-f9bbace5a922",
    "kb-5386c067f305",
}
FAKE_KNOWLEDGE_BASE_LABELS = {
    "商品基础知识库",
    "家电文案知识库",
    "Runbook KB 20260507131952",
    "Runbook KB 20260507132201",
}
FAKE_SOURCES = {"fallback", "file-fallback", "java-fallback", "database-fallback"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_default_state() -> Dict[str, List[Dict[str, object]]]:
    return {"knowledge_bases": [], "documents": [], "chunks": []}


class KnowledgeBaseRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.schema = settings.merchant_schema
        self.engine: Optional[Engine] = None
        if settings.database_url:
            self.engine = create_engine(settings.database_url, future=True, pool_pre_ping=True)
            self.data_file = None
        else:
            base_dir = Path(__file__).resolve().parents[2]
            self.data_file = (base_dir / settings.merchant_ai_data_file).resolve()
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.data_file.exists():
                self._save_state(build_default_state())

    def list_knowledge_bases(self) -> List[KnowledgeBaseOptionResponse]:
        if self.engine is not None:
            return self._list_knowledge_bases_from_database()
        return [
            KnowledgeBaseOptionResponse(
                id=str(item["id"]),
                label=str(item.get("label") or item.get("name") or item["id"]),
                description=str(item.get("description", "")),
                documentCount=self._document_count(str(item["id"])),
                chunkCount=self._chunk_count(str(item["id"])),
                embeddingStatus=self._knowledge_base_embedding_status(str(item["id"])),
                updatedAt=str(item.get("updatedAt", "")),
                source=str(item.get("source", "upload-txt")),
            )
            for item in self._visible_knowledge_bases(self._state()["knowledge_bases"])
        ]

    def list_knowledge_base_summaries(self) -> List[KnowledgeBaseSummaryResponse]:
        return [KnowledgeBaseSummaryResponse(**item.model_dump()) for item in self.list_knowledge_bases()]

    def create_knowledge_base(
        self,
        name: str,
        description: str,
        source: str = "manual",
        domain: str = "",
    ) -> KnowledgeBaseCreateResponse:
        if self.engine is not None:
            return self._create_knowledge_base_in_database(name, description, source, domain)

        state = self._state()
        now = utc_now_iso()
        knowledge_base = {
            "id": f"kb-{uuid.uuid4().hex[:12]}",
            "name": name,
            "label": name,
            "description": description,
            "domain": domain,
            "source": source,
            "createdAt": now,
            "updatedAt": now,
        }
        state["knowledge_bases"].append(knowledge_base)
        self._save_state(state)
        return KnowledgeBaseCreateResponse(
            id=str(knowledge_base["id"]),
            label=name,
            description=description,
            embeddingStatus="empty",
            source=source,
            updatedAt=now,
        )

    def save_document_with_chunks(
        self,
        knowledge_base_id: str,
        title: str,
        content: str,
        chunks: List[TextChunk],
        embeddings: List[List[float]],
        embedding_provider: str,
        content_hash: str,
        source_type: str,
        source_filename: str,
    ) -> KnowledgeDocumentResponse:
        existing = self.find_document_by_hash(knowledge_base_id, content_hash)
        if existing is not None:
            return existing

        if self.engine is not None:
            return self._save_document_with_chunks_in_database(
                knowledge_base_id=knowledge_base_id,
                title=title,
                content=content,
                chunks=chunks,
                embeddings=embeddings,
                embedding_provider=embedding_provider,
                content_hash=content_hash,
                source_type=source_type,
                source_filename=source_filename,
            )

        state = self._state()
        knowledge_base = self._get_knowledge_base(state, knowledge_base_id)
        if knowledge_base is None:
            raise ValueError("知识库不存在")

        now = utc_now_iso()
        document_id = f"doc-{uuid.uuid4().hex[:12]}"
        document = {
            "id": document_id,
            "knowledgeBaseId": knowledge_base_id,
            "title": title,
            "content": content,
            "sourceType": source_type,
            "sourceFilename": source_filename,
            "contentHash": content_hash,
            "status": "ready",
            "chunkCount": len(chunks),
            "embeddingStatus": f"embedded:{embedding_provider}",
            "createdAt": now,
            "updatedAt": now,
        }
        state["documents"].append(document)

        for index, chunk in enumerate(chunks):
            state["chunks"].append(
                {
                    "id": f"chunk-{uuid.uuid4().hex[:12]}",
                    "knowledgeBaseId": knowledge_base_id,
                    "documentId": document_id,
                    "chunkIndex": chunk.chunk_index,
                    "content": chunk.content,
                    "charCount": chunk.char_count,
                    "metadata": chunk.metadata,
                    "embedding": embeddings[index] if index < len(embeddings) else [],
                    "embeddingProvider": embedding_provider,
                    "createdAt": now,
                    "updatedAt": now,
                }
            )

        knowledge_base["updatedAt"] = now
        self._save_state(state)
        return self._to_document_response(document)

    def find_document_by_hash(self, knowledge_base_id: str, content_hash: str) -> Optional[KnowledgeDocumentResponse]:
        if not knowledge_base_id or not content_hash:
            return None
        if self.engine is not None:
            sql = text(
                f"""
                select id, knowledge_base_id, title, content, chunk_count, embedding_status, updated_at
                from {self.schema}.knowledge_documents
                where knowledge_base_id = :knowledge_base_id and content_hash = :content_hash
                limit 1
                """
            )
            with self.engine.connect() as connection:
                row = connection.execute(
                    sql,
                    {"knowledge_base_id": knowledge_base_id, "content_hash": content_hash},
                ).mappings().first()
            return self._to_document_response(dict(row)) if row else None

        state = self._state()
        for document in state["documents"]:
            if (
                str(document.get("knowledgeBaseId")) == knowledge_base_id
                and str(document.get("contentHash", "")) == content_hash
            ):
                return self._to_document_response(document)
        return None

    def list_documents(self, knowledge_base_id: str) -> List[KnowledgeDocumentResponse]:
        if self.engine is not None:
            sql = text(
                f"""
                select id, knowledge_base_id, title, content, chunk_count, embedding_status, updated_at
                from {self.schema}.knowledge_documents
                where knowledge_base_id = :knowledge_base_id
                order by updated_at desc
                """
            )
            with self.engine.connect() as connection:
                rows = connection.execute(sql, {"knowledge_base_id": knowledge_base_id}).mappings().all()
            return [self._to_document_response(dict(row)) for row in rows]

        state = self._state()
        if self._get_knowledge_base(state, knowledge_base_id) is None:
            return []
        documents = [
            self._to_document_response(item)
            for item in state["documents"]
            if item["knowledgeBaseId"] == knowledge_base_id
        ]
        return sorted(documents, key=lambda item: item.updatedAt, reverse=True)

    def search_chunks(
        self,
        knowledge_base_id: Optional[str],
        query_embedding: List[float],
        top_k: int,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        if not knowledge_base_id or not query_embedding:
            return []
        if self.engine is not None:
            chunks = self._search_chunks_in_database(knowledge_base_id, query_embedding, top_k)
        else:
            chunks = self._search_chunks_in_file(knowledge_base_id, query_embedding, top_k)
        if min_score <= 0:
            return chunks
        return [chunk for chunk in chunks if float(chunk.get("score") or 0.0) >= min_score]

    def get_chunks_for_retrieval(self, knowledge_base_id: Optional[str]) -> List[Dict[str, object]]:
        if not knowledge_base_id:
            return []
        state = self._state()
        return [item for item in state["chunks"] if item["knowledgeBaseId"] == knowledge_base_id]

    def get_documents(self, knowledge_base_id: Optional[str]) -> List[str]:
        if not knowledge_base_id:
            bases = self.list_knowledge_bases()
            if not bases:
                return []
            knowledge_base_id = bases[0].id
        return [item.contentPreview for item in self.list_documents(knowledge_base_id)]

    def _list_knowledge_bases_from_database(self) -> List[KnowledgeBaseOptionResponse]:
        sql = text(
            f"""
            select
                kb.id,
                coalesce(nullif(kb.name, ''), nullif(kb.label, ''), kb.id) as label,
                coalesce(kb.description, '') as description,
                coalesce(kb.source, 'database') as source,
                kb.updated_at,
                count(distinct doc.id) as document_count,
                count(chunk.id) as chunk_count,
                coalesce(max(doc.embedding_status), 'empty') as embedding_status
            from {self.schema}.knowledge_bases kb
            left join {self.schema}.knowledge_documents doc on doc.knowledge_base_id = kb.id
            left join {self.schema}.knowledge_chunks chunk on chunk.knowledge_base_id = kb.id
            where coalesce(kb.source, '') not in ('fallback', 'file-fallback', 'java-fallback', 'database-fallback')
              and kb.id not in ('kb-product-baseline', 'kb-appliance-style', 'kb-f9bbace5a922', 'kb-5386c067f305')
              and coalesce(kb.name, kb.label, '') not in ('商品基础知识库', '家电文案知识库', 'Runbook KB 20260507131952', 'Runbook KB 20260507132201')
            group by kb.id, kb.name, kb.label, kb.description, kb.source, kb.updated_at
            order by kb.updated_at desc
            """
        )
        with self.engine.connect() as connection:
            rows = connection.execute(sql).mappings().all()
        return [
            KnowledgeBaseOptionResponse(
                id=str(row["id"]),
                label=str(row["label"]),
                description=str(row["description"]),
                documentCount=int(row["document_count"] or 0),
                chunkCount=int(row["chunk_count"] or 0),
                embeddingStatus=str(row["embedding_status"] or "empty"),
                updatedAt=self._format_datetime(row["updated_at"]),
                source=str(row["source"] or "database"),
            )
            for row in rows
        ]

    def _create_knowledge_base_in_database(
        self,
        name: str,
        description: str,
        source: str,
        domain: str,
    ) -> KnowledgeBaseCreateResponse:
        knowledge_base_id = f"kb-{uuid.uuid4().hex[:12]}"
        sql = text(
            f"""
            insert into {self.schema}.knowledge_bases (id, name, label, description, domain, source)
            values (:id, :name, :label, :description, :domain, :source)
            returning id, name, description, source, updated_at
            """
        )
        with self.engine.begin() as connection:
            row = connection.execute(
                sql,
                {
                    "id": knowledge_base_id,
                    "name": name,
                    "label": name,
                    "description": description,
                    "domain": domain,
                    "source": source,
                },
            ).mappings().one()
        return KnowledgeBaseCreateResponse(
            id=str(row["id"]),
            label=str(row["name"]),
            description=str(row["description"] or ""),
            embeddingStatus="empty",
            source=str(row["source"] or source),
            updatedAt=self._format_datetime(row["updated_at"]),
        )

    def _save_document_with_chunks_in_database(
        self,
        knowledge_base_id: str,
        title: str,
        content: str,
        chunks: List[TextChunk],
        embeddings: List[List[float]],
        embedding_provider: str,
        content_hash: str,
        source_type: str,
        source_filename: str,
    ) -> KnowledgeDocumentResponse:
        document_id = f"doc-{uuid.uuid4().hex[:12]}"
        embedding_status = f"embedded:{embedding_provider}"
        with self.engine.begin() as connection:
            exists = connection.execute(
                text(f"select 1 from {self.schema}.knowledge_bases where id = :id"),
                {"id": knowledge_base_id},
            ).first()
            if exists is None:
                raise ValueError("知识库不存在")

            document_row = connection.execute(
                text(
                    f"""
                    insert into {self.schema}.knowledge_documents (
                        id, knowledge_base_id, title, source_type, source_filename,
                        content_hash, status, content, chunk_count, embedding_status
                    )
                    values (
                        :id, :knowledge_base_id, :title, :source_type, :source_filename,
                        :content_hash, 'ready', :content, :chunk_count, :embedding_status
                    )
                    returning id, knowledge_base_id, title, content, chunk_count, embedding_status, updated_at
                    """
                ),
                {
                    "id": document_id,
                    "knowledge_base_id": knowledge_base_id,
                    "title": title,
                    "source_type": source_type,
                    "source_filename": source_filename,
                    "content_hash": content_hash,
                    "content": content,
                    "chunk_count": len(chunks),
                    "embedding_status": embedding_status,
                },
            ).mappings().one()

            chunk_sql = text(
                f"""
                insert into {self.schema}.knowledge_chunks (
                    id, knowledge_base_id, document_id, chunk_index, content,
                    char_count, metadata, embedding, embedding_provider
                )
                values (
                    :id, :knowledge_base_id, :document_id, :chunk_index, :content,
                    :char_count, cast(:metadata as jsonb), cast(:embedding as vector), :embedding_provider
                )
                """
            )
            for index, chunk in enumerate(chunks):
                connection.execute(
                    chunk_sql,
                    {
                        "id": f"chunk-{uuid.uuid4().hex[:12]}",
                        "knowledge_base_id": knowledge_base_id,
                        "document_id": document_id,
                        "chunk_index": chunk.chunk_index,
                        "content": chunk.content,
                        "char_count": chunk.char_count,
                        "metadata": json.dumps(chunk.metadata, ensure_ascii=False),
                        "embedding": self._vector_literal(embeddings[index] if index < len(embeddings) else []),
                        "embedding_provider": embedding_provider,
                    },
                )

            connection.execute(
                text(f"update {self.schema}.knowledge_bases set updated_at = now() where id = :id"),
                {"id": knowledge_base_id},
            )

        return self._to_document_response(dict(document_row))

    def _search_chunks_in_database(
        self,
        knowledge_base_id: str,
        query_embedding: List[float],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        sql = text(
            f"""
            select
                chunk.id as chunk_id,
                chunk.document_id,
                chunk.knowledge_base_id,
                chunk.content,
                chunk.chunk_index,
                chunk.metadata,
                doc.source_filename,
                chunk.embedding_provider,
                (1 - (chunk.embedding <=> cast(:query_embedding as vector))) as score
            from {self.schema}.knowledge_chunks chunk
            join {self.schema}.knowledge_documents doc on doc.id = chunk.document_id
            where chunk.knowledge_base_id = :knowledge_base_id
              and chunk.embedding is not null
            order by chunk.embedding <=> cast(:query_embedding as vector)
            limit :top_k
            """
        )
        with self.engine.connect() as connection:
            rows = connection.execute(
                sql,
                {
                    "knowledge_base_id": knowledge_base_id,
                    "query_embedding": self._vector_literal(query_embedding),
                    "top_k": max(1, top_k),
                },
            ).mappings().all()
        return [self._chunk_row_to_response(dict(row)) for row in rows]

    def _search_chunks_in_file(
        self,
        knowledge_base_id: str,
        query_embedding: List[float],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        chunks = self.get_chunks_for_retrieval(knowledge_base_id)
        scored: List[tuple[float, Dict[str, Any]]] = []
        for chunk in chunks:
            embedding = chunk.get("embedding") or []
            if not embedding:
                continue
            score = self._dot_product(query_embedding, embedding)
            scored.append((score, self._file_chunk_to_response(chunk, score)))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in scored[: max(1, top_k)]]

    def _state(self) -> Dict[str, List[Dict[str, object]]]:
        assert self.data_file is not None
        try:
            with self.data_file.open("r", encoding="utf-8-sig") as handle:
                loaded = json.load(handle)
        except (json.JSONDecodeError, FileNotFoundError):
            return build_default_state()
        state = build_default_state()
        for key in state:
            value = loaded.get(key, [])
            state[key] = value if isinstance(value, list) else []
        return state

    def _save_state(self, state: Dict[str, List[Dict[str, object]]]) -> None:
        assert self.data_file is not None
        with self.data_file.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2)

    def _get_knowledge_base(
        self,
        state: Dict[str, List[Dict[str, object]]],
        knowledge_base_id: str,
    ) -> Optional[Dict[str, object]]:
        for item in self._visible_knowledge_bases(state["knowledge_bases"]):
            if item["id"] == knowledge_base_id:
                return item
        return None

    def _visible_knowledge_bases(self, items: List[Dict[str, object]]) -> List[Dict[str, object]]:
        return [item for item in items if not self._is_fake_knowledge_base(item)]

    def _is_fake_knowledge_base(self, item: Dict[str, object]) -> bool:
        knowledge_base_id = str(item.get("id", ""))
        label = str(item.get("label") or item.get("name") or "")
        source = str(item.get("source", ""))
        return (
            knowledge_base_id in FAKE_KNOWLEDGE_BASE_IDS
            or label in FAKE_KNOWLEDGE_BASE_LABELS
            or source in FAKE_SOURCES
        )

    def _document_count(self, knowledge_base_id: str) -> int:
        return len([item for item in self._state()["documents"] if item["knowledgeBaseId"] == knowledge_base_id])

    def _chunk_count(self, knowledge_base_id: str) -> int:
        return len([item for item in self._state()["chunks"] if item["knowledgeBaseId"] == knowledge_base_id])

    def _knowledge_base_embedding_status(self, knowledge_base_id: str) -> str:
        documents = [item for item in self._state()["documents"] if item["knowledgeBaseId"] == knowledge_base_id]
        if not documents:
            return "empty"
        statuses = {str(item.get("embeddingStatus", "pending")) for item in documents}
        if len(statuses) == 1:
            return statuses.pop()
        return "partial"

    def _to_document_response(self, document: Dict[str, object]) -> KnowledgeDocumentResponse:
        content = str(document.get("content", ""))
        preview = content if len(content) <= 80 else f"{content[:80]}..."
        return KnowledgeDocumentResponse(
            id=str(document["id"]),
            knowledgeBaseId=str(document.get("knowledgeBaseId") or document.get("knowledge_base_id")),
            title=str(document["title"]),
            chunkCount=int(document.get("chunkCount") or document.get("chunk_count") or 0),
            embeddingStatus=str(document.get("embeddingStatus") or document.get("embedding_status") or "pending"),
            updatedAt=self._format_datetime(document.get("updatedAt") or document.get("updated_at")),
            contentPreview=preview,
        )

    def _chunk_row_to_response(self, row: Dict[str, Any]) -> Dict[str, Any]:
        metadata = row.get("metadata") or {}
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {}
        return {
            "chunkId": str(row.get("chunk_id", "")),
            "documentId": str(row.get("document_id", "")),
            "knowledgeBaseId": str(row.get("knowledge_base_id", "")),
            "content": str(row.get("content", "")),
            "score": float(row.get("score") or 0.0),
            "sourceFilename": str(row.get("source_filename") or metadata.get("source_filename") or ""),
            "chunkIndex": int(row.get("chunk_index") or 0),
            "metadata": metadata,
            "embeddingProvider": str(row.get("embedding_provider") or ""),
        }

    def _file_chunk_to_response(self, chunk: Dict[str, Any], score: float) -> Dict[str, Any]:
        metadata = chunk.get("metadata") or {}
        return {
            "chunkId": str(chunk.get("id", "")),
            "documentId": str(chunk.get("documentId", "")),
            "knowledgeBaseId": str(chunk.get("knowledgeBaseId", "")),
            "content": str(chunk.get("content", "")),
            "score": float(score),
            "sourceFilename": str(metadata.get("source_filename", "")),
            "chunkIndex": int(chunk.get("chunkIndex") or metadata.get("chunk_index") or 0),
            "metadata": metadata,
            "embeddingProvider": str(chunk.get("embeddingProvider", "")),
        }

    def _format_datetime(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.replace(microsecond=0).isoformat()
        return str(value)

    def _vector_literal(self, embedding: List[float]) -> str:
        return "[" + ",".join(str(float(item)) for item in embedding) + "]"

    def _dot_product(self, left: List[float], right: List[float]) -> float:
        if not left or not right:
            return 0.0
        size = min(len(left), len(right))
        return sum(float(left[index]) * float(right[index]) for index in range(size))
