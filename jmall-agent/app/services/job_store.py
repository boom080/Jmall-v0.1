"""Redis-backed job store for persistent agent orchestration jobs.

Jobs survive SSE disconnections and page navigation. Each job has:
- jobId: UUID v4
- status: PENDING | RUNNING | COMPLETED | FAILED
- user_id / product_draft_id: ownership and draft association
- currentStep: last completed agent node
- progress: {agent_name: status} map
- result: final aggregated result (null while running)
- error: error message if failed
- createdAt / updatedAt: ISO timestamps
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import redis

from app.core.config import Settings

logger = logging.getLogger(__name__)

JOB_KEY_PREFIX = "agent:job:"
ACTIVE_JOB_KEY_PREFIX = "agent:user:active:"
JOB_TTL_SECONDS = 3600  # 1 hour


class JobStore:
    """Manages persistent agent job state in Redis."""

    def __init__(self, settings: Settings) -> None:
        redis_url = settings.redis_url or "redis://localhost:6379"
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()
            self.available = True
            logger.info("JobStore: Redis connected at %s", redis_url)
        except Exception as exc:
            logger.warning("JobStore: Redis unavailable (%s), jobs will not persist", exc)
            self.redis = None
            self.available = False

    def create_job(
        self,
        user_id: Optional[int] = None,
        product_draft_id: Optional[int] = None,
        product_info: Optional[Dict[str, Any]] = None,
        target_style: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
    ) -> str:
        """Create a new job record. Returns the jobId."""
        job_id = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc).isoformat()
        job = {
            "jobId": job_id,
            "job_id": job_id,
            "status": "PENDING",
            "user_id": user_id,
            "product_draft_id": product_draft_id,
            # Persist the submitted facts with the server-side job. A page
            # refresh must restore a new-product form even without a DB draft.
            "productInfo": product_info or {},
            "product_info": product_info or {},
            "targetStyle": target_style,
            "target_style": target_style,
            "knowledge_base_id": knowledge_base_id,
            "currentStep": None,
            "current_step": None,
            "progress": {},
            "ragQuality": None,
            "rag_quality": None,
            "result": None,
            "error": None,
            "createdAt": now,
            "updatedAt": now,
            "created_at": now,
            "updated_at": now,
        }
        if self.available and self.redis:
            try:
                self.redis.setex(
                    JOB_KEY_PREFIX + job_id,
                    JOB_TTL_SECONDS,
                    json.dumps(job, ensure_ascii=False),
                )
                if user_id is not None:
                    self.redis.setex(
                        ACTIVE_JOB_KEY_PREFIX + str(user_id),
                        JOB_TTL_SECONDS,
                        job_id,
                    )
            except Exception as exc:
                logger.warning("JobStore: failed to create job %s: %s", job_id, exc)
        logger.info("JobStore: created job %s", job_id)
        return job_id

    def mark_running(self, job_id: str) -> None:
        """Move a newly-created job to RUNNING before execution starts."""
        self._update_status(job_id, "RUNNING")

    def mark_failed(self, job_id: str, error: str) -> None:
        """Persist a terminal background-task failure."""
        self._update_status(job_id, "FAILED", error=error)

    def _update_status(self, job_id: str, status: str, error: Optional[str] = None) -> None:
        if not self.available or not self.redis:
            return
        try:
            raw = self.redis.get(JOB_KEY_PREFIX + job_id)
            if not raw:
                return
            job = json.loads(raw)
            job["status"] = status
            job["updatedAt"] = datetime.now(timezone.utc).isoformat()
            job["updated_at"] = job["updatedAt"]
            if error is not None:
                job["error"] = error
            self.redis.setex(
                JOB_KEY_PREFIX + job_id,
                JOB_TTL_SECONDS,
                json.dumps(job, ensure_ascii=False),
            )
        except Exception as exc:
            logger.warning("JobStore: failed to update status for %s: %s", job_id, exc)

    def update_progress(
        self,
        job_id: str,
        agent_name: str,
        status: str,
        result: dict,
    ) -> None:
        """Update job progress with the latest agent results."""
        if not self.available or not self.redis:
            return
        try:
            raw = self.redis.get(JOB_KEY_PREFIX + job_id)
            if not raw:
                return
            job = json.loads(raw)
            job["updatedAt"] = datetime.now(timezone.utc).isoformat()
            job["updated_at"] = job["updatedAt"]

            # Track progress
            progress = job.get("progress", {})
            progress[agent_name] = status.upper()
            job["progress"] = progress
            job["currentStep"] = agent_name
            job["current_step"] = agent_name

            # Store partial results for key agents
            if agent_name == "parse_intent":
                plan = result.get("plan", {})
                job["plan"] = plan
            elif agent_name == "market_research":
                job["marketInsights"] = result.get("market_insights")
            elif agent_name == "rag_retrieval":
                job["ragQuality"] = result.get("rag_quality")
                job["rag_quality"] = result.get("rag_quality")
            elif agent_name == "copy_generation":
                job["copyDrafts"] = result.get("style_previews")
            elif agent_name == "compliance_review":
                job["complianceResult"] = result
            elif agent_name == "style_adaptation":
                job["stylePreviews"] = result.get("style_previews")
            elif agent_name == "orchestration_complete":
                job["status"] = "COMPLETED"
                job["result"] = result.get("final_result")
                job["costStats"] = result.get("cost_stats")
                job["cost_stats"] = result.get("cost_stats")
            elif agent_name == "error":
                job["status"] = "FAILED"
                job["error"] = result.get("error", "Unknown error")

            self.redis.setex(
                JOB_KEY_PREFIX + job_id,
                JOB_TTL_SECONDS,
                json.dumps(job, ensure_ascii=False),
            )
        except Exception as exc:
            logger.warning("JobStore: failed to update job %s: %s", job_id, exc)

    def get_job(
        self,
        job_id: str,
        user_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve job state by ID."""
        if not self.available or not self.redis:
            return None
        try:
            raw = self.redis.get(JOB_KEY_PREFIX + job_id)
            if raw:
                job = json.loads(raw)
                owner_id = job.get("user_id")
                if user_id is not None and owner_id is not None and owner_id != user_id:
                    return None
                return job
        except Exception as exc:
            logger.warning("JobStore: failed to get job %s: %s", job_id, exc)
        return None

    def get_active_job(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Return the user's most recent unexpired job, including its final result."""
        if not self.available or not self.redis:
            return None
        try:
            job_id = self.redis.get(ACTIVE_JOB_KEY_PREFIX + str(user_id))
            if not job_id:
                return None
            job = self.get_job(job_id, user_id=user_id)
            if job is None:
                self.redis.delete(ACTIVE_JOB_KEY_PREFIX + str(user_id))
            return job
        except Exception as exc:
            logger.warning("JobStore: failed to get active job for user %s: %s", user_id, exc)
            return None

    def delete_job(self, job_id: str) -> None:
        """Delete a job record."""
        if not self.available or not self.redis:
            return
        try:
            raw = self.redis.get(JOB_KEY_PREFIX + job_id)
            if raw:
                job = json.loads(raw)
                user_id = job.get("user_id")
                if user_id is not None:
                    active_key = ACTIVE_JOB_KEY_PREFIX + str(user_id)
                    if self.redis.get(active_key) == job_id:
                        self.redis.delete(active_key)
            self.redis.delete(JOB_KEY_PREFIX + job_id)
        except Exception as exc:
            logger.warning("JobStore: failed to delete job %s: %s", job_id, exc)

    def consume_job(self, job_id: str, user_id: int) -> bool:
        """Remove a completed job after its generated result is published."""
        job = self.get_job(job_id, user_id=user_id)
        if not job or job.get("status") != "COMPLETED":
            return False
        self.delete_job(job_id)
        return True
