# Agent flow

A request enters `POST /api/v1/agent/run` with an API key and optional correlation ID. The FastAPI boundary validates the request, creates a trace envelope and audit event, routes the natural-language query to a bounded tool plan, and authorizes each planned tool against the caller role.

The LangGraph reference graph provides parse, plan, and ground stages. Database access is restricted to approved views; knowledge retrieval uses chunk metadata, embeddings, pgvector similarity, and an evidence threshold. MCP connector calls use authenticated JSON-RPC discovery and execution. If evidence is insufficient, the answer stage abstains rather than producing unsupported claims. Run completion records latency, tool selection, errors, trace ID, and audit context.
