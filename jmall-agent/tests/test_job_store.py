"""Focused tests for persistent orchestration job ownership and recovery."""

import json

from app.services.job_store import ACTIVE_JOB_KEY_PREFIX, JOB_KEY_PREFIX, JobStore


class FakeRedis:
    def __init__(self):
        self.values = {}

    def setex(self, key, ttl, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    def delete(self, key):
        self.values.pop(key, None)


def make_store(settings):
    store = JobStore.__new__(JobStore)
    store.redis = FakeRedis()
    store.available = True
    return store


def test_job_persists_required_fields_and_active_user_index(settings):
    store = make_store(settings)
    job_id = store.create_job(
        user_id=7,
        product_draft_id=42,
        product_info={"title": "恐龙蛋", "category": "食品饮料", "price": "19.9"},
        target_style="xiaohongshu",
    )

    job = store.get_active_job(7)
    assert job["job_id"] == job_id
    assert job["user_id"] == 7
    assert job["product_draft_id"] == 42
    assert job["status"] == "PENDING"
    assert job["current_step"] is None
    assert job["rag_quality"] is None
    assert job["product_info"]["title"] == "恐龙蛋"
    assert job["target_style"] == "xiaohongshu"

    store.mark_running(job_id)
    store.update_progress(job_id, "rag_retrieval", "completed", {
        "rag_quality": {"quality": "good", "top1_score": 0.7},
    })
    store.update_progress(job_id, "orchestration_complete", "completed", {
        "final_result": {"overall_status": "success"},
    })

    completed = store.get_active_job(7)
    assert completed["status"] == "COMPLETED"
    assert completed["current_step"] == "orchestration_complete"
    assert completed["rag_quality"]["quality"] == "good"
    assert completed["result"]["overall_status"] == "success"
    assert store.get_job(job_id, user_id=8) is None
    assert store.consume_job(job_id, user_id=8) is False
    assert store.consume_job(job_id, user_id=7) is True
    assert store.get_active_job(7) is None
