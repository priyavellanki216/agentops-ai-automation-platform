# PostgreSQL migration and verification

The reference schema is versioned at `backend/migrations/001_agentops.sql`. Apply it from a PostgreSQL client with the `vector` extension available:

```bash
psql "$DATABASE_URL" --set ON_ERROR_STOP=1 --file backend/migrations/001_agentops.sql
```

After applying the migration, verify the extension, required relations, and indexes with:

```sql
SELECT extname FROM pg_extension WHERE extname = 'vector';

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
    'users', 'customers', 'support_tickets', 'transactions', 'invoices',
    'campaigns', 'product_events', 'incidents', 'documents', 'document_chunks',
    'tool_registry', 'api_key_roles', 'agent_runs', 'tool_calls',
    'generated_reports', 'evaluation_runs', 'evaluation_results', 'audit_logs'
  )
ORDER BY table_name;

SELECT indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN (
    'document_chunks_embedding_idx',
    'tickets_status_priority_idx',
    'transactions_occurred_idx'
  )
ORDER BY indexname;

SELECT conrelid::regclass AS table_name, conname
FROM pg_constraint
WHERE contype = 'f'
  AND connamespace = 'public'::regnamespace
ORDER BY table_name, conname;
```

The expected result includes the `vector` extension, all listed tables, three named indexes, and foreign-key constraints linking business records to customers, campaigns, documents, users, runs, and evaluation runs. If the extension is unavailable, install the pgvector package for the target PostgreSQL service before applying the migration. The managed preview database is not PostgreSQL, so this procedure must run in the deployment environment.
