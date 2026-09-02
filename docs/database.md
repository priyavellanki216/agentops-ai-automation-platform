# Database

`backend/schema.sql` is the PostgreSQL/pgvector reference schema. It defines users, customers, support tickets, transactions, invoices, campaigns, product events, incidents, documents, document chunks, tool registry metadata, agent runs, tool calls, generated reports, evaluation runs/results, and audit logs. Foreign keys connect business records, chunks, runs, tool calls, evaluations, and audit ownership.

The application’s safe query boundary permits read-only SELECT statements against named approved views. The schema is intended to be initialized by the PostgreSQL service in Docker Compose or a deployment migration pipeline. The managed Manus project database is separate; no claim is made that this reference DDL has been applied to a live PostgreSQL instance.
