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


def get_metrics() -> bytes:
    """Return Prometheus text format metrics."""
    return generate_latest(REGISTRY)
