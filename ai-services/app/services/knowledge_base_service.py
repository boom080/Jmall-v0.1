import hashlib
from io import BytesIO
from typing import List

from pypdf import PdfReader

from app.models.responses import (
    KnowledgeBaseCreateResponse,
    KnowledgeBaseSummaryResponse,
    KnowledgeBaseUploadTxtResponse,
    KnowledgeDocumentResponse,
)
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService


class KnowledgeBaseService:
    def __init__(
        self,
        repository: KnowledgeBaseRepository,
        embedding_service: EmbeddingService,
        chunking_service: ChunkingService,
    ) -> None:
        self.repository = repository
        self.embedding_service = embedding_service
        self.chunking_service = chunking_service

    def list_knowledge_bases(self) -> List[KnowledgeBaseSummaryResponse]:
        return self.repository.list_knowledge_base_summaries()

    def create_knowledge_base(self, name: str, description: str) -> KnowledgeBaseCreateResponse:
        return self.repository.create_knowledge_base(name, description, source="manual")

    def upload_txt_create_knowledge_base(
        self,
        name: str,
        description: str,
        filename: str,
        content: bytes,
    ) -> KnowledgeBaseUploadTxtResponse:
        text = self._decode_utf8_txt(content)
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("知识库名称不能为空")
        source_filename = filename.strip() or "knowledge.txt"
        if not source_filename.lower().endswith(".txt"):
            raise ValueError("仅支持 txt 文件")

        knowledge_base = self.repository.create_knowledge_base(
            normalized_name,
            (description or "").strip(),
            source="upload-txt",
            domain="ecommerce",
        )
        document = self.import_text_document(
            knowledge_base.id,
            source_filename,
            text,
            source_type="txt",
            source_filename=source_filename,
        )
        provider = document.embeddingStatus.replace("embedded:", "", 1) if document.embeddingStatus else ""
        return KnowledgeBaseUploadTxtResponse(
            knowledgeBaseId=knowledge_base.id,
            name=knowledge_base.label,
            documentId=document.id,
            chunkCount=document.chunkCount,
            embeddingProvider=provider,
            status="ready",
        )

    def import_text_document(
        self,
        knowledge_base_id: str,
        title: str,
        content: str,
        source_type: str = "text",
        source_filename: str = "",
    ) -> KnowledgeDocumentResponse:
        normalized_title = title.strip() or source_filename.strip() or "未命名文本"
        cleaned = self.chunking_service.clean_text(content)
        if not cleaned:
            raise ValueError("文本内容不能为空")
        content_hash = self._content_hash(cleaned)
        existing = self.repository.find_document_by_hash(knowledge_base_id, content_hash)
        if existing is not None:
            return existing

        chunks = self.chunking_service.chunk_text(
            cleaned,
            source_filename=source_filename or normalized_title,
            document_title=normalized_title,
            source_type=source_type,
        )
        if not chunks:
            raise ValueError("文本未生成有效 chunk")
        embeddings, provider = self.embedding_service.embed_texts([chunk.content for chunk in chunks])
        return self.repository.save_document_with_chunks(
            knowledge_base_id=knowledge_base_id,
            title=normalized_title,
            content=cleaned,
            chunks=chunks,
            embeddings=embeddings,
            embedding_provider=provider,
            content_hash=content_hash,
            source_type=source_type,
            source_filename=source_filename or normalized_title,
        )

    def import_pdf_document(
        self,
        knowledge_base_id: str,
        title: str,
        filename: str,
        content: bytes,
    ) -> KnowledgeDocumentResponse:
        text = self._extract_pdf_text(content)
        normalized_title = title.strip() or filename.strip() or "未命名 PDF"
        return self.import_text_document(
            knowledge_base_id,
            normalized_title,
            text,
            source_type="pdf",
            source_filename=filename,
        )

    def list_documents(self, knowledge_base_id: str) -> List[KnowledgeDocumentResponse]:
        return self.repository.list_documents(knowledge_base_id)

    def _decode_utf8_txt(self, content: bytes) -> str:
        if not content:
            raise ValueError("txt 文件不能为空")
        if len(content) > 2 * 1024 * 1024:
            raise ValueError("txt 文件不能超过 2MB")
        try:
            return content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("txt 文件必须使用 UTF-8 编码") from exc

    def _extract_pdf_text(self, content: bytes) -> str:
        if not content:
            raise ValueError("PDF 文件不能为空")
        try:
            reader = PdfReader(BytesIO(content))
            pages = []
            for page in reader.pages:
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(text.strip())
        except Exception as exc:
            raise ValueError("PDF 解析失败，请确认上传的是可读取的 PDF 文件") from exc

        normalized = "\n\n".join(pages).strip()
        if not normalized:
            raise ValueError("PDF 未解析到可用于 RAG 的文本内容")
        return normalized[:20000]

    def _content_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
