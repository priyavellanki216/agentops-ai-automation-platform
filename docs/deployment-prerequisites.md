# Deployment prerequisites

The repository includes the PostgreSQL/pgvector schema reference, approved-view query boundary, API-key authentication, role mapping, and bounded rate limiter required by the reference services. Applying `backend/schema.sql` and creating the PostgreSQL indexes must be performed in a PostgreSQL deployment environment; the managed preview database is not PostgreSQL and was not modified.

For production, replace the in-process request limiter with a shared Redis or gateway limiter when running more than one FastAPI instance. Configure secrets through the deployment secret manager, including database credentials, provider keys, MCP bearer tokens, and API-key role mappings. These requirements are operational deployment steps rather than missing source files.
