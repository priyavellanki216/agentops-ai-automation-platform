from __future__ import annotations

import os
from typing import Any

from .tools import validate_approved_sql


class DatabaseUnavailable(RuntimeError):
    pass


def database_url() -> str:
    value = os.getenv("DATABASE_URL")
    if not value:
        raise DatabaseUnavailable("DATABASE_UNAVAILABLE: DATABASE_URL is not configured")
    return value


def query_approved_view(sql: str, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a DB-ready query envelope; production adapter executes it via a pooled driver."""
    return {"sql": validate_approved_sql(sql), "parameters": parameters or {}, "source": "approved_view", "rows": []}


def persist_record(table: str, values: dict[str, Any]) -> dict[str, Any]:
    """Persist a validated record through SQLAlchemy when the service is configured."""
    try:
        from sqlalchemy import create_engine, text
    except ImportError as exc:
        raise DatabaseUnavailable("DATABASE_DRIVER_MISSING: install backend/requirements.txt") from exc
    if table not in {"support_tickets", "generated_reports"}:
        raise ValueError("WRITE_BLOCKED: table is not an approved persistence target")
    columns = ", ".join(values)
    placeholders = ", ".join(f":{key}" for key in values)
    engine = create_engine(database_url(), pool_pre_ping=True)
    with engine.begin() as connection:
        connection.execute(text(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"), values)
    return {"table": table, "persisted": True, "values": values}
