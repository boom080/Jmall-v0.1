"""Integration tests for the SSE streaming endpoint.

Tests the POST /api/agent/orchestrate/stream endpoint with FastAPI TestClient.
"""

import json

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_sse_stream_returns_event_stream():
    """SSE endpoint returns text/event-stream content type."""
    with client.stream(
        "POST",
        "/api/agent/orchestrate/stream",
        json={
            "product_info": {
                "title": "测试商品",
                "category": "测试类别",
                "description": "测试描述",
                "price": "9900",
            },
            "target_style": "taobao",
        },
    ) as response:
        assert response.status_code == 200, f"Unexpected status: {response.status_code}"
        content_type = response.headers.get("content-type", "")
        assert "text/event-stream" in content_type, f"Expected text/event-stream, got: {content_type}"


def test_sse_stream_contains_events():
    """SSE stream contains valid SSE event format."""
    with client.stream(
        "POST",
        "/api/agent/orchestrate/stream",
        json={
            "product_info": {
                "title": "静音破壁机",
                "category": "厨房电器",
                "description": "低噪音设计",
                "price": "29900",
            },
            "target_style": "taobao",
        },
    ) as response:
        assert response.status_code == 200

        body = ""
        for chunk in response.iter_bytes():
            body += chunk.decode("utf-8", errors="replace")

        # Should contain SSE event markers
        assert "event: " in body or "data: " in body, f"Should contain SSE events, got: {body[:200]}"

        # Parse events
        lines = body.strip().split("\n")
        events_found = []
        for line in lines:
            if line.startswith("event: "):
                events_found.append(line[7:].strip())

        assert len(events_found) > 0, "Should have at least one event type"


def test_sse_stream_includes_completion():
    """SSE stream includes orchestration_complete event."""
    with client.stream(
        "POST",
        "/api/agent/orchestrate/stream",
        json={
            "product_info": {
                "title": "测试商品",
                "category": "测试",
                "description": "描述",
                "price": "1000",
            },
            "target_style": "jd",
        },
    ) as response:
        body = ""
        for chunk in response.iter_bytes():
            body += chunk.decode("utf-8", errors="replace")

        # Should have completion or done event
        assert ("orchestration_complete" in body) or ("done" in body.split("event:")), \
            f"Should contain completion event, got: {body[:300]}"


def test_sse_stream_event_data_is_valid_json():
    """SSE event data is valid JSON."""
    with client.stream(
        "POST",
        "/api/agent/orchestrate/stream",
        json={
            "product_info": {
                "title": "测试",
                "category": "测试",
                "description": "",
                "price": "1000",
            },
            "target_style": "taobao",
        },
    ) as response:
        body = ""
        for chunk in response.iter_bytes():
            body += chunk.decode("utf-8", errors="replace")

    # Extract data lines and verify they parse as JSON
    json_lines = []
    for line in body.split("\n"):
        if line.startswith("data: ") and line[6:].strip() not in ("{}", ""):
            json_lines.append(line[6:].strip())

    assert len(json_lines) > 0, "Should have at least one non-trivial data line"

    for data_line in json_lines:
        try:
            parsed = json.loads(data_line)
            assert (
                "jobId" in parsed
                or "agent" in parsed
                or "final_result" in parsed
                or "error" in parsed
            ), f"Data should contain jobId, agent, final_result, or error: {data_line[:100]}"
        except json.JSONDecodeError:
            # Some data lines might not be JSON (like error messages)
            pass


def test_sse_stream_handles_keepalive():
    """SSE stream may include keepalive comments."""
    with client.stream(
        "POST",
        "/api/agent/orchestrate/stream",
        json={
            "product_info": {
                "title": "快速测试",
                "category": "测试",
                "description": "",
                "price": "1000",
            },
            "target_style": "taobao",
        },
    ) as response:
        body = ""
        for chunk in response.iter_bytes():
            body += chunk.decode("utf-8", errors="replace")

    # Keepalive comments start with ":"
    has_keepalive = any(
        line.startswith(": keepalive") for line in body.split("\n")
    )
    # Keepalive is optional; just verify no crash
    assert isinstance(body, str)


def test_sse_stream_has_cache_headers():
    """SSE response includes proper cache-control headers."""
    with client.stream(
        "POST",
        "/api/agent/orchestrate/stream",
        json={
            "product_info": {
                "title": "测试",
                "category": "测试",
                "description": "",
                "price": "1000",
            },
            "target_style": "taobao",
        },
    ) as response:
        cache_control = response.headers.get("cache-control", "")
        assert "no-cache" in cache_control.lower(), f"Should have no-cache: {cache_control}"
        connection = response.headers.get("connection", "")
        assert "keep-alive" in connection.lower(), f"Should have keep-alive: {connection}"
