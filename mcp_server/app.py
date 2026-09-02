from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .server import call_tool, list_tools

app = FastAPI(title="AgentOps MCP Server", version="2.4.1")


class JSONRPCRequest(BaseModel):
    jsonrpc: str = Field(pattern=r"^2\.0$")
    id: int | str
    method: str
    params: dict[str, Any] = Field(default_factory=dict)


def bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"code": "AUTH_REQUIRED", "message": "Bearer token required"})
    return authorization.removeprefix("Bearer ")


@app.post("/mcp")
def rpc(request: JSONRPCRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    token = bearer_token(authorization)
    if request.method == "tools/list":
        return {"jsonrpc": "2.0", "id": request.id, "result": {"tools": list_tools(token)}}
    if request.method == "tools/call":
        name = request.params.get("name")
        arguments = request.params.get("arguments", {})
        if not isinstance(name, str) or not isinstance(arguments, dict):
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "error": {"code": -32602, "message": "name and object arguments are required"},
            }
        result = call_tool(name, arguments, token)
        return {"jsonrpc": "2.0", "id": request.id, "result": result}
    return {"jsonrpc": "2.0", "id": request.id, "error": {"code": -32601, "message": "Method not found"}}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("MCP_PORT", "8100")))
