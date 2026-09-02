from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

logger = logging.getLogger("agentops.audit")


@dataclass
class AuditEvent:
    action: str
    resource: str
    user_id: int | None = None
    trace_id: str = field(default_factory=lambda: f"trace_{uuid4().hex[:10]}")
    detail: dict[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def persist(self) -> dict[str, object]:
        """Emit a DB-ready event and structured log; DB repositories can insert this row."""
        payload = {"id": str(uuid4()), "action": self.action, "resource": self.resource, "user_id": self.user_id, "trace_id": self.trace_id, "detail": self.detail, "created_at": self.created_at.isoformat()}
        logger.info(json.dumps(payload, default=str))
        return payload
