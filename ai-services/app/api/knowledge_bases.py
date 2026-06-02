from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.dependencies import get_knowledge_base_service
from app.models.requests import KnowledgeBaseCreateRequest, KnowledgeDocumentTextImportRequest
from app.models.responses import (
    KnowledgeBaseCreateResponse,
    KnowledgeBaseSummaryResponse,
    KnowledgeBaseUploadTxtResponse,
    KnowledgeDocumentResponse,
)
from app.services.knowledge_base_service import KnowledgeBaseService

router = APIRouter(prefix="/merchant/knowledge-bases", tags=["merchant-knowledge-bases"])


@router.get("", response_model=List[KnowledgeBaseSummaryResponse])
def list_merchant_knowledge_bases(
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> List[KnowledgeBaseSummaryResponse]:
    return service.list_knowledge_bases()


@router.post("", response_model=KnowledgeBaseCreateResponse)
def create_merchant_knowledge_base(
    request: KnowledgeBaseCreateRequest,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> KnowledgeBaseCreateResponse:
    return service.create_knowledge_base(request.name, request.description or "")


@router.post("/upload-txt", response_model=KnowledgeBaseUploadTxtResponse)
async def upload_txt_create_knowledge_base(
    name: str = Form(...),
    description: str = Form(default=""),
    file: UploadFile = File(...),
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> KnowledgeBaseUploadTxtResponse:
    filename = file.filename or "knowledge.txt"
    if file.content_type not in ("text/plain", "application/octet-stream") and not filename.lower().endswith(".txt"):
        raise HTTPException(status_code=400, detail="仅支持 txt 文件")
    content = await file.read()
    try:
        return service.upload_txt_create_knowledge_base(name, description or "", filename, content)
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/{knowledge_base_id}/documents", response_model=List[KnowledgeDocumentResponse])
def list_merchant_knowledge_base_documents(
    knowledge_base_id: str,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> List[KnowledgeDocumentResponse]:
    return service.list_documents(knowledge_base_id)


@router.post("/{knowledge_base_id}/documents/text", response_model=KnowledgeDocumentResponse)
def import_text_document(
    knowledge_base_id: str,
    request: KnowledgeDocumentTextImportRequest,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> KnowledgeDocumentResponse:
    try:
        return service.import_text_document(knowledge_base_id, request.title, request.content)
    except ValueError as ex:
        raise HTTPException(status_code=404, detail=str(ex))


@router.post("/{knowledge_base_id}/documents/pdf", response_model=KnowledgeDocumentResponse)
async def import_pdf_document(
    knowledge_base_id: str,
    title: str = Form(default=""),
    file: UploadFile = File(...),
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> KnowledgeDocumentResponse:
    filename = file.filename or "未命名 PDF"
    if file.content_type not in ("application/pdf", "application/octet-stream") and not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="PDF 文件不能超过 10MB")

    try:
        return service.import_pdf_document(knowledge_base_id, title or filename, filename, content)
    except ValueError as ex:
        status_code = 404 if "知识库不存在" in str(ex) else 400
        raise HTTPException(status_code=status_code, detail=str(ex))
