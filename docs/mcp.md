# MCP integration

The repository includes an authenticated MCP JSON-RPC boundary at `mcp_server/app.py`. Clients send `tools/list` or `tools/call` requests to `/mcp` with a Bearer token. The connector catalog includes customer, ticket search, product metrics, finance summary, and incident detail capabilities. The in-agent client uses `MCP_SERVER_URL` when configured and falls back to the local connector adapter for deterministic tests.

The flow is: Agent → MCP client → authenticated MCP server → typed connector tool → database or internal API → structured result. Unknown methods, invalid parameters, missing credentials, and denied roles return structured protocol errors.
