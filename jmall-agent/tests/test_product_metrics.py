"""M5 counters use deltas because the registry lives for the process lifetime."""

import asyncio
import pytest
from fastapi.testclient import TestClient

from app.core import metrics
from app.main import app


def sample(name, **labels):
    return metrics.REGISTRY.get_sample_value(name, labels) or 0


def test_free_check_records_ready_and_blocked_without_llm_tokens():
    before_tokens = sum(s.value for family in metrics.agent_tokens_total.collect()
                        for s in family.samples if s.name == "agent_tokens_total")
    before = sample("jmall_input_assessments_total", entrypoint="preflight", outcome="needs_input")
    response = TestClient(app).post("/api/agent/input-assessment", json={
        "product_info": {"title": "保温水杯", "category": "家居日用"},
    })
    assert response.json()["input_assessment"]["ready"] is False
    assert sample("jmall_input_assessments_total", entrypoint="preflight", outcome="needs_input") == before + 1
    assert before_tokens == sum(s.value for family in metrics.agent_tokens_total.collect()
                                for s in family.samples if s.name == "agent_tokens_total")


def test_graph_rejection_does_not_count_generation_start_or_first_progress(graph):
    labels = {"entrypoint": "graph", "platform": "jd"}
    blocked = sample("jmall_generation_runs_total", **labels, outcome="blocked")
    started = sample("jmall_generation_runs_total", **labels, outcome="started")
    progress = sample("jmall_generation_first_progress_seconds_count", platform="jd")
    async def callback(*_):
        pass
    asyncio.run(graph.invoke({"product_info": {"title": "保温水杯", "category": "家居日用"},
                              "target_style": "jd"}, progress_callback=callback))
    assert sample("jmall_generation_runs_total", **labels, outcome="blocked") == blocked + 1
    assert sample("jmall_generation_runs_total", **labels, outcome="started") == started
    assert sample("jmall_generation_first_progress_seconds_count", platform="jd") == progress


@pytest.mark.parametrize("status,outcome", [
    ("success", "completed"), ("ready_with_warnings", "warnings"),
    ("needs_revision", "needs_revision"), ("partial_success", "partial"), ("error", "failed"),
])
def test_generation_has_exactly_one_terminal_and_one_progress_sample(status, outcome):
    labels = {"entrypoint": "graph", "platform": "taobao"}
    before = sample("jmall_generation_runs_total", **labels, outcome=outcome)
    progress = sample("jmall_generation_first_progress_seconds_count", platform="taobao")
    observed = metrics.GenerationObservation("graph", "taobao", True)
    observed.first_progress()
    observed.first_progress()
    observed.finish({"overall_status": status})
    observed.finish({"overall_status": status})
    observed.finish()
    assert sample("jmall_generation_runs_total", **labels, outcome=outcome) == before + 1
    assert sample("jmall_generation_first_progress_seconds_count", platform="taobao") == progress + 1


def test_fallback_is_not_ordinary_success_and_metadata_is_measured():
    labels = {"entrypoint": "preview", "platform": "suning"}
    fallback = sample("jmall_generation_runs_total", **labels, outcome="fallback")
    traced = sample("jmall_platform_drafts_total", platform="suning", metadata="present", fallback="yes")
    observed = metrics.GenerationObservation("preview", "suning", True)
    observed.finish({"overall_status": "success", "style_adaptation": {
        "draft": {"titles": ["保温杯"]}, "fallback": True,
        "platform_skill_id": "suning_listing_v1", "platform_skill_version": "1.0.0",
    }})
    assert sample("jmall_generation_runs_total", **labels, outcome="fallback") == fallback + 1
    assert sample("jmall_platform_drafts_total", platform="suning", metadata="present", fallback="yes") == traced + 1


def test_metrics_failure_cannot_break_product_actions(monkeypatch):
    def fail(*_, **__):
        raise RuntimeError("registry unavailable")
    monkeypatch.setattr(metrics.generation_runs_total, "labels", fail)
    monkeypatch.setattr(metrics.input_assessments_total, "labels", fail)
    metrics.record_input_assessment("preflight", "ready", .001)
    metrics.GenerationObservation("graph", "jd", True).finish()


def test_unknown_metric_dimensions_are_bucketed_and_blocked_search_does_not_reduce_p95():
    metrics.record_input_assessment("secret-user-text", "secret-result", .001)
    observed = metrics.GenerationObservation("secret-entry", "secret-platform", True)
    observed.finish()
    assert "secret-" not in metrics.get_metrics().decode()
    before = sample("image_search_duration_seconds_count", provider="test-m5")
    metrics.record_image_search("test-m5", "needs_input", 0, 0)
    assert sample("image_search_duration_seconds_count", provider="test-m5") == before
