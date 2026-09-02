import pytest

from backend.app.tool_handlers import CustomerInput, QueryInput, create_ticket, get_customer, query_database
from backend.app.services.mcp_client import MCPClient


def test_customer_tool_is_typed_and_traceable() -> None:
    result = get_customer(CustomerInput(customer_id="cus_123"), "viewer", MCPClient("viewer_key"))
    assert result.ok is True
    assert result.trace_id.startswith("trace_")


def test_query_tool_requires_approved_view() -> None:
    with pytest.raises(ValueError, match="SQL_BLOCKED"):
        query_database(QueryInput(sql="SELECT * FROM raw_transactions"), "analyst")


def test_ticket_creation_is_role_restricted() -> None:
    with pytest.raises(PermissionError, match="ROLE_DENIED"):
        create_ticket("Billing issue", "viewer", lambda subject: {"subject": subject})
