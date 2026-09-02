from fastapi.testclient import TestClient

from mcp_server.app import app


def test_mcp_tools_list_requires_auth() -> None:
    client = TestClient(app)
    assert client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).status_code == 401


def test_mcp_tools_list_returns_typed_catalog() -> None:
    response = TestClient(app).post(
        "/mcp",
        headers={"Authorization": "Bearer analyst_key"},
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
    )
    assert response.status_code == 200
    assert {tool["name"] for tool in response.json()["result"]["tools"]} >= {"get_customer", "get_product_metrics"}


def test_mcp_incident_tool_is_discoverable_and_callable() -> None:
    client = TestClient(app)
    listed = client.post(
        "/mcp",
        headers={"Authorization": "Bearer analyst_key"},
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
    ).json()["result"]["tools"]
    assert any(tool["name"] == "get_incident_details" for tool in listed)
    response = client.post(
        "/mcp",
        headers={"Authorization": "Bearer analyst_key"},
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "get_incident_details", "arguments": {"incident_id": "inc_1"}},
        },
    )
    assert response.json()["result"]["ok"] is True


def test_mcp_tool_call_returns_structured_result() -> None:
    response = TestClient(app).post(
        "/mcp",
        headers={"Authorization": "Bearer analyst_key"},
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "get_customer", "arguments": {"customer_id": "cus_1"}},
        },
    )
    assert response.json()["result"]["ok"] is True
