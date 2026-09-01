"""Prometheus metrics for agent observability.

Exposes:
- agent_requests_total: Counter of LLM requests by agent_type, provider, model
- agent_tokens_total: Counter of tokens consumed by direction (input/output)
- agent_cost_daily_usd: Gauge of today's cost
- agent_cost_total_usd: Counter of all-time cost
- agent_request_duration_seconds: Histogram of request latency
"""

from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, generate_latest

REGISTRY = CollectorRegistry(auto_describe=True)

# Counters
agent_requests_total = Counter(
    "agent_requests_total",
    "Total number of LLM API calls",
    labelnames=["agent_type", "provider", "model"],
    registry=REGISTRY,
)

agent_tokens_total = Counter(
    "agent_tokens_total",
    "Total tokens consumed",
    labelnames=["agent_type", "direction"],
    registry=REGISTRY,
)

agent_cost_total_usd = Counter(
    "agent_cost_total_usd",
    "Cumulative cost in USD",
    labelnames=["agent_type"],
    registry=REGISTRY,
)

# Gauges
agent_cost_daily_usd = Gauge(
    "agent_cost_daily_usd",
    "Today's total cost in USD",
    registry=REGISTRY,
)

agent_budget_daily_usd = Gauge(
    "agent_budget_daily_usd",
    "Configured daily cost budget in USD",
    registry=REGISTRY,
)

agent_over_budget = Gauge(
    "agent_over_budget",
    "Whether daily cost budget is exceeded (1=yes, 0=no)",
    registry=REGISTRY,
)

# Histograms
agent_request_duration_seconds = Histogram(
    "agent_request_duration_seconds",
    "LLM API call latency",
    labelnames=["agent_type", "provider"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0],
    registry=REGISTRY,
)

image_search_requests_total = Counter(
    "image_search_requests_total",
    "Total number of Image Scout searches",
    labelnames=["provider", "status"],
    registry=REGISTRY,
)

image_search_duration_seconds = Histogram(
    "image_search_duration_seconds",
    "Image Scout provider latency",
    labelnames=["provider"],
    buckets=[0.25, 0.5, 1.0, 2.0, 4.0, 6.0, 8.0, 12.0],
    registry=REGISTRY,
)

image_search_candidates_total = Counter(
    "image_search_candidates_total",
    "Total number of image candidates returned to merchants",
    labelnames=["provider"],
    registry=REGISTRY,
)

# Product metrics use bounded labels only; no merchant text, IDs or URLs.
input_assessments_total = Counter(
    "jmall_input_assessments_total", "Deterministic input checks, not unique users",
    ["entrypoint", "outcome"], registry=REGISTRY,
)
input_assessment_duration = Histogram(
    "jmall_input_assessment_duration_seconds", "Model-free input check latency",
    ["entrypoint"], buckets=[.001, .005, .01, .05, .1, .2, .3, .5, 1], registry=REGISTRY,
)
generation_runs_total = Counter(
    "jmall_generation_runs_total", "Generation runs by start or terminal outcome",
    ["entrypoint", "platform", "outcome"], registry=REGISTRY,
)
generation_duration = Histogram(
    "jmall_generation_duration_seconds", "Full generation duration excluding rejected inputs",
    ["entrypoint", "platform"], buckets=[1, 3, 5, 10, 30, 60, 120, 300, 600], registry=REGISTRY,
)
generation_first_progress = Histogram(
    "jmall_generation_first_progress_seconds", "Time to first delivered graph progress callback",
    ["platform"], buckets=[.01, .1, .5, 1, 2, 3, 5, 10], registry=REGISTRY,
)
platform_drafts_total = Counter(
    "jmall_platform_drafts_total", "Delivered drafts with skill traceability and fallback state",
    ["platform", "metadata", "fallback"], registry=REGISTRY,
)


def record_input_assessment(entrypoint: str, outcome: str, duration: float) -> None:
    try:
        entrypoint = entrypoint if entrypoint in {"preflight", "graph", "copy", "preview", "image"} else "other"
        outcome = outcome if outcome in {"ready", "needs_input", "error"} else "error"
        input_assessments_total.labels(entrypoint, outcome).inc()
        input_assessment_duration.labels(entrypoint).observe(max(0, duration))
    except Exception:
        pass  # Observability must never prevent a merchant action.


class GenerationObservation:
    """One local observation per invocation; SSE reconnection is not a new run."""

    def __init__(self, entrypoint: str, platform: str, ready: bool):
        import time
        self.entrypoint = entrypoint if entrypoint in {"graph", "copy", "preview"} else "other"
        self.platform = platform if platform in {"taobao", "jd", "pinduoduo", "suning", "xiaohongshu"} else "other"
        self.ready = ready
        self.started_at = time.perf_counter()
        self.closed = False
        self.progress_recorded = False
        self._record("started" if ready else "blocked")

    def _record(self, outcome: str) -> None:
        try:
            generation_runs_total.labels(self.entrypoint, self.platform, outcome).inc()
        except Exception:
            pass

    def first_progress(self) -> None:
        import time
        if self.progress_recorded or not self.ready:
            return
        self.progress_recorded = True
        try:
            generation_first_progress.labels(self.platform).observe(time.perf_counter() - self.started_at)
        except Exception:
            pass

    def finish(self, final: dict | None = None) -> None:
        import time
        if self.closed or not self.ready:
            return
        self.closed = True
        final = final or {}
        status = final.get("overall_status", "error")
        outcome = {
            "success": "completed", "ready_with_warnings": "warnings",
            "needs_revision": "needs_revision", "partial_success": "partial",
        }.get(status, "failed")
        adaptation = final.get("style_adaptation") or {}
        if adaptation.get("fallback") and outcome == "completed":
            outcome = "fallback"
        self._record(outcome)
        try:
            generation_duration.labels(self.entrypoint, self.platform).observe(time.perf_counter() - self.started_at)
            if adaptation.get("draft"):
                traced = bool(adaptation.get("platform_skill_id") and adaptation.get("platform_skill_version"))
                platform_drafts_total.labels(self.platform, "present" if traced else "missing",
                                             "yes" if adaptation.get("fallback") else "no").inc()
        except Exception:
            pass


def record_llm_call(
    agent_type: str,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    duration_seconds: float = 0.0,
) -> None:
    """Record metrics for a single LLM call."""
    agent_requests_total.labels(agent_type=agent_type, provider=provider, model=model).inc()
    agent_tokens_total.labels(agent_type=agent_type, direction="input").inc(input_tokens)
    agent_tokens_total.labels(agent_type=agent_type, direction="output").inc(output_tokens)
    agent_cost_total_usd.labels(agent_type=agent_type).inc(cost_usd)
    if duration_seconds > 0:
        agent_request_duration_seconds.labels(agent_type=agent_type, provider=provider).observe(duration_seconds)


def update_budget_gauges(daily_cost: float, budget: float, over_budget: bool) -> None:
    """Update daily budget-related gauges."""
    agent_cost_daily_usd.set(daily_cost)
    agent_budget_daily_usd.set(budget)
    agent_over_budget.set(1 if over_budget else 0)


def record_image_search(
    provider: str,
    status: str,
    duration_seconds: float,
    candidate_count: int,
) -> None:
    """Record one Image Scout attempt without treating it as an LLM call."""

    image_search_requests_total.labels(provider=provider, status=status).inc()
    # Rejected input never called a search provider; don't dilute search P95.
    if status != "needs_input":
        image_search_duration_seconds.labels(provider=provider).observe(duration_seconds)
    if candidate_count > 0:
        image_search_candidates_total.labels(provider=provider).inc(candidate_count)


def get_metrics() -> bytes:
    """Return Prometheus text format metrics."""
    return generate_latest(REGISTRY)
