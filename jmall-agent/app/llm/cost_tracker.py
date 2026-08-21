"""Tracks LLM token usage and costs across all agent invocations."""

import logging
import time
import uuid
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.config import Settings
from app.core.metrics import record_llm_call, update_budget_gauges

logger = logging.getLogger(__name__)

# Pricing per 1M tokens (USD).  Qwen's Beijing-region tariffs are published in
# CNY, so they are converted here at a deliberately explicit estimate.  This
# powers an observability estimate, not the provider invoice; free quota and
# promotions can make the actual billed amount lower (including zero).
ESTIMATED_CNY_PER_USD = 7.20
DEFAULT_PRICING: Dict[str, Dict[str, float]] = {
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    "qwen-plus": {"input": 0.80 / ESTIMATED_CNY_PER_USD, "output": 2.00 / ESTIMATED_CNY_PER_USD},
    "qwen-max": {"input": 2.40 / ESTIMATED_CNY_PER_USD, "output": 9.60 / ESTIMATED_CNY_PER_USD},
    "qwen-turbo": {"input": 0.30 / ESTIMATED_CNY_PER_USD, "output": 0.60 / ESTIMATED_CNY_PER_USD},
    "mock": {"input": 0.0, "output": 0.0},
    "mock-product-copy-v1": {"input": 0.0, "output": 0.0},
}


class TokenUsage:
    """A single tracked usage record."""

    def __init__(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        agent_type: str = "",
        scope_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.agent_type = agent_type
        self.scope_id = scope_id
        self.timestamp = timestamp or datetime.now(timezone.utc)

    @property
    def cost_usd(self) -> float:
        pricing = DEFAULT_PRICING.get(self.model, DEFAULT_PRICING.get("mock", {"input": 0.0, "output": 0.0}))
        input_cost = (self.input_tokens / 1_000_000) * pricing.get("input", 0.0)
        output_cost = (self.output_tokens / 1_000_000) * pricing.get("output", 0.0)
        return round(input_cost + output_cost, 8)


class CostTracker:
    """Tracks LLM token usage and costs with daily budget awareness."""

    PRICING = DEFAULT_PRICING

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._records: List[TokenUsage] = []
        self.enabled = settings.cost_tracking_enabled
        self._scope_id: ContextVar[Optional[str]] = ContextVar(
            "cost_tracking_scope_id",
            default=None,
        )

    def begin_scope(self) -> tuple[str, Token]:
        """Start a context-local request scope and return its reset token."""
        scope_id = uuid.uuid4().hex
        return scope_id, self._scope_id.set(scope_id)

    def end_scope(self, token: Token) -> None:
        """Restore the previous context after a request scope ends."""
        self._scope_id.reset(token)

    def track(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        agent_type: str = "",
        duration_seconds: float = 0.0,
    ) -> TokenUsage:
        """Record a usage entry and return it."""
        if not self.enabled:
            return TokenUsage(provider, model, 0, 0, agent_type, self._scope_id.get())
        record = TokenUsage(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            agent_type=agent_type,
            scope_id=self._scope_id.get(),
        )
        self._records.append(record)
        logger.info(
            "Cost tracked: %s/%s in=%d out=%d cost=$%.6f agent=%s",
            provider, model, input_tokens, output_tokens, record.cost_usd, agent_type,
        )

        # Update Prometheus metrics
        try:
            record_llm_call(
                agent_type=agent_type,
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=record.cost_usd,
                duration_seconds=duration_seconds,
            )
        except Exception:
            logger.debug("Failed to record Prometheus metrics", exc_info=True)

        if self.is_over_budget():
            logger.warning(
                "Daily cost budget exceeded: $%.2f / $%.2f",
                self.get_daily_cost(),
                self.settings.agent_cost_budget_daily,
            )

        # Update budget gauges periodically
        try:
            update_budget_gauges(
                daily_cost=self.get_daily_cost(),
                budget=self.settings.agent_cost_budget_daily,
                over_budget=self.is_over_budget(),
            )
        except Exception:
            logger.debug("Failed to update budget gauges", exc_info=True)

        return record

    def get_daily_cost(self) -> float:
        """Total cost for today (UTC)."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        daily = sum(
            r.cost_usd for r in self._records
            if r.timestamp and r.timestamp >= today_start
        )
        return round(daily, 6)

    def get_total_cost(self) -> float:
        """Total cost across all time."""
        return round(sum(r.cost_usd for r in self._records), 6)

    def is_over_budget(self) -> bool:
        """Check if daily budget is exceeded."""
        return self.get_daily_cost() > self.settings.agent_cost_budget_daily

    def get_stats(self, scope_id: Optional[str] = None) -> dict:
        """Return global statistics or statistics for one orchestration scope."""
        records = [r for r in self._records if scope_id is None or r.scope_id == scope_id]
        daily = self.get_daily_cost()
        total = round(sum(r.cost_usd for r in records), 6)
        by_agent: Dict[str, float] = {}
        tokens_by_agent: Dict[str, Dict[str, Any]] = {}
        for r in records:
            key = r.agent_type or "unknown"
            by_agent[key] = round(by_agent.get(key, 0.0) + r.cost_usd, 6)
            detail = tokens_by_agent.setdefault(key, {
                "calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "cost_usd": 0.0,
            })
            detail["calls"] += 1
            detail["input_tokens"] += r.input_tokens
            detail["output_tokens"] += r.output_tokens
            detail["total_tokens"] += r.input_tokens + r.output_tokens
            detail["cost_usd"] = round(detail["cost_usd"] + r.cost_usd, 8)
        return {
            "daily_cost_usd": daily,
            "total_cost_usd": total,
            "budget_daily_usd": self.settings.agent_cost_budget_daily,
            "over_budget": daily > self.settings.agent_cost_budget_daily,
            "total_calls": len(records),
            "total_input_tokens": sum(r.input_tokens for r in records),
            "total_output_tokens": sum(r.output_tokens for r in records),
            "total_tokens": sum(r.input_tokens + r.output_tokens for r in records),
            "cost_by_agent": by_agent,
            "tokens_by_agent": tokens_by_agent,
            "scope_id": scope_id,
            "cost_basis": "estimated_public_list_price_before_free_quota",
            "tracking_enabled": self.enabled,
        }

    def reset(self) -> None:
        """Clear all records."""
        self._records.clear()
