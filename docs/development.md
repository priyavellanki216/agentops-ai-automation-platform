# Development

For the React/Node control plane, run `pnpm install`, `pnpm dev`, `pnpm check`, `pnpm test`, and `pnpm build`. For Python references, create a Python 3.12 environment, install `backend/requirements.txt`, then run `uvicorn backend.app.main:app --reload` and `uvicorn mcp_server.app:app --port 8100`. Run `python3 -m pytest backend/tests evaluation/test_metrics.py -q` for the deterministic suite.

Docker Compose provides frontend, FastAPI, MCP, and PostgreSQL/pgvector service references. Docker validation should be performed on a host with Docker installed. Live OpenAI embeddings/answers and PostgreSQL execution require environment configuration and are intentionally not exercised by the offline test suite.
