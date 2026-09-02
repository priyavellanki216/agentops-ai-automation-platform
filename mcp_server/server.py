"""Minimal MCP-compatible connector boundary for local Docker deployment.

The server intentionally exposes a small allow-listed catalog. Each tool accepts
validated JSON and returns structured data suitable for trace capture.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    required_role: str


TOOLS = (
    ToolSpec("get_customer", "Retrieve a customer record by stable ID.", "viewer"),
    ToolSpec("search_tickets", "Search support tickets with status and priority filters.", "viewer"),
    ToolSpec("get_product_metrics", "Retrieve product metrics for a bounded time range.", "analyst"),
    ToolSpec("get_financial_summary", "Retrieve finance aggregates from approved views.", "analyst"),
    ToolSpec("get_incident_details", "Retrieve incident details by stable ID.", "viewer"),
)


def authenticate(token: str | None) -> str:
    if not token:
        raise PermissionError("AUTH_REQUIRED: MCP bearer token is missing")
    return "admin" if token.startswith("admin_") else "analyst"


def list_tools(token: str | None) -> list[dict[str, str]]:
    authenticate(token)
    return [{"name": tool.name, "description": tool.description, "required_role": tool.required_role} for tool in TOOLS]


def call_tool(name: str, arguments: dict[str, Any], token: str | None) -> dict[str, Any]:
    role = authenticate(token)
    spec = next((tool for tool in TOOLS if tool.name == name), None)
    if spec is None:
        return {"ok": False, "error": {"code": "TOOL_NOT_FOUND", "message": name}}
    if spec.required_role == "analyst" and role not in {"admin", "analyst"}:
        return {"ok": False, "error": {"code": "ROLE_DENIED", "message": f"{role} cannot call {name}"}}
    return {
        "ok": True,
        "tool": name,
        "arguments": arguments,
        "data": [],
        "evidence": [],
        "trace": {"connector": "internal-mcp"},
    }
