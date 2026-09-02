from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from uuid import uuid4

logger = logging.getLogger("agentops")


@dataclass
class TraceEnvelope:
    trace_id: str = field(default_factory=lambda: f"trace_{uuid4().hex[:10]}")
    request_id: str = field(default_factory=lambda: f"req_{uuid4().hex[:10]}")
    agent_version: str = "v2.4.1"
    model: str = "openai"
    tool_calls: list[dict[str, object]] = field(default_factory=list)
    retrieval_results: list[dict[str, object]] = field(default_factory=list)
    errors: list[dict[str, object]] = field(default_factory=list)
    started_at: float = field(default_factory=time.perf_counter)

    def event(self, kind: str, **payload: object) -> None:
        record = {"trace_id": self.trace_id, "request_id": self.request_id, "event": kind, **payload}
        logger.info(json.dumps(record, default=str))

    def finish(self, evaluation_score: float | None = None) -> dict[str, object]:
        payload = {
            **asdict(self),
            "latency_ms": round((time.perf_counter() - self.started_at) * 1000),
            "evaluation_score": evaluation_score,
        }
        self.event("run_finished", latency_ms=payload["latency_ms"], evaluation_score=evaluation_score)
        return payload
