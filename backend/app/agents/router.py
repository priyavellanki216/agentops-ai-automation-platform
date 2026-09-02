from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolPlan:
    intent: str
    tools: tuple[str, ...]
    requires_evidence: bool = True


def route_request(query: str) -> ToolPlan:
    text = query.lower()
    if "campaign" in text or "region" in text:
        return ToolPlan("campaign_performance", ("query_database", "calculate_metrics"))
    if "invoice" in text or "transaction" in text or "payment" in text:
        return ToolPlan("financial_analysis", ("get_financial_summary", "calculate_metrics"))
    if "ticket" in text or "support" in text or "customer" in text:
        return ToolPlan("customer_support", ("query_database", "search_knowledge_base"))
    if "incident" in text or "outage" in text:
        return ToolPlan("incident_analysis", ("get_incident_details", "search_knowledge_base"))
    return ToolPlan("knowledge_lookup", ("search_knowledge_base",))
