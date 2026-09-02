# AgentOps — AI Agent Automation, MCP & Evaluation Platform

AgentOps is an internal enterprise operations platform for turning natural-language business questions into evidence-backed, traceable results. The interface is an engineering control plane: operators can run investigations, inspect traces, review connectors, assess system health, and compare agent versions.

## Architecture

The portable reference architecture is Python-first: React + TypeScript for the console, FastAPI for the API layer, LangGraph for orchestration, OpenAI for model reasoning, PostgreSQL + pgvector for relational and semantic evidence, an authenticated MCP connector boundary for internal tools, OpenTelemetry-compatible trace envelopes, structured JSON logs, and a PyTest/Ruff/MyPy evaluation workflow. The managed preview uses the provided authenticated web shell so the console remains reviewable in-browser; `backend/` and `mcp_server/` contain the local Docker-oriented Python reference implementation.

## Tool and permission model

The allow-listed tools are `query_database`, `search_knowledge_base`, `get_customer`, `get_support_ticket`, `get_product_metrics`, `get_financial_summary`, `calculate_metrics`, `get_incident_details`, `create_ticket`, and `generate_report`. Roles are `admin`, `analyst`, `support`, and `viewer`. Tools must validate typed inputs, enforce role access, use approved database views rather than arbitrary SQL, apply bounded retries and timeouts, and emit structured failures with a correlation ID.

## MCP flow

MCP provides a typed connector boundary between the orchestrator and internal capabilities. At startup, the client discovers the authenticated server's tool catalog. During a run, the planner selects only tools allowed for the caller's role, sends validated JSON arguments, receives structured data and evidence references, and records the request, response, latency, and failure state in the trace. Knowledge-base answers are evidence-gated: without sufficient retrieved chunks, the agent must abstain or ask for clarification.

## Evaluation and regression detection

Evaluation cases live under `evaluation/` and should include at least 30 representative requests with expected tools, arguments, answer characteristics, and evidence. The harness calculates tool-selection accuracy, argument accuracy, answer correctness, groundedness, retrieval precision/recall, task success, latency, failure rate, and cost where provider metadata is available. Each run writes JSON and Markdown reports. Configurable thresholds fail CI when a new agent version materially regresses.

## Data model and security references

The PostgreSQL/pgvector reference DDL is in `backend/schema.sql`; the relationship map is in [`docs/er-diagram.mmd`](docs/er-diagram.mmd). Authentication, per-key roles, and the single-process limiter boundary are documented in [`docs/security.md`](docs/security.md).

## Run locally

The managed preview is available from the project dashboard. For the Python reference services, install the dependencies listed in `backend/requirements.txt`, configure environment variables without committing secrets, then run `uvicorn backend.app.main:app --reload`. The MCP boundary can be imported from `mcp_server.server`. Docker Compose and GitHub Actions are included as deployment references and should be connected to a PostgreSQL + pgvector service before production use.

## Operational status

The console deliberately labels benchmark metrics as measured only after an evaluation run. It does not fabricate benchmark results. The preview contains simulated internal-system labels for demonstrating the control-plane experience, while production data and credentials must be supplied through environment-managed configuration.
