from fastapi import FastAPI

from app.api import catalog, health, knowledge_bases, mock_ai, product_copy
from app.core.config import get_settings
from app.core.logging import setup_logging

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(health.router)
app.include_router(catalog.router, prefix=settings.api_prefix)
app.include_router(knowledge_bases.router, prefix=settings.api_prefix)
app.include_router(product_copy.router, prefix=settings.api_prefix)
app.include_router(mock_ai.router, prefix=settings.api_prefix)
