# Environment configuration

The managed project does not permit committing a `.env.example` file through the project file policy. This document is the repository-safe equivalent: it lists variable names and example shapes only, with no credentials.

| Variable | Purpose | Example shape |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@host:5432/agentops` |
| `OPENAI_API_KEY` | Optional OpenAI provider credential | supplied through a secret manager |
| `OPENAI_MODEL` | Grounded answer model | `gpt-4.1-mini` |
| `OPENAI_EMBEDDING_MODEL` | Embedding model | `text-embedding-3-small` |
| `MCP_SERVER_URL` | MCP JSON-RPC endpoint | `http://localhost:8100` |
| `MCP_BEARER_TOKEN` | MCP bearer credential | supplied through a secret manager |
| `AGENTOPS_API_KEYS` | Comma-separated reference API keys | supplied through a secret manager |
| `AGENTOPS_KEY_ROLES` | Per-key role mapping | `key=analyst,other=support` |
| `AGENTOPS_DEFAULT_ROLE` | Fallback API role | `analyst` |
| `AGENTOPS_RATE_LIMIT` | Per-process request limit | `60` |
| `MCP_PORT` | MCP service port | `8100` |

Never commit real keys, tokens, passwords, or connection strings. Configure these values through the deployment secret manager or local shell environment.
