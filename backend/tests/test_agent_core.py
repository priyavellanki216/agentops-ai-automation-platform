import pytest

from backend.app.agents.router import route_request
from backend.app.db import DatabaseUnavailable, database_url, query_approved_view
from backend.app.services.retrieval import (
    EvidenceInsufficient,
    RetrievedChunk,
    evidence_gate,
)
from backend.app.tools import authorize_tool, validate_approved_sql, with_retry


def test_router_selects_finance_tools() -> None:
    assert route_request("What caused failed transactions?").tools == ("get_financial_summary", "calculate_metrics")


def test_database_boundary_returns_parameterized_approved_view_envelope() -> None:
    result = query_approved_view("SELECT * FROM campaign_performance", {"region": "NA"})
    assert result["source"] == "approved_view"
    assert result["parameters"]["region"] == "NA"


def test_database_url_requires_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(DatabaseUnavailable):
        database_url()


def test_sql_layer_blocks_destructive_queries() -> None:
    with pytest.raises(ValueError, match="SQL_BLOCKED"):
        validate_approved_sql("DROP VIEW customer_support_summary")
    assert validate_approved_sql("SELECT * FROM customer_support_summary")


def test_role_restriction_is_deny_by_default() -> None:
    with pytest.raises(PermissionError, match="ROLE_DENIED"):
        authorize_tool("get_financial_summary", "viewer")


def test_retry_recovers_from_transient_tool_failure() -> None:
    attempts = {"count": 0}

    def operation() -> str:
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("temporary")
        return "ok"

    assert with_retry(operation, attempts=3) == "ok"


def test_evidence_gate_abstains_below_threshold() -> None:
    with pytest.raises(EvidenceInsufficient):
        evidence_gate([RetrievedChunk("d1", "Runbook", "A", "internal", 0.4, "text", {})])
