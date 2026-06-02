from typing import Any, Dict, List

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    env: str
    provider: str
    version: str
    mock: bool


class RagUsedChunkResponse(BaseModel):
    chunkId: str
    documentId: str
    knowledgeBaseId: str
    content: str
    score: float = 0.0
    sourceFilename: str = ""
    chunkIndex: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProductCopyResponse(BaseModel):
    generatedTitle: str
    highlights: List[str]
    summary: str
    pendingMerchantConfirmations: List[str] = Field(default_factory=list)
    provider: str
    mock: bool
    success: bool = True
    message: str = "商品文案生成成功（Mock）"
    response_source: str = "no_rag_fallback"
    usedChunks: List[RagUsedChunkResponse] = Field(default_factory=list)
    citations: List[RagUsedChunkResponse] = Field(default_factory=list)
    embeddingProvider: str = ""


class AiModelOptionResponse(BaseModel):
    id: str
    label: str
    provider: str
    modelName: str
    description: str = ""


class KnowledgeBaseOptionResponse(BaseModel):
    id: str
    label: str
    documentCount: int = 0
    chunkCount: int = 0
    embeddingStatus: str = "empty"
    updatedAt: str = ""
    description: str = ""
    source: str = "database"


class KnowledgeBaseSummaryResponse(BaseModel):
    id: str
    label: str
    description: str = ""
    documentCount: int = 0
    chunkCount: int = 0
    embeddingStatus: str = "empty"
    updatedAt: str = ""
    source: str = "database"


class KnowledgeDocumentResponse(BaseModel):
    id: str
    knowledgeBaseId: str
    title: str
    chunkCount: int = 0
    embeddingStatus: str = "pending"
    updatedAt: str = ""
    contentPreview: str = ""


class KnowledgeBaseCreateResponse(BaseModel):
    id: str
    label: str
    description: str = ""
    embeddingStatus: str = "empty"
    source: str = "database"
    updatedAt: str = ""


class KnowledgeBaseUploadTxtResponse(BaseModel):
    knowledgeBaseId: str
    name: str
    documentId: str
    chunkCount: int
    embeddingProvider: str
    status: str = "ready"
