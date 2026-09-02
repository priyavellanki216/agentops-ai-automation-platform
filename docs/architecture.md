# Architecture

AgentOps is a portfolio implementation of an enterprise-oriented AI operations control plane. The React dashboard is hosted by the managed Node application, while the Python reference services expose the FastAPI agent boundary, MCP JSON-RPC server, retrieval contracts, evaluation runner, and PostgreSQL/pgvector schema.

```mermaid
flowchart LR
  UI[React + TypeScript dashboard] --> API[FastAPI agent API]
  API --> G[LangGraph state graph]
  G --> T[Typed role-restricted tools]
  T --> DB[(PostgreSQL + pgvector)]
  T --> MCP[MCP JSON-RPC client]
  MCP --> MS[MCP connector server]
  G --> R[Metadata-filtered retrieval]
  R --> DB
  G --> O[Structured trace + audit events]
  E[Evaluation runner] --> O
  E --> CI[GitHub Actions regression gate]
```

The runtime intentionally separates UI scaffolding from provider-backed execution. Database URLs, OpenAI credentials, MCP endpoints, API keys, and role mappings are environment-managed. The repository does not claim customer traffic or a production deployment.
