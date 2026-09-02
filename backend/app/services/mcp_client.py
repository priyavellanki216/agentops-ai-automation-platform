from __future__ import annotations

import os
from typing import Any

import httpx

from mcp_server.server import call_tool, list_tools


class MCPClient:
    def __init__(self, token: str, endpoint: str | None = None) -> None:
        self.token = token
        self.endpoint = endpoint or os.getenv("MCP_SERVER_URL")

    def discover(self) -> list[dict[str, str]]:
        if not self.endpoint:
            return list_tools(self.token)
        response = httpx.post(f"{self.endpoint.rstrip('/')}/mcp", headers={"Authorization": f"Bearer {self.token}"}, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, timeout=10)
        response.raise_for_status()
        return response.json()["result"]["tools"]

    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if not self.endpoint:
            return call_tool(name, arguments, self.token)
        response = httpx.post(f"{self.endpoint.rstrip('/')}/mcp", headers={"Authorization": f"Bearer {self.token}"}, json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}}, timeout=15)
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            return {"ok": False, "error": payload["error"]}
        return payload["result"]
