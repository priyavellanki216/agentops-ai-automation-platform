from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .db import DatabaseUnavailable, database_url, persist_record
from .observability.tracing import TraceEnvelope
from .services.mcp_client import MCPClient
from .services.retrieval import RetrievedChunk, build_pgvector_query, evidence_gate
from .tools import authorize_tool, validate_approved_sql, with_retry


class CustomerInput(BaseModel):
    customer_id: str = Field(min_length=1, max_length=80)


class TicketInput(BaseModel):
    ticket_id: str = Field(min_length=1, max_length=80)


class MetricsInput(BaseModel):
    metric: str = Field(min_length=1, max_length=80)
    region: str | None = Field(default=None, max_length=80)


class FinanceInput(BaseModel):
    period: str = Field(pattern=r"^\d{4}-\d{2}$")


class QueryInput(BaseModel):
    sql: str = Field(min_length=12, max_length=4000)


@dataclass(frozen=True)
class ToolResult:
    tool: str
    ok: bool
    data: dict[str, Any]
    evidence: list[dict[str, Any]]
    trace_id: str


def _result(
    tool: str,
    role: str,
    data: dict[str, Any],
    evidence: list[dict[str, Any]] | None = None,
    trace: TraceEnvelope | None = None,
) -> ToolResult:
    authorize_tool(tool, role)
    active_trace = trace or TraceEnvelope()
    active_trace.event("tool_completed", tool=tool, status="success")
    return ToolResult(tool, True, data, evidence or [], active_trace.trace_id)


def _db_execute(sql: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
    """Execute a parameterized approved-view query when DATABASE_URL is configured."""
    try:
        from sqlalchemy import create_engine, text
    except ImportError as exc:
        raise DatabaseUnavailable("DATABASE_DRIVER_MISSING: install backend/requirements.txt") from exc
    engine = create_engine(database_url(), pool_pre_ping=True)
    with engine.connect() as connection:
        return [dict(row._mapping) for row in connection.execute(text(sql), parameters).fetchall()]


def query_database(
    payload: QueryInput, role: str, executor: Callable[[str, dict[str, Any]], list[dict[str, Any]]] | None = None
) -> ToolResult:
    trace = TraceEnvelope()
    sql = validate_approved_sql(payload.sql)
    rows = with_retry(lambda: (executor or _db_execute)(sql, {}))
    return _result("query_database", role, {"rows": rows}, [{"source_type": "approved_view", "query": sql}], trace)


def search_knowledge_base(
    query: str,
    role: str,
    embedding: list[float],
    metadata: dict[str, str] | None = None,
    executor: Callable[[str, dict[str, Any]], list[dict[str, Any]]] | None = None,
) -> ToolResult:
    trace = TraceEnvelope()
    sql, params = build_pgvector_query(embedding, metadata=metadata)
    raw_chunks = with_retry(lambda: (executor or _db_execute)(sql, params))
    chunks = [
        RetrievedChunk(
            str(row["document_id"]),
            str(row["title"]),
            str(row["section"]),
            str(row["source"]),
            float(row["relevance"]),
            str(row["content"]),
            dict(row.get("metadata") or {}),
        )
        for row in raw_chunks
    ]
    accepted = evidence_gate(chunks)
    evidence = [
        {
            "document_id": chunk.document_id,
            "title": chunk.title,
            "section": chunk.section,
            "source": chunk.source,
            "relevance": chunk.relevance,
        }
        for chunk in accepted
    ]
    return _result(
        "search_knowledge_base",
        role,
        {"query": query, "chunks": [chunk.content for chunk in accepted]},
        evidence,
        trace,
    )


def get_customer(payload: CustomerInput, role: str, client: MCPClient) -> ToolResult:
    return _result("get_customer", role, client.call("get_customer", payload.model_dump()).get("data", {}))


def get_support_ticket(payload: TicketInput, role: str, client: MCPClient) -> ToolResult:
    return _result("get_support_ticket", role, client.call("search_tickets", payload.model_dump()).get("data", {}))


def get_product_metrics(payload: MetricsInput, role: str, client: MCPClient) -> ToolResult:
    return _result(
        "get_product_metrics", role, client.call("get_product_metrics", payload.model_dump()).get("data", {})
    )


def get_financial_summary(payload: FinanceInput, role: str, client: MCPClient) -> ToolResult:
    return _result(
        "get_financial_summary", role, client.call("get_financial_summary", payload.model_dump()).get("data", {})
    )


def calculate_metrics(expression: str, role: str) -> ToolResult:
    if len(expression) > 500:
        raise ValueError("INPUT_INVALID: metric expression is too long")
    return _result("calculate_metrics", role, {"expression": expression})


def get_incident_details(incident_id: str, role: str, client: MCPClient) -> ToolResult:
    return _result(
        "get_incident_details", role, client.call("get_incident_details", {"incident_id": incident_id}).get("data", {})
    )


def create_ticket(subject: str, role: str, persist: Callable[[str], dict[str, Any]] | None = None) -> ToolResult:
    authorize_tool("create_ticket", role)
    trace = TraceEnvelope()
    ticket_id = str(uuid4())
    writer = persist or (
        lambda value: persist_record(
            "support_tickets", {"id": ticket_id, "priority": "normal", "status": "open", "product_area": "unclassified"}
        )
    )
    return _result("create_ticket", role, writer(subject), trace=trace)


def generate_report(title: str, role: str, persist: Callable[[str, str], dict[str, Any]] | None = None) -> ToolResult:
    authorize_tool("generate_report", role)
    trace = TraceEnvelope()
    report_id = str(uuid4())
    body = f"Report draft: {title}\n\nEvidence and citations must be attached before publication."
    writer = persist or (
        lambda report_title, report_body: persist_record(
            "generated_reports",
            {"id": report_id, "title": report_title, "body": report_body, "trace_id": trace.trace_id},
        )
    )
    return _result("generate_report", role, writer(title, body), trace=trace)
