from fastapi import Depends

from app.core.config import Settings, get_settings
from app.langchain_flows.product_copy_graph import ProductCopyLangGraphFlow
from app.providers.factory import ProviderFactory
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.repositories.model_config_repository import ModelConfigRepository
from app.repositories.request_log_repository import RequestLogRepository
from app.retrieval.service import RetrievalService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.product_copy_workflow_service import ProductCopyWorkflowService


def get_provider_factory(settings: Settings = Depends(get_settings)) -> ProviderFactory:
    return ProviderFactory(settings)


def get_knowledge_base_repository(
    settings: Settings = Depends(get_settings),
) -> KnowledgeBaseRepository:
    return KnowledgeBaseRepository(settings)


def get_embedding_service(
    settings: Settings = Depends(get_settings),
) -> EmbeddingService:
    return EmbeddingService(settings)


def get_chunking_service(
    settings: Settings = Depends(get_settings),
) -> ChunkingService:
    return ChunkingService(settings)


def get_model_config_repository(
    provider_factory: ProviderFactory = Depends(get_provider_factory),
) -> ModelConfigRepository:
    return ModelConfigRepository(provider_factory)


def get_request_log_repository() -> RequestLogRepository:
    return RequestLogRepository()


def get_retrieval_service(
    settings: Settings = Depends(get_settings),
    repository: KnowledgeBaseRepository = Depends(get_knowledge_base_repository),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> RetrievalService:
    return RetrievalService(settings, repository, embedding_service)


def get_knowledge_base_service(
    repository: KnowledgeBaseRepository = Depends(get_knowledge_base_repository),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    chunking_service: ChunkingService = Depends(get_chunking_service),
) -> KnowledgeBaseService:
    return KnowledgeBaseService(repository, embedding_service, chunking_service)


def get_product_copy_workflow_service(
    settings: Settings = Depends(get_settings),
    provider_factory: ProviderFactory = Depends(get_provider_factory),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    request_log_repository: RequestLogRepository = Depends(get_request_log_repository),
) -> ProductCopyWorkflowService:
    flow = ProductCopyLangGraphFlow(
        settings=settings,
        provider_factory=provider_factory,
        retrieval_service=retrieval_service,
        request_log_repository=request_log_repository,
    )
    return ProductCopyWorkflowService(flow)
