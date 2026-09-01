"""Agent orchestration API router.

Endpoints:
- POST /api/agent/orchestrate  - Full multi-agent orchestration
- POST /api/agent/product/copy  - Fact draft plus selected platform skill
- POST /api/agent/product/review - Single-agent compliance review
- POST /api/agent/product/insights - Single-agent market research
- GET  /api/styles             - List available styles
- POST /api/styles/preview     - Preview product in a specific style
- POST /api/agent/search/trends - Search market trends
- GET  /api/admin/cost-stats    - Token usage and cost statistics
"""

import json
import logging
import asyncio
from typing import Any, Dict, Optional, Set

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.agents.copywriter import CopywriterAgent, SUPPORTED_STYLES
from app.agents.graph import AgentGraphState, AgentOrchestratorGraph
from app.agents.input_gate import assess_product_input
from app.agents.market_research import MarketResearchAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.style_adapter import StyleAdapterAgent, STYLE_PROFILES, StyleAdapterAgent as SA
from app.api.dependencies import get_job_store, get_provider_factory, get_retrieval_service
from app.services.job_store import JobStore
from app.core.config import Settings, get_settings
from app.core.metrics import GenerationObservation
from app.services.input_assessment_service import assess_input_at_boundary
from app.llm.router import LLMRouter
from app.models.agent_models import (
    CopyOnlyRequest,
    CopyOnlyResponse,
    CostStatsResponse,
    InputAssessmentResponse,
    InsightsRequest,
    InsightsResponse,
    OrchestrateRequest,
    OrchestrateResponse,
    RAGEvaluateRequest,
    RAGEvaluateResponse,
    ReviewOnlyRequest,
    ReviewOnlyResponse,
    SearchTrendsRequest,
    SearchTrendsResponse,
    StyleInfo,
    StylePreviewRequest,
    StylePreviewResponse,
    StylesListResponse,
)
from app.providers.factory import ProviderFactory
from app.retrieval.service import RetrievalService
from app.tools.search import get_search_tool, search_market_trends

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])

# ---- Shared state ----
_orchestrator_graph: Optional[AgentOrchestratorGraph] = None
_background_tasks: Set[asyncio.Task] = set()


def get_orchestrator_graph(
    settings: Settings = Depends(get_settings),
    provider_factory: ProviderFactory = Depends(get_provider_factory),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> AgentOrchestratorGraph:
    """Get or create the singleton orchestrator graph instance."""
    global _orchestrator_graph
    if _orchestrator_graph is None:
        _orchestrator_graph = AgentOrchestratorGraph(
            settings=settings,
            provider_factory=provider_factory,
            retrieval_service=retrieval_service,
        )
    return _orchestrator_graph


# ---- Agent orchestration endpoints ----

@router.post("/input-assessment", response_model=InputAssessmentResponse)
async def input_assessment(request: OrchestrateRequest) -> InputAssessmentResponse:
    """Free deterministic preflight for the model-backed orchestration graph."""
    assessment = assess_input_at_boundary(request.product_info.model_dump(), "preflight")
    return InputAssessmentResponse(input_assessment=assessment)

@router.post("/orchestrate", response_model=OrchestrateResponse)
async def orchestrate(
    request: OrchestrateRequest,
    graph: AgentOrchestratorGraph = Depends(get_orchestrator_graph),
) -> OrchestrateResponse:
    """Main agent orchestration endpoint.

    Coordinates multiple AI agents to:
    1. Research market trends for the product category
    2. Generate e-commerce copy optimized for the target platform
    3. Review copy for compliance issues
    4. Adapt the style to match the target platform

    Returns the complete orchestration result with all agent outputs.
    """
    try:
        state: AgentGraphState = {
            "user_request": request.user_request or "",
            "product_info": {
                "title": request.product_info.title,
                "category": request.product_info.category,
                "description": request.product_info.description or "",
                "price": request.product_info.price or "",
                "specifications": request.product_info.specifications or "",
                "target_audience": request.product_info.target_audience or "",
                "usage_scenarios": request.product_info.usage_scenarios or "",
            },
            "target_style": request.target_style,
            "knowledge_base_id": request.knowledge_base_id or "",
            "errors": [],
        }

        result = await graph.invoke(state)
        final = result.get("final_result", {})
        errors = result.get("errors", [])

        cost_stats = result.get("cost_stats") or graph.get_cost_stats()

        return OrchestrateResponse(
            success=final.get("overall_status", "error") != "error",
            message=f"编排完成，状态：{final.get('overall_status', 'unknown')}",
            overall_status=final.get("overall_status", "unknown"),
            product_title=final.get("product_title", ""),
            market_insights=final.get("market_insights", {}),
            copy_content=final.get("copy", {}),
            compliance=final.get("compliance", {}),
            style_adaptation=final.get("style_adaptation", {}),
            pending_confirmations=final.get("pending_confirmations", []),
            input_assessment=final.get("input_assessment", {}),
            errors=errors,
            generation_metadata=final.get("generation_metadata", {}),
            cost_stats=cost_stats,
        )
    except Exception as exc:
        logger.exception("Orchestration endpoint failed")
        raise HTTPException(status_code=500, detail=f"编排失败: {exc}")


@router.post("/orchestrate/stream")
async def orchestrate_stream(
    request: OrchestrateRequest,
    graph: AgentOrchestratorGraph = Depends(get_orchestrator_graph),
    job_store: JobStore = Depends(get_job_store),
):
    """SSE streaming agent orchestration endpoint.

    Streams progress events as each agent completes:
    - event: job_created — emitted first with jobId for reconnection
    - event: agent_progress — individual agent results
    - event: orchestration_complete — final aggregated result
    - event: error — fatal error

    Jobs persist in Redis for 1 hour. Use GET /api/agent/jobs/{jobId}
    to reconnect and retrieve status after page navigation.
    """
    queue: asyncio.Queue = asyncio.Queue()
    logger.info(
        "agent_request_received user_id=%s product_draft_id=%s title=%s",
        request.user_id,
        request.product_draft_id,
        request.product_info.title,
    )
    job_id = job_store.create_job(
        user_id=request.user_id,
        product_draft_id=request.product_draft_id,
        product_info={
            "title": request.product_info.title,
            "category": request.product_info.category,
            "description": request.product_info.description or "",
            "price": request.product_info.price or "",
            "specifications": request.product_info.specifications or "",
            "target_audience": request.product_info.target_audience or "",
            "usage_scenarios": request.product_info.usage_scenarios or "",
        },
        target_style=request.target_style,
        knowledge_base_id=request.knowledge_base_id,
    )
    logger.info("agent_job_created job_id=%s user_id=%s", job_id, request.user_id)

    async def progress_callback(agent_name: str, status: str, result: dict) -> None:
        """Put progress events into the queue for SSE streaming and update job store."""
        data = {
            "agent": agent_name,
            "status": status,
            **result,
        }
        await queue.put({
            "event": "agent_progress" if agent_name not in ("orchestration_complete", "error") else agent_name,
            "data": data,
        })
        # Persist to job store
        job_store.update_progress(job_id, agent_name, status, result)

    state: AgentGraphState = {
        "user_request": request.user_request or "",
        "product_info": {
            "title": request.product_info.title,
            "category": request.product_info.category,
            "description": request.product_info.description or "",
            "price": request.product_info.price or "",
            "specifications": request.product_info.specifications or "",
            "target_audience": request.product_info.target_audience or "",
            "usage_scenarios": request.product_info.usage_scenarios or "",
        },
        "target_style": request.target_style,
        "knowledge_base_id": request.knowledge_base_id or "",
        "errors": [],
    }

    async def run_job() -> None:
        job_store.mark_running(job_id)
        try:
            await graph.invoke(state, progress_callback=progress_callback)
            logger.info("agent_job_completed job_id=%s", job_id)
        except Exception as exc:
            logger.exception("Background orchestration failed for job %s", job_id)
            job_store.mark_failed(job_id, str(exc))
            await queue.put({"event": "error", "data": {"error": str(exc)}})

    # Start and retain the task before StreamingResponse begins iterating. The job
    # therefore keeps running when the browser disconnects from the SSE transport.
    task = asyncio.create_task(run_job(), name=f"agent-job-{job_id}")
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    async def event_generator():
        """Generate SSE events from the queue."""
        # Emit job_created event first so frontend can reconnect
        yield f"event: job_created\ndata: {json.dumps({'jobId': job_id}, ensure_ascii=False)}\n\n"

        # Stream events until the task is done and queue is drained
        task_done = False
        while not task_done or not queue.empty():
            try:
                # Wait for an event with a timeout
                event = await asyncio.wait_for(queue.get(), timeout=0.1)
                yield f"event: {event['event']}\ndata: {json.dumps(event['data'], ensure_ascii=False)}\n\n"
            except asyncio.TimeoutError:
                if task.done() and queue.empty():
                    task_done = True
                # Send keepalive comment
                if not task_done:
                    yield ": keepalive\n\n"

        # Ensure the task completed without error
        try:
            await task
        except Exception as exc:
            logger.exception("Stream orchestration failed")
            yield f"event: error\ndata: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\n\n"

        # Send completion event
        yield f"event: done\ndata: {json.dumps({'jobId': job_id}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/product/copy", response_model=CopyOnlyResponse)
async def product_copy_only(
    request: CopyOnlyRequest,
    settings: Settings = Depends(get_settings),
    provider_factory: ProviderFactory = Depends(get_provider_factory),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> CopyOnlyResponse:
    """Fact preparation plus one platform skill, without research or review.
    """
    product_info = {
        "title": request.product_info.title,
        "category": request.product_info.category,
        "description": request.product_info.description or "",
        "price": request.product_info.price or "",
        "specifications": request.product_info.specifications or "",
        "target_audience": request.product_info.target_audience or "",
        "usage_scenarios": request.product_info.usage_scenarios or "",
    }
    assessment = assess_input_at_boundary(product_info, "copy")
    observation = GenerationObservation("copy", request.target_style, assessment["ready"])
    if not assessment["ready"]:
        return CopyOnlyResponse(
            success=False,
            message="商品信息不足，暂不生成文案",
            input_assessment=assessment,
        )

    try:
        llm_router = LLMRouter(settings)
        agent = CopywriterAgent(
            settings=settings,
            provider_factory=provider_factory,
            llm_router=llm_router,
            retrieval_service=retrieval_service,
        )

        state = {
            "product_info": product_info,
            "target_style": request.target_style,
            "knowledge_base_id": request.knowledge_base_id or "",
            "market_research": {},
        }

        update = await agent.run(state)
        state.update(update)
        style_update = await StyleAdapterAgent(
            settings=settings, provider_factory=provider_factory, llm_router=llm_router,
        ).run(state)
        style_result = style_update["style_previews"]
        copy_result = style_result["draft"]
        observation.finish({"overall_status": "success", "style_adaptation": style_result})

        return CopyOnlyResponse(
            success=True,
            message="已生成平台草稿，请核对后发布",
            titles=copy_result.get("titles", []),
            selling_points=copy_result.get("selling_points", []),
            detail_copy=copy_result.get("detail_copy", ""),
            short_video_script=copy_result.get("short_video_script", ""),
            style=copy_result.get("style", request.target_style),
            pending_confirmations=copy_result.get("pending_confirmations", []),
            input_assessment=assessment,
            platform_skill_id=style_result["platform_skill_id"],
            platform_skill_version=style_result["platform_skill_version"],
            draft=copy_result,
            fallback=style_result["fallback"],
        )
    except Exception as exc:
        logger.exception("Product copy endpoint failed")
        raise HTTPException(status_code=500, detail=f"文案生成失败: {exc}")
    finally:
        observation.finish()


@router.post("/product/review", response_model=ReviewOnlyResponse)
async def product_review_only(
    request: ReviewOnlyRequest,
    settings: Settings = Depends(get_settings),
    provider_factory: ProviderFactory = Depends(get_provider_factory),
) -> ReviewOnlyResponse:
    """Single-agent compliance review endpoint.

    Reviews product information and optional copy content for:
    - Ad law violations
    - Price anomalies
    - Misleading claims
    - Missing information
    """
    try:
        llm_router = LLMRouter(settings)
        agent = ReviewerAgent(
            settings=settings,
            provider_factory=provider_factory,
            llm_router=llm_router,
        )

        copy_drafts = {}
        if request.copy_content:
            copy_drafts = {
                "titles": [request.product_info.title],
                "detail_copy": request.copy_content,
                "selling_points": [],
            }

        state = {
            "product_info": {
                "title": request.product_info.title,
                "category": request.product_info.category,
                "description": request.product_info.description or "",
                "price": request.product_info.price or "",
                "specifications": request.product_info.specifications or "",
                "target_audience": request.product_info.target_audience or "",
                "usage_scenarios": request.product_info.usage_scenarios or "",
            },
            "copy_drafts": copy_drafts,
            "market_research": {},
        }

        update = await agent.run(state)
        review_result = update.get("review_result", {})

        return ReviewOnlyResponse(
            success=True,
            message=f"审查完成，状态：{review_result.get('status', 'unknown')}",
            status=review_result.get("status", "warning"),
            issues=review_result.get("issues", []),
            warnings=review_result.get("warnings", []),
            checklist=review_result.get("checklist", {}),
            summary=review_result.get("summary", ""),
            suggestions=review_result.get("suggestions", []),
        )
    except Exception as exc:
        logger.exception("Product review endpoint failed")
        raise HTTPException(status_code=500, detail=f"审查失败: {exc}")


@router.post("/product/insights", response_model=InsightsResponse)
async def product_insights(
    request: InsightsRequest,
    settings: Settings = Depends(get_settings),
    provider_factory: ProviderFactory = Depends(get_provider_factory),
) -> InsightsResponse:
    """Single-agent market research endpoint.

    Searches market trends, hot keywords, and competitor pricing
    for the given product category.
    """
    try:
        llm_router = LLMRouter(settings)
        agent = MarketResearchAgent(
            settings=settings,
            provider_factory=provider_factory,
            llm_router=llm_router,
        )

        state = {
            "product_info": {
                "title": request.category,
                "category": request.category,
                "description": "",
                "price": "",
            },
        }

        update = await agent.run(state)
        research_result = update.get("market_research", {})

        return InsightsResponse(
            success=True,
            message="市场调研完成",
            category=request.category,
            trends_summary=research_result.get("trends_summary", ""),
            hot_keywords=research_result.get("hot_keywords", []),
            competitor_price_range=research_result.get("competitor_price_range", {}),
            suggestions=research_result.get("suggestions", []),
        )
    except Exception as exc:
        logger.exception("Product insights endpoint failed")
        raise HTTPException(status_code=500, detail=f"市场调研失败: {exc}")


# ---- Style endpoints (separate prefix) ----

styles_router = APIRouter(tags=["styles"])


@styles_router.get("/styles", response_model=StylesListResponse)
async def list_styles() -> StylesListResponse:
    """List available styles with descriptions.

    Returns all supported e-commerce platform styles with their characteristics.
    """
    styles_data = StyleAdapterAgent.get_available_styles()
    styles = [
        StyleInfo(
            id=style_id,
            name=info.get("name", style_id),
            description=info.get("description", ""),
            title_style=info.get("title_style", ""),
            color_scheme=info.get("color_scheme", ""),
            platform_skill_id=info["platform_skill_id"],
            platform_skill_version=info["platform_skill_version"],
        )
        for style_id, info in styles_data.items()
    ]
    return StylesListResponse(styles=styles, total=len(styles))


@styles_router.post("/styles/preview", response_model=StylePreviewResponse)
async def preview_style(
    request: StylePreviewRequest,
    settings: Settings = Depends(get_settings),
    provider_factory: ProviderFactory = Depends(get_provider_factory),
) -> StylePreviewResponse:
    """Preview a product in a specific platform style.

    Adapts the product information and optional existing copy to
    match the target platform's style conventions.
    """
    assessment = assess_input_at_boundary(request.product_info.model_dump(), "preview")
    observation = GenerationObservation("preview", request.target_style, assessment["ready"])
    if not assessment["ready"]:
        raise HTTPException(status_code=422, detail={"input_assessment": assessment})
    try:
        llm_router = LLMRouter(settings)
        agent = StyleAdapterAgent(
            settings=settings,
            provider_factory=provider_factory,
            llm_router=llm_router,
        )

        copy_drafts = request.copy_drafts or {}
        if not copy_drafts:
            # Build minimal copy drafts from product info
            title = request.product_info.title
            copy_drafts = {
                "titles": [title],
                "selling_points": [],
                "detail_copy": request.product_info.description or "",
            }

        state = {
            "product_info": {
                "title": request.product_info.title,
                "category": request.product_info.category,
                "description": request.product_info.description or "",
                "price": request.product_info.price or "",
                "specifications": request.product_info.specifications or "",
                "target_audience": request.product_info.target_audience or "",
                "usage_scenarios": request.product_info.usage_scenarios or "",
            },
            "target_style": request.target_style,
            "copy_drafts": copy_drafts,
        }

        update = await agent.run(state)
        style_result = update.get("style_previews", {})

        profile = STYLE_PROFILES[request.target_style]
        observation.finish({"overall_status": "success", "style_adaptation": style_result})

        return StylePreviewResponse(
            success=True,
            message=f"风格预览完成：{profile['name']}",
            target_style=request.target_style,
            style_name=style_result.get("style_name", profile["name"]),
            adapted_title=style_result.get("adapted_title", ""),
            adapted_selling_points=style_result.get("adapted_selling_points", []),
            adapted_detail=style_result.get("adapted_detail", ""),
            visual_params=style_result.get("visual_params", {}),
            style_notes=style_result.get("style_notes", ""),
            platform_skill_id=style_result["platform_skill_id"],
            platform_skill_version=style_result["platform_skill_version"],
            draft=style_result["draft"],
            pending_confirmations=style_result["pending_confirmations"],
            fallback=style_result["fallback"],
            guarded=style_result["guarded"],
        )
    except Exception as exc:
        logger.exception("Style preview endpoint failed")
        raise HTTPException(status_code=500, detail=f"风格预览失败: {exc}")
    finally:
        observation.finish()


# ---- Search trends endpoint ----

@router.post("/search/trends", response_model=SearchTrendsResponse)
async def search_trends(
    request: SearchTrendsRequest,
    settings: Settings = Depends(get_settings),
    provider_factory: ProviderFactory = Depends(get_provider_factory),
) -> SearchTrendsResponse:
    """Search market trends for a category.

    Uses Tavily web search (with mock fallback) to find:
    - Current market trends
    - Hot search keywords
    - Competitor price ranges
    - Category-specific suggestions
    """
    try:
        search_tool = get_search_tool(
            settings.tavily_api_key,
            settings.qwen_api_key,
            settings.qwen_base_url,
            settings.qwen_chat_model,
        )
        search_results = search_market_trends(
            search_tool=search_tool,
            category=request.category,
            keywords=request.keywords,
        )

        # Use LLM to structure the results
        llm_router = LLMRouter(settings)
        provider_name, model_name = llm_router.route("market_research")

        analysis_prompt = (
            f"请根据以下搜索结果，分析'{request.category}'品类：\n\n"
            f"{search_results}\n\n"
            "请输出 JSON：{{\"trends_summary\": \"...\", \"hot_keywords\": [...], "
            "\"competitor_price_range\": {{\"low\": 0, \"mid\": 0, \"high\": 0, \"currency\": \"CNY\"}}, "
            "\"suggestions\": [...]}}"
        )

        messages = [
            {"role": "system", "content": "你是电商市场分析师。只输出JSON格式的分析结果。"},
            {"role": "user", "content": analysis_prompt},
        ]

        llm_result = provider_factory.chat(
            provider_name=provider_name,
            model_name=model_name,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )

        # Parse the LLM result
        import json
        try:
            content = llm_result.get("content", "{}")
            parsed = json.loads(content) if isinstance(content, str) else content
        except json.JSONDecodeError:
            parsed = {
                "trends_summary": f"关于'{request.category}'的市场分析",
                "hot_keywords": [],
                "competitor_price_range": {"low": 0, "mid": 0, "high": 0, "currency": "CNY"},
                "suggestions": [],
            }

        return SearchTrendsResponse(
            success=True,
            message="趋势搜索完成",
            category=request.category,
            search_results=search_results if isinstance(search_results, str) else str(search_results),
            trends_summary=parsed.get("trends_summary", ""),
            hot_keywords=parsed.get("hot_keywords", []),
            competitor_price_range=parsed.get("competitor_price_range", {}),
            suggestions=parsed.get("suggestions", []),
        )
    except Exception as exc:
        logger.exception("Search trends endpoint failed")
        raise HTTPException(status_code=500, detail=f"趋势搜索失败: {exc}")


# ---- Job status endpoint ----

@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    user_id: Optional[int] = None,
    job_store: JobStore = Depends(get_job_store),
) -> Dict[str, Any]:
    """Get the status of a persistent agent orchestration job.

    Use this endpoint to reconnect to a job after page navigation.
    Returns the full job state including progress, partial results, and final result.
    """
    job = job_store.get_job(job_id, user_id=user_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return job


@router.get("/jobs/active/{user_id}")
async def get_active_job(
    user_id: int,
    job_store: JobStore = Depends(get_job_store),
) -> Dict[str, Any]:
    """Return the current user's most recent running or completed job."""
    job = job_store.get_active_job(user_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Active job not found for user: {user_id}")
    return job


@router.delete("/jobs/{job_id}/consume")
async def consume_job(
    job_id: str,
    user_id: int,
    job_store: JobStore = Depends(get_job_store),
) -> Dict[str, Any]:
    """Consume a completed job after its result has been published."""
    if not job_store.consume_job(job_id, user_id):
        raise HTTPException(status_code=409, detail="Only an owned completed job can be consumed")
    return {"consumed": True, "jobId": job_id}


# ---- Admin/cost endpoints ----

admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.get("/cost-stats", response_model=CostStatsResponse)
async def cost_stats(
    graph: AgentOrchestratorGraph = Depends(get_orchestrator_graph),
) -> CostStatsResponse:
    """Get token usage and cost statistics.

    Returns:
    - Daily and total cost in USD
    - Budget status
    - Cost breakdown by agent type
    - Total API calls
    """
    stats = graph.get_cost_stats()
    return CostStatsResponse(**stats)


@admin_router.post("/cost-stats/reset")
async def reset_cost_stats(
    graph: AgentOrchestratorGraph = Depends(get_orchestrator_graph),
) -> Dict[str, Any]:
    """Reset cost tracking statistics."""
    graph.cost_tracker.reset()
    return {"success": True, "message": "成本统计已重置"}


@admin_router.post("/rag/evaluate", response_model=RAGEvaluateResponse)
async def evaluate_rag_quality(
    request: RAGEvaluateRequest,
    settings: Settings = Depends(get_settings),
    provider_factory: ProviderFactory = Depends(get_provider_factory),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    graph: AgentOrchestratorGraph = Depends(get_orchestrator_graph),
) -> RAGEvaluateResponse:
    """Evaluate RAG retrieval quality using LLM-as-Judge.

    Runs retrieval for the given query against the specified knowledge base,
    then scores each retrieved document's relevance (1-5 scale) using an LLM.

    Returns standard IR metrics:
    - hit_rate: fraction of results with relevance >= 3
    - mrr: mean reciprocal rank of first relevant result
    - ndcg: normalized discounted cumulative gain
    - precision_at_k: precision among top-k results
    - avg_relevance: average relevance score across all results
    """
    try:
        metrics = await retrieval_service.evaluate_quality(
            query=request.query,
            knowledge_base_id=request.knowledge_base_id,
            top_k=request.top_k or 5,
            provider_factory=provider_factory,
            cost_tracker=graph.cost_tracker,
        )

        return RAGEvaluateResponse(
            success=True,
            message=(
                f"RAG质量评估完成：命中率 {metrics.hit_rate:.1%}，"
                f"平均相关性 {metrics.avg_relevance:.1f}/5，"
                f"MRR {metrics.mrr:.3f}"
            ),
            query=metrics.query,
            knowledge_base_id=metrics.knowledge_base_id,
            total_retrieved=metrics.total_retrieved,
            avg_relevance=metrics.avg_relevance,
            hit_rate=metrics.hit_rate,
            mrr=metrics.mrr,
            ndcg=metrics.ndcg,
            precision_at_k=metrics.precision_at_k,
            judgments=metrics.judgments,
        )
    except Exception as exc:
        logger.exception("RAG quality evaluation failed")
        raise HTTPException(status_code=500, detail=f"RAG质量评估失败: {exc}")
