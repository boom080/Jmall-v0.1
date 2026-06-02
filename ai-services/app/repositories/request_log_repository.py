from typing import Dict, List


class RequestLogRepository:
    def __init__(self) -> None:
        self.logs: List[Dict[str, str]] = []

    def save(self, payload: Dict[str, str]) -> None:
        self.logs.append(payload)
