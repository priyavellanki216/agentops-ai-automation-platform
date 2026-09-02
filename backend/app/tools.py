from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

T = TypeVar("T")

APPROVED_VIEWS = {"customer_support_summary", "transaction_failure_summary", "campaign_performance", "incident_rollup"}
DESTRUCTIVE_SQL = re.compile(r"\b(insert|update|delete|drop|alter|truncate|grant|revoke)\b", re.I)


@dataclass(frozen=True)
class ToolContract:
    name: str
    roles: frozenset[str]
    description: str


TOOL_CONTRACTS = {
    name: ToolContract(name, frozenset(roles), description)
    for name, roles, description in [
        ("query_database", {"admin", "analyst"}, "Query an approved read-only view."),
        ("search_knowledge_base", {"admin", "analyst", "support", "viewer"}, "Retrieve evidence-gated document chunks."),
        ("get_customer", {"admin", "analyst", "support", "viewer"}, "Retrieve a customer record."),
        ("get_support_ticket", {"admin", "analyst", "support", "viewer"}, "Retrieve a support ticket."),
        ("get_product_metrics", {"admin", "analyst", "viewer"}, "Retrieve product metrics."),
        ("get_financial_summary", {"admin", "analyst"}, "Retrieve finance aggregates."),
        ("calculate_metrics", {"admin", "analyst"}, "Run deterministic calculations."),
        ("get_incident_details", {"admin", "analyst", "support", "viewer"}, "Retrieve an incident."),
        ("create_ticket", {"admin", "support"}, "Create a support ticket."),
        ("generate_report", {"admin", "analyst"}, "Generate a cited report."),
    ]
}


def validate_approved_sql(sql: str) -> str:
    normalized = " ".join(sql.strip().split())
    if not normalized.lower().startswith("select ") or DESTRUCTIVE_SQL.search(normalized):
        raise ValueError("SQL_BLOCKED: only read-only SELECT statements are allowed")
    if not any(re.search(rf"\b{re.escape(view)}\b", normalized, re.I) for view in APPROVED_VIEWS):
        raise ValueError("SQL_BLOCKED: query must target an approved view")
    return normalized


def authorize_tool(name: str, role: str) -> ToolContract:
    contract = TOOL_CONTRACTS.get(name)
    if not contract:
        raise ValueError("TOOL_NOT_FOUND: tool is not registered")
    if role not in contract.roles:
        raise PermissionError(f"ROLE_DENIED: {role} cannot call {name}")
    return contract


def with_retry(operation: Callable[[], T], *, attempts: int = 3, timeout_seconds: float = 10.0) -> T:
    """Run a bounded operation with exponential backoff; callers map errors to trace IDs."""
    started = time.monotonic()
    last_error: Exception | None = None
    for attempt in range(attempts):
        if time.monotonic() - started >= timeout_seconds:
            break
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 - boundary converts unknown tool failures
            last_error = exc
            time.sleep(min(0.1 * (2 ** attempt), 0.8))
    raise TimeoutError("TOOL_TIMEOUT: operation exceeded bounded retry/timeout policy") from last_error


def structured_failure(code: str, message: str, trace_id: str) -> dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message, "trace_id": trace_id}}
