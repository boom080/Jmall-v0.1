"""Observe API-boundary checks while keeping the underlying gate pure."""

import time
from typing import Any, Mapping

from app.agents.input_gate import assess_product_input
from app.core.metrics import record_input_assessment


def assess_input_at_boundary(info: Mapping[str, Any], entrypoint: str) -> dict[str, Any]:
    started = time.perf_counter()
    outcome = "error"
    try:
        assessment = assess_product_input(info)
        outcome = assessment["status"]
        return assessment
    finally:
        record_input_assessment(entrypoint, outcome, time.perf_counter() - started)
