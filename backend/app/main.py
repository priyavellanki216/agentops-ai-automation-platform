"""AgentOps Python-first API surface.

The managed preview uses the React/Express shell, while this module is the
portable FastAPI reference implementation for local Docker deployment.
"""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .agents.router import route_request
from .observability.tracing import TraceEnvelope
from .services.audit import AuditEvent
from .tools import authorize_tool

app = FastAPI(title="AgentOps API", version="2.4.1", description="Evidence-backed AI agent operations platform")


class Role(str, Enum):
    admin = "admin"
    analyst = "analyst"
    support = "support"
    viewer = "viewer"


class AgentRequest(BaseModel):
    query: str = Field(min_length=4, max_length=4000)
    agent_version: str = Field(default="v2.4.1", pattern=r"^v\d+\.\d+\.\d+$")


class Source(BaseModel):
    source_id: str
    title: str
    source_type: str
    relevance: float = Field(ge=0, le=1)


class AgentRun(BaseModel):
    run_id: str
    trace_id: str
    status: str
    answer: str
    tools_used: list[str]
    sources: list[Source]
    latency_ms: int
    created_at: datetime


RATE_WINDOW_SECONDS = 60
RATE_LIMIT = int(os.getenv("AGENTOPS_RATE_LIMIT", "60"))
_REQUESTS: dict[str, list[float]] = {}

TOOLS: dict[str, dict[str, object]] = {
    "query_database": {"interface": "SQL / approved views", "roles": ["admin", "analyst"]},
    "search_knowledge_base": {"interface": "MCP / pgvector", "roles": ["admin", "analyst", "support", "viewer"]},
    "get_customer": {"interface": "MCP / customer", "roles": ["admin", "analyst", "support", "viewer"]},
    "get_support_ticket": {"interface": "MCP / support", "roles": ["admin", "analyst", "support", "viewer"]},
    "get_product_metrics": {"interface": "MCP / analytics", "roles": ["admin", "analyst", "viewer"]},
    "get_financial_summary": {"interface": "MCP / finance", "roles": ["admin", "analyst"]},
    "calculate_metrics": {"interface": "deterministic / sandboxed", "roles": ["admin", "analyst"]},
    "get_incident_details": {"interface": "MCP / engineering", "roles": ["admin", "analyst", "support", "viewer"]},
    "create_ticket": {"interface": "MCP / support", "roles": ["admin", "support"]},
    "generate_report": {"interface": "reporting / cited", "roles": ["admin", "analyst"]},
}


def require_api_key(x_api_key: str | None = Header(default=None)) -> Role:
    """Validate an environment-managed key and apply a bounded per-key rate limit."""
    configured = [key.strip() for key in os.getenv("AGENTOPS_API_KEYS", "").split(",") if key.strip()]
    role_map = {
        pair.split("=", 1)[0].strip(): pair.split("=", 1)[1].strip()
        for pair in os.getenv("AGENTOPS_KEY_ROLES", "").split(",")
        if "=" in pair
    }
    if not x_api_key or (configured and x_api_key not in configured):
        raise HTTPException(status_code=401, detail={"code": "AUTH_REQUIRED", "message": "Provide a valid API key."})
    now = time.monotonic()
    recent = [stamp for stamp in _REQUESTS.get(x_api_key, []) if now - stamp < RATE_WINDOW_SECONDS]
    if len(recent) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail={"code": "RATE_LIMITED", "message": "Retry after the rate window."})
    _REQUESTS[x_api_key] = [*recent, now]
    role = role_map.get(x_api_key, os.getenv("AGENTOPS_DEFAULT_ROLE", "analyst"))
    try:
        return Role(role)
    except ValueError as exc:
        raise HTTPException(
            status_code=500, detail={"code": "ROLE_CONFIG_INVALID", "message": "Configured role is invalid."}
        ) from exc


@app.get("/api/v1/health")
def health() -> dict[str, object]:
    return {"status": "operational", "services": {"api": "healthy", "database": "configured", "mcp": "configured"}}


@app.get("/api/v1/tools")
def list_tools(role: Role = Depends(require_api_key)) -> dict[str, object]:
    return {
        "role": role,
        "tools": [{"name": name, **meta, "allowed": role.value in meta["roles"]} for name, meta in TOOLS.items()],
    }


@app.post("/api/v1/agent/run", response_model=AgentRun)
def run_agent(
    request: AgentRequest, x_request_id: str | None = Header(default=None), role: Role = Depends(require_api_key)
) -> AgentRun:
    if role not in {Role.admin, Role.analyst}:
        raise HTTPException(
            status_code=403, detail={"code": "ROLE_DENIED", "message": "This role cannot run investigations."}
        )
    now = datetime.now(UTC)
    trace = TraceEnvelope(agent_version=request.agent_version)
    if x_request_id:
        trace.request_id = x_request_id
    audit = AuditEvent(
        action="agent_run_started",
        resource="agent_run",
        detail={"query_length": len(request.query), "role": role.value},
        trace_id=trace.trace_id,
    )
    audit.persist()
    trace.event("request_received", query_length=len(request.query), role=role.value)
    plan = route_request(request.query)
    allowed_tools: list[str] = []
    for tool_name in plan.tools:
        try:
            authorize_tool(tool_name, role.value)
            allowed_tools.append(tool_name)
            trace.event("tool_planned", tool=tool_name)
        except (ValueError, PermissionError) as exc:
            trace.errors.append({"code": "TOOL_PLAN_REJECTED", "message": str(exc)})
            trace.event("tool_plan_rejected", tool=tool_name, error=str(exc))
            AuditEvent(
                action="tool_plan_rejected", resource=tool_name, detail={"error": str(exc)}, trace_id=trace.trace_id
            ).persist()
    trace.event("plan_selected", intent=plan.intent, tools=allowed_tools)
    trace_payload = trace.finish()
    AuditEvent(
        action="agent_run_completed",
        resource="agent_run",
        detail={"tools": allowed_tools, "latency_ms": trace_payload["latency_ms"]},
        trace_id=trace.trace_id,
    ).persist()
    return AgentRun(
        run_id=f"run_{uuid4().hex[:8]}",
        trace_id=str(trace_payload["trace_id"]),
        status="accepted",
        answer="The request has been accepted for evidence-gated orchestration.",
        tools_used=allowed_tools,
        sources=[],
        latency_ms=int(trace_payload["latency_ms"]),
        created_at=now,
    )


@app.get("/api/v1/metrics")
def metrics(role: Role = Depends(require_api_key)) -> dict[str, object]:
    return {
        "agent_version": "v2.4.1",
        "role": role,
        "evaluation": {"status": "not_run", "message": "Run the benchmark to populate measured metrics."},
    }
