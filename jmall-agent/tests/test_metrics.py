"""Integration tests for Prometheus metrics endpoint.

Tests GET /metrics returns valid Prometheus-format metrics.
"""

from fastapi.testclient import TestClient

from app.core.metrics import agent_request_duration_seconds
from app.main import app

client = TestClient(app)


def test_metrics_endpoint_returns_200():
    """GET /metrics returns HTTP 200."""
    response = client.get("/metrics")
    assert response.status_code == 200


def test_metrics_endpoint_returns_text_plain():
    """GET /metrics returns text/plain content type."""
    response = client.get("/metrics")
    content_type = response.headers.get("content-type", "")
    assert "text/plain" in content_type, f"Expected text/plain, got: {content_type}"


def test_metrics_contains_expected_counters():
    """Response includes agent_requests_total counter."""
    response = client.get("/metrics")
    body = response.text

    # Prometheus metrics should include our custom counters
    assert "agent_requests_total" in body, "Should have agent_requests_total counter"
    assert "agent_tokens_total" in body, "Should have agent_tokens_total counter"
    assert "agent_cost_total_usd" in body, "Should have agent_cost_total_usd counter"


def test_metrics_contains_gauges():
    """Response includes budget gauges."""
    response = client.get("/metrics")
    body = response.text

    assert "agent_cost_daily_usd" in body, "Should have agent_cost_daily_usd gauge"
    assert "agent_budget_daily_usd" in body, "Should have agent_budget_daily_usd gauge"
    assert "agent_over_budget" in body, "Should have agent_over_budget gauge"


def test_metrics_contains_histogram():
    """Response includes request duration histogram."""
    # Record a dummy observation so labeled histogram appears in Prometheus output
    agent_request_duration_seconds.labels(agent_type="test", provider="test").observe(0.5)
    response = client.get("/metrics")
    body = response.text

    assert "agent_request_duration_seconds" in body, "Should have request duration histogram"
    # Histogram should have bucket definitions
    assert "le=" in body, "Should have histogram bucket definitions"


def test_metrics_declares_image_scout_observability():
    response = client.get("/metrics")
    body = response.text

    assert "image_search_requests_total" in body
    assert "image_search_duration_seconds" in body
    assert "image_search_candidates_total" in body


def test_metrics_format_is_valid_prometheus():
    """Each non-comment line follows Prometheus exposition format."""
    response = client.get("/metrics")
    body = response.text

    metrics_found = 0
    for line in body.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Valid metric lines have format: name{labels} value or name value
        if "{" in line:
            assert "}" in line, f"Malformed metric line: {line}"
        metrics_found += 1

    assert metrics_found > 0, "Should have at least one metric line"


def test_metrics_includes_help_text():
    """Prometheus metrics include HELP comments."""
    response = client.get("/metrics")
    body = response.text

    assert "# HELP" in body, "Should have HELP comments"
    assert "# TYPE" in body, "Should have TYPE declarations"
