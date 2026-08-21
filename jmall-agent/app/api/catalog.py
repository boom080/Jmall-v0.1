from typing import List

from fastapi import APIRouter, Depends

from app.api.dependencies import get_knowledge_base_service, get_model_config_repository
from app.models.responses import AiModelOptionResponse, KnowledgeBaseOptionResponse
from app.repositories.model_config_repository import ModelConfigRepository
from app.services.knowledge_base_service import KnowledgeBaseService

router = APIRouter(tags=["catalog"])


@router.get("/models", response_model=List[AiModelOptionResponse])
def list_models(
    repository: ModelConfigRepository = Depends(get_model_config_repository),
) -> List[AiModelOptionResponse]:
    return repository.list_models()


@router.get("/knowledge-bases", response_model=List[KnowledgeBaseOptionResponse])
def list_knowledge_bases(
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> List[KnowledgeBaseOptionResponse]:
    return service.list_knowledge_bases()
