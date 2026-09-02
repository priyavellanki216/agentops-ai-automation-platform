from fastapi.testclient import TestClient

from backend.app.main import app
from mcp_server.server import call_tool


def test_health_is_public() -> None:
    assert TestClient(app).get("/api/v1/health").status_code == 200


def test_agent_requires_api_key() -> None:
    assert TestClient(app).post("/api/v1/agent/run", json={"query": "Find failed transactions"}).status_code == 401


def test_mcp_denies_missing_token() -> None:
    try:
        call_tool("get_customer", {}, None)
    except PermissionError as exc:
        assert "AUTH_REQUIRED" in str(exc)
    else:
        raise AssertionError("missing MCP token should be rejected")
