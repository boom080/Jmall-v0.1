"""LangGraph StateGraph for multi-agent orchestration.

Graph structure (corrected data dependencies):

    START -> parse_intent
               |
         ┌─────┴─────────┐  (parallel: both are independent)
         ▼                 ▼
    market_research    rag_retrieval
         │                 │
         └─────┬───────────┘
               ▼
        join_research_rag
               │
               ▼
        copy_generation    (consumes market_research + rag_context)
               │
               ▼
        compliance_review
               │
               ▼
        style_adaptation
               │
               ▼
        aggregate_results -> END

Key design decisions:
- market_research and rag_retrieval run in parallel (no inter-dependency)
- copy_generation runs AFTER both, ensuring it has the current market_research
  and rag_context results
- Conditional edges handle errors and missing knowledge bases gracefully
"""

import logging
import operator
import time
from contextvars import ContextVar
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.types import Send

from app.agents.copywriter import CopywriterAgent
from app.agents.market_research import MarketResearchAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.style_adapter import StyleAdapterAgent
from app.core.config import Settings
from app.llm.cost_tracker import CostTracker
from app.llm.router import LLMRouter
from app.providers.factory import ProviderFactory
from app.retrieval.rag_retriever import assess_rag_quality
from app.retrieval.service import RetrievalService

logger = logging.getLogger(__name__)


# Reducer for simple values in parallel fan-out — takes the last non-None value
def _last_wins(a, b):
    """Reducer: return b if b is not None, else a."""
    return b if b is not None else a


class AgentGraphState(TypedDict, total=False):
    """State type for the agent orchestration graph.

    Uses Annotated keys so LangGraph's Send API fan-out can correctly
    merge state updates from parallel branches.
    """

    user_request: Annotated[str, _last_wins]
    product_info: Annotated[dict, _last_wins]
    target_style: Annotated[str, _last_wins]
    knowledge_base_id: Annotated[str, _last_wins]
    # Intermediate results
    orchestration_plan: Annotated[Optional[dict], _last_wins]
    market_research: Annotated[Optional[dict], _last_wins]
    rag_context: Annotated[Optional[str], _last_wins]       # Pre-retrieved RAG context
    rag_quality: Annotated[Optional[dict], _last_wins]      # Simple RAG quality assessment
    copy_drafts: Annotated[Optional[dict], _last_wins]
    review_result: Annotated[Optional[dict], _last_wins]
    style_previews: Annotated[Optional[dict], _last_wins]
    # Final output
    final_result: Annotated[Optional[dict], _last_wins]
    cost_stats: Annotated[Optional[dict], _last_wins]
    errors: Annotated[List[str], operator.add]


class AgentOrchestratorGraph:
    """LangGraph-based multi-agent orchestration system.

    Coordinates multiple specialized agents to handle e-commerce tasks:
    1. OrchestratorAgent: Plan decomposition
    2. MarketResearchAgent: Market trend analysis (with LLM tool calling)
    3. RAG Retrieval: Knowledge base document retrieval (parallel with #2)
    4. CopywriterAgent: Copy generation (consumes #2 + #3)
    5. ReviewerAgent: Compliance review
    6. StyleAdapterAgent: Platform style adaptation
    """

    def __init__(
        self,
        settings: Settings,
        provider_factory: ProviderFactory,
        retrieval_service: Optional[RetrievalService] = None,
    ) -> None:
        self.settings = settings
        self.provider_factory = provider_factory
        self.retrieval_service = retrieval_service

        # Initialize shared services
        self.llm_router = LLMRouter(settings)
        self.cost_tracker = CostTracker(settings)

        # Initialize agents (lazy - they're recreated per graph build)
        self._orchestrator: Optional[OrchestratorAgent] = None
        self._market_research: Optional[MarketResearchAgent] = None
        self._copywriter: Optional[CopywriterAgent] = None
        self._reviewer: Optional[ReviewerAgent] = None
        self._style_adapter: Optional[StyleAdapterAgent] = None

        # Context-local callback keeps concurrent invocations on this singleton isolated.
        self._progress_callback: ContextVar[Optional[callable]] = ContextVar(
            "agent_progress_callback",
            default=None,
        )

        self.graph = self._build_graph()

    def _get_orchestrator(self) -> OrchestratorAgent:
        if self._orchestrator is None:
            self._orchestrator = OrchestratorAgent(
                settings=self.settings,
                provider_factory=self.provider_factory,
                llm_router=self.llm_router,
                cost_tracker=self.cost_tracker,
            )
        return self._orchestrator

    def _get_market_research(self) -> MarketResearchAgent:
        if self._market_research is None:
            self._market_research = MarketResearchAgent(
                settings=self.settings,
                provider_factory=self.provider_factory,
                llm_router=self.llm_router,
                cost_tracker=self.cost_tracker,
            )
        return self._market_research

    def _get_copywriter(self) -> CopywriterAgent:
        if self._copywriter is None:
            self._copywriter = CopywriterAgent(
                settings=self.settings,
                provider_factory=self.provider_factory,
                llm_router=self.llm_router,
                cost_tracker=self.cost_tracker,
                retrieval_service=self.retrieval_service,
            )
        return self._copywriter

    def _get_reviewer(self) -> ReviewerAgent:
        if self._reviewer is None:
            self._reviewer = ReviewerAgent(
                settings=self.settings,
                provider_factory=self.provider_factory,
                llm_router=self.llm_router,
                cost_tracker=self.cost_tracker,
            )
        return self._reviewer

    def _get_style_adapter(self) -> StyleAdapterAgent:
        if self._style_adapter is None:
            self._style_adapter = StyleAdapterAgent(
                settings=self.settings,
                provider_factory=self.provider_factory,
                llm_router=self.llm_router,
                cost_tracker=self.cost_tracker,
            )
        return self._style_adapter

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph StateGraph for multi-agent orchestration.

        Graph structure (corrected for data dependencies):
            START -> parse_intent
                       |
                 ┌─────┴─────────┐  (parallel)
                 ▼                 ▼
            market_research    rag_retrieval
                 │                 │
                 └─────┬───────────┘
                       ▼
                join_research_rag
                       │
                       ▼
                copy_generation  (has market_research + rag_context)
                       │
                       ▼
                compliance_review -> style_adaptation -> aggregate_results -> END
        """
        graph = StateGraph(AgentGraphState)

        # Add nodes
        graph.add_node("parse_intent", self._parse_intent)
        graph.add_node("node_market_research", self._run_market_research)
        graph.add_node("rag_retrieval", self._run_rag_retrieval)
        graph.add_node("join_research_rag", self._join_research_rag)
        graph.add_node("copy_generation", self._run_copy_generation)
        graph.add_node("compliance_review", self._run_compliance_review)
        graph.add_node("style_adaptation", self._run_style_adaptation)
        graph.add_node("aggregate_results", self._aggregate_results)

        # Set entry point
        graph.set_entry_point("parse_intent")

        # Fan-out from parse_intent to market_research + rag_retrieval (parallel)
        graph.add_conditional_edges(
            "parse_intent",
            self._after_parse_intent,
            ["node_market_research", "rag_retrieval", "copy_generation", "aggregate_results"],
        )

        # Both parallel branches converge at join_research_rag
        graph.add_edge("node_market_research", "join_research_rag")
        graph.add_edge("rag_retrieval", "join_research_rag")

        # Join → copy_generation (sequential: copywriter needs both research + rag)
        graph.add_conditional_edges(
            "join_research_rag",
            self._after_join,
            {
                "copy_generation": "copy_generation",
                "aggregate_results": "aggregate_results",
            },
        )

        # copy_generation → compliance_review (or aggregate on error)
        graph.add_conditional_edges(
            "copy_generation",
            self._after_copy_generation,
            {
                "compliance_review": "compliance_review",
                "aggregate_results": "aggregate_results",
            },
        )

        # compliance_review → style_adaptation
        graph.add_conditional_edges(
            "compliance_review",
            self._after_compliance_review,
            {
                "style_adaptation": "style_adaptation",
                "aggregate_results": "aggregate_results",
            },
        )

        graph.add_edge("style_adaptation", "aggregate_results")
        graph.add_edge("aggregate_results", END)

        return graph.compile()

    async def invoke(
        self,
        state: AgentGraphState,
        progress_callback: Optional[callable] = None,
    ) -> dict:
        """Execute the full orchestration graph.

        Args:
            state: Initial state with user_request, product_info, target_style, etc.
            progress_callback: Optional async callback(agent_name, status, result_dict)
                called after each agent node completes, for SSE streaming.

        Returns:
            Complete state dict with all agent results and final_result
        """
        logger.info(
            "AgentOrchestratorGraph: starting orchestration for '%s'",
            state.get("product_info", {}).get("title", "unknown"),
        )

        # Ensure defaults
        state.setdefault("errors", [])
        state.setdefault("knowledge_base_id", "")
        state.setdefault("target_style", "taobao")
        state.setdefault("user_request", "")

        callback_token = self._progress_callback.set(progress_callback)
        cost_scope_id, cost_scope_token = self.cost_tracker.begin_scope()

        try:
            result = await self.graph.ainvoke(state)
            logger.info("AgentOrchestratorGraph: orchestration complete")
            cost_stats = self.cost_tracker.get_stats(cost_scope_id)
            result["cost_stats"] = cost_stats

            # Notify completion
            if progress_callback:
                try:
                    final = result.get("final_result", {})
                    await progress_callback("orchestration_complete", "completed", {
                        "final_result": final,
                        "cost_stats": cost_stats,
                    })
                except Exception:
                    logger.debug("Progress callback failed on completion", exc_info=True)

            return result
        except Exception as exc:
            logger.error("AgentOrchestratorGraph: orchestration failed: %s", exc)
            errors = state.get("errors", [])
            errors.append(f"Orchestration failed: {exc}")
            state["errors"] = errors
            # Notify error
            if progress_callback:
                try:
                    await progress_callback("error", "error", {"error": str(exc)})
                except Exception:
                    pass
            # Try to aggregate whatever results we have
            orchestrator = self._get_orchestrator()
            state["final_result"] = orchestrator.aggregate_results(state)
            state["cost_stats"] = self.cost_tracker.get_stats(cost_scope_id)
            return state
        finally:
            self.cost_tracker.end_scope(cost_scope_token)
            self._progress_callback.reset(callback_token)

    # ---- Graph node implementations ----

    async def _notify_progress(
        self,
        state: AgentGraphState,
        agent_name: str,
        result: dict,
        extra: Optional[dict] = None,
        status: str = "completed",
    ) -> None:
        """Call the progress callback if set (stored on instance, not in LangGraph state)."""
        cb = self._progress_callback.get()
        if cb:
            try:
                payload = dict(result)
                if extra:
                    payload.update(extra)
                await cb(agent_name, status, payload)
            except Exception:
                logger.debug("Progress callback failed for %s", agent_name, exc_info=True)

    async def _parse_intent(self, state: AgentGraphState) -> AgentGraphState:
        """Parse user intent and create execution plan."""
        t0 = time.monotonic()
        logger.info("Graph node: parse_intent")
        try:
            orchestrator = self._get_orchestrator()
            update = await orchestrator.run(dict(state))
            state.update(update)
            elapsed = time.monotonic() - t0
            plan = state.get("orchestration_plan", {})
            progress_status = "error" if plan.get("fallback") else "completed"
            if plan.get("fallback"):
                state["errors"] = [
                    *state.get("errors", []),
                    f"parse_intent: {plan.get('error', '模型规划失败')}",
                ]
            logger.info("parse_intent completed in %.2fs", elapsed)
            await self._notify_progress(state, "parse_intent", {
                "plan": plan,
                "elapsed_ms": int(elapsed * 1000),
            }, status=progress_status)
        except Exception as exc:
            elapsed = time.monotonic() - t0
            logger.error("parse_intent failed after %.2fs: %s", elapsed, exc)
            errors: List[str] = state.get("errors", [])
            errors.append(f"parse_intent: {exc}")
            state["errors"] = errors
            # Fallback: build a default plan so downstream nodes can proceed
            try:
                orchestrator = self._get_orchestrator()
                plan = orchestrator._build_default_plan(state.get("knowledge_base_id", ""))
                state["orchestration_plan"] = {
                    "plan": plan,
                    "reasoning": "parse_intent LLM call failed, using default plan",
                    "expected_output": "标准的电商文案交付物",
                    "target_style": state.get("target_style", "taobao"),
                    "knowledge_base_available": bool(state.get("knowledge_base_id")),
                    "fallback": True,
                }
                logger.info("parse_intent: used fallback default plan (%d steps)", len(plan))
                await self._notify_progress(state, "parse_intent", {
                    "plan": state["orchestration_plan"],
                    "elapsed_ms": int(elapsed * 1000),
                    "fallback": True,
                })
            except Exception as fallback_exc:
                logger.error("parse_intent fallback also failed: %s", fallback_exc)
        return state

    async def _run_market_research(self, state: AgentGraphState) -> AgentGraphState:
        """Execute market research agent (with LLM tool calling)."""
        t0 = time.monotonic()
        logger.info("Graph node: market_research")
        try:
            agent = self._get_market_research()
            update = await agent.run(dict(state))
            state.update(update)
            mr = state.get("market_research", {})
            elapsed = time.monotonic() - t0
            progress_status = "error" if mr.get("status") == "failed" else "completed"
            if mr.get("status") == "failed":
                state["errors"] = [
                    *state.get("errors", []),
                    f"market_research: {mr.get('error', '搜索服务不可用')}",
                ]
            logger.info("market_research completed in %.2fs", elapsed)
            await self._notify_progress(state, "market_research", {
                "market_insights": mr,
                "method": mr.get("method", "unknown"),
                "tool_calls": mr.get("tool_calls", []),
                "elapsed_ms": int(elapsed * 1000),
            }, status=progress_status)
        except Exception as exc:
            logger.error("market_research failed: %s", exc)
            errors: List[str] = state.get("errors", [])
            errors.append(f"market_research: {exc}")
            state["errors"] = errors
            state["market_research"] = {
                "trends_summary": f"市场调研暂时不可用（{exc}）",
                "hot_keywords": [],
                "competitor_price_range": {"low": 0, "mid": 0, "high": 0, "currency": "CNY"},
                "suggestions": ["请稍后重试市场调研"],
                "error": str(exc),
            }
        return state

    async def _run_rag_retrieval(self, state: AgentGraphState) -> AgentGraphState:
        """Pre-retrieve RAG context for the copywriter.

        Runs in parallel with market_research. If no knowledge_base_id is
        configured, this is a no-op.  Stores a simple quality assessment
        in ``rag_quality`` for downstream observability.
        """
        t0 = time.monotonic()
        logger.info("Graph node: rag_retrieval")
        kb_id = state.get("knowledge_base_id", "")
        if not kb_id or not self.retrieval_service:
            state["rag_context"] = ""
            state["rag_quality"] = {"quality": "empty", "top1_score": 0.0, "avg_score": 0.0, "result_count": 0}
            logger.info("rag_retrieval: skipped (no kb_id or retrieval_service)")
            await self._notify_progress(state, "rag_retrieval", {
                "rag_context": {"chunk_count": 0, "knowledge_base_id": kb_id},
                "rag_quality": state["rag_quality"],
                "skipped": True,
            })
            return state

        try:
            product_info = state.get("product_info", {})
            title = product_info.get("title", "")
            category = product_info.get("category", "")
            query = f"{title} {category}".strip()
            if not query:
                state["rag_context"] = ""
                state["rag_quality"] = {"quality": "empty", "top1_score": 0.0, "avg_score": 0.0, "result_count": 0}
                return state

            chunks = self.retrieval_service.retrieve(
                kb_id, query,
                top_k=self.settings.rag_top_k or 4,
            )

            # Simple quality assessment (no extra LLM calls)
            state["rag_quality"] = assess_rag_quality(chunks)

            if not chunks:
                state["rag_context"] = ""
                logger.info("rag_retrieval: no chunks found (quality=%s)", state["rag_quality"]["quality"])
                await self._notify_progress(state, "rag_retrieval", {
                    "rag_context": {"chunk_count": 0, "knowledge_base_id": kb_id},
                    "rag_quality": state["rag_quality"],
                })
                return state

            # Format as context string
            lines = ["【知识库参考资料】"]
            for i, chunk in enumerate(chunks, 1):
                content = chunk.get("content", "")
                source = chunk.get("sourceFilename", "未知来源")
                score = float(chunk.get("score", 0))
                lines.append(f"{i}. 来源：{source}（相关度：{score:.2f}）\n{content}")
            rag_text = "\n\n".join(lines)

            state["rag_context"] = rag_text
            await self._notify_progress(state, "rag_retrieval", {
                "rag_context": {
                    "chunk_count": len(chunks),
                    "knowledge_base_id": kb_id,
                },
                "rag_quality": state["rag_quality"],
            })
            elapsed = time.monotonic() - t0
            logger.info("rag_retrieval: retrieved %d chunks in %.2fs (quality=%s)", len(chunks), elapsed, state["rag_quality"]["quality"])
        except Exception as exc:
            elapsed = time.monotonic() - t0
            logger.warning("rag_retrieval failed after %.2fs: %s", elapsed, exc)
            state["rag_context"] = ""
            state["rag_quality"] = {"quality": "empty", "top1_score": 0.0, "avg_score": 0.0, "result_count": 0}
        return state

    async def _run_copy_generation(self, state: AgentGraphState) -> AgentGraphState:
        """Execute copy generation agent.

        Now runs AFTER market_research and rag_retrieval complete,
        so it has access to both results.
        """
        t0 = time.monotonic()
        logger.info("Graph node: copy_generation")
        try:
            agent = self._get_copywriter()
            update = await agent.run(dict(state))
            state.update(update)
            elapsed = time.monotonic() - t0
            copy_drafts = state.get("copy_drafts", {})
            progress_status = "error" if copy_drafts.get("fallback") else "completed"
            if copy_drafts.get("fallback"):
                state["errors"] = [
                    *state.get("errors", []),
                    f"copy_generation: {copy_drafts.get('error', '模型生成失败')}",
                ]
            logger.info("copy_generation completed in %.2fs", elapsed)
            await self._notify_progress(state, "copy_generation", {
                "style_previews": copy_drafts,
                "elapsed_ms": int(elapsed * 1000),
            }, status=progress_status)
        except Exception as exc:
            elapsed = time.monotonic() - t0
            logger.error("copy_generation failed after %.2fs: %s", elapsed, exc)
            errors: List[str] = state.get("errors", [])
            errors.append(f"copy_generation: {exc}")
            state["errors"] = errors
            title = state.get("product_info", {}).get("title", "商品")
            state["copy_drafts"] = {
                "titles": [f"【品质推荐】{title}"],
                "selling_points": ["品质优选", "值得信赖"],
                "detail_copy": f"商品文案生成失败（{exc}），请稍后重试。",
                "short_video_script": "",
                "pending_confirmations": ["请商家确认商品详情"],
                "style": state.get("target_style", "taobao"),
                "rag_used": False,
                "market_context_used": False,
            }
        return state

    async def _run_compliance_review(self, state: AgentGraphState) -> AgentGraphState:
        """Execute compliance review agent."""
        t0 = time.monotonic()
        logger.info("Graph node: compliance_review")
        try:
            agent = self._get_reviewer()
            update = await agent.run(dict(state))
            state.update(update)
            elapsed = time.monotonic() - t0
            review = state.get("review_result", {})
            progress_status = "error" if review.get("fallback") else "completed"
            if review.get("fallback"):
                state["errors"] = [
                    *state.get("errors", []),
                    f"compliance_review: {review.get('error', '模型审查失败')}",
                ]
            logger.info("compliance_review completed in %.2fs", elapsed)
            await self._notify_progress(state, "compliance_review", {
                "compliance_result": review,
                "elapsed_ms": int(elapsed * 1000),
            }, status=progress_status)
        except Exception as exc:
            elapsed = time.monotonic() - t0
            logger.error("compliance_review failed after %.2fs: %s", elapsed, exc)
            errors: List[str] = state.get("errors", [])
            errors.append(f"compliance_review: {exc}")
            state["errors"] = errors
            state["review_result"] = {
                "status": "warning",
                "warnings": [f"合规审查暂时不可用（{exc}），建议人工审查"],
                "issues": [],
                "checklist": {"error": str(exc)},
                "summary": "合规审查服务暂时不可用，请人工审查后再发布。",
                "suggestions": ["请进行人工合规审查"],
            }
        return state

    async def _run_style_adaptation(self, state: AgentGraphState) -> AgentGraphState:
        """Execute style adaptation agent."""
        t0 = time.monotonic()
        logger.info("Graph node: style_adaptation")
        try:
            agent = self._get_style_adapter()
            update = await agent.run(dict(state))
            state.update(update)
            elapsed = time.monotonic() - t0
            style_previews = state.get("style_previews", {})
            progress_status = "error" if style_previews.get("fallback") else "completed"
            if style_previews.get("fallback"):
                state["errors"] = [
                    *state.get("errors", []),
                    f"style_adaptation: {style_previews.get('error', '模型适配失败')}",
                ]
            logger.info("style_adaptation completed in %.2fs", elapsed)
            await self._notify_progress(state, "style_adaptation", {
                "style_previews": style_previews,
                "elapsed_ms": int(elapsed * 1000),
            }, status=progress_status)
        except Exception as exc:
            elapsed = time.monotonic() - t0
            logger.error("style_adaptation failed after %.2fs: %s", elapsed, exc)
            errors: List[str] = state.get("errors", [])
            errors.append(f"style_adaptation: {exc}")
            state["errors"] = errors
            copy_drafts = state.get("copy_drafts", {})
            state["style_previews"] = {
                "target_style": state.get("target_style", "taobao"),
                "style_name": "默认风格",
                "adapted_title": copy_drafts.get("titles", [""])[0] if copy_drafts.get("titles") else "",
                "adapted_selling_points": copy_drafts.get("selling_points", []),
                "adapted_detail": copy_drafts.get("detail_copy", ""),
                "visual_params": {"color_scheme": "default", "layout": "standard", "font_style": "standard"},
                "style_notes": f"风格适配暂时不可用（{exc}）",
            }
        return state

    async def _aggregate_results(self, state: AgentGraphState) -> AgentGraphState:
        """Aggregate all agent results into final output."""
        t0 = time.monotonic()
        logger.info("Graph node: aggregate_results")
        try:
            orchestrator = self._get_orchestrator()
            final_result = orchestrator.aggregate_results(dict(state))
            state["final_result"] = final_result
            elapsed = time.monotonic() - t0
            logger.info("aggregate_results completed in %.2fs", elapsed)
        except Exception as exc:
            elapsed = time.monotonic() - t0
            logger.error("aggregate_results failed after %.2fs: %s", elapsed, exc)
            errors: List[str] = state.get("errors", [])
            errors.append(f"aggregate_results: {exc}")
            state["errors"] = errors
            state["final_result"] = {
                "overall_status": "error",
                "error": str(exc),
                "errors": errors,
            }
        return state

    # ---- Conditional edge functions ----

    def _after_parse_intent(self, state: AgentGraphState):
        """Fan out to market_research and rag_retrieval in parallel.

        Uses LangGraph's Send API to execute both agents concurrently.
        On critical parse_intent error, routes directly to aggregate_results.
        """
        if not state.get("orchestration_plan"):
            return ["aggregate_results"]
        # Fan out: both agents receive a copy of the state and run in parallel
        return [
            Send("node_market_research", dict(state)),
            Send("rag_retrieval", dict(state)),
        ]

    def _after_join(self, state: AgentGraphState) -> str:
        """After both market_research and rag_retrieval complete.

        Both provide fallback results on error, so we always proceed
        to copy_generation unless something fatal occurred.
        """
        errors = state.get("errors", [])
        fatal = all(
            "market_research" in str(e) and "rag_retrieval" in str(e)
            for e in errors
        ) if errors else False
        if fatal:
            logger.warning("Both parallel agents failed, aggregating partial results")
            return "aggregate_results"
        return "copy_generation"

    def _after_copy_generation(self, state: AgentGraphState) -> str:
        """After copy generation: proceed to compliance review."""
        copy_drafts = state.get("copy_drafts", {})
        if not copy_drafts or not copy_drafts.get("titles"):
            logger.warning("Copy generation produced no titles, but continuing")
        return "compliance_review"

    def _after_compliance_review(self, state: AgentGraphState) -> str:
        """After compliance review: proceed to style adaptation."""
        review = state.get("review_result", {})
        if review.get("status") == "rejected":
            logger.warning("Compliance review rejected, but continuing to style adaptation")
        return "style_adaptation"

    # ---- Join node ----

    async def _join_research_rag(self, state: AgentGraphState) -> AgentGraphState:
        """Join point after parallel market_research and rag_retrieval.

        LangGraph automatically merges state updates from fan-out branches.
        This is a pass-through logging node.
        """
        mr = state.get("market_research", {})
        rag = state.get("rag_context", "")
        logger.info(
            "Graph node: join_research_rag (market=%s, rag=%d chars)",
            "present" if mr else "absent",
            len(rag) if rag else 0,
        )
        return state

    # ---- Public helpers ----

    def get_cost_stats(self) -> dict:
        """Get current cost tracking statistics."""
        return self.cost_tracker.get_stats()

    def get_agent_status(self) -> dict:
        """Get the status of all agents in the system."""
        return {
            "orchestrator": self._orchestrator is not None,
            "market_research": self._market_research is not None,
            "copywriter": self._copywriter is not None,
            "reviewer": self._reviewer is not None,
            "style_adapter": self._style_adapter is not None,
        }
