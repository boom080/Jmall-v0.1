from fastapi import FastAPI
from fastapi.responses import Response

from app.api import agent, catalog, health, images, knowledge_bases, mock_ai, product_copy
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.metrics import get_metrics

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
app.include_router(agent.router, prefix=settings.api_prefix)
app.include_router(images.router, prefix=settings.api_prefix)
app.include_router(agent.styles_router, prefix=settings.api_prefix)
app.include_router(agent.admin_router, prefix=settings.api_prefix)


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=get_metrics(), media_type="text/plain; version=0.0.4")
