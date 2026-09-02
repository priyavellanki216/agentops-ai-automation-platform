from __future__ import annotations

from typing import TypedDict

from .router import ToolPlan, route_request
from ..observability.tracing import TraceEnvelope


class AgentState(TypedDict, total=False):
    query: str
    role: str
    plan: ToolPlan
    evidence: list[dict[str, object]]
    answer: str
    trace_id: str


def parse_request(state: AgentState) -> AgentState:
    trace = TraceEnvelope()
    trace.event("request_parsed", query_length=len(state["query"]))
    return {**state, "trace_id": trace.trace_id}


def plan_tools(state: AgentState) -> AgentState:
    plan = route_request(state["query"])
    return {**state, "plan": plan}


def ground_answer(state: AgentState) -> AgentState:
    if not state.get("evidence"):
        return {**state, "answer": "Insufficient evidence to provide a grounded answer."}
    return {**state, "answer": "Grounded answer generation is ready for the configured OpenAI provider."}


def build_graph():
    """Build a LangGraph state machine when LangGraph is installed in the runtime."""
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise RuntimeError("Install backend/requirements.txt to enable LangGraph orchestration") from exc
    graph = StateGraph(AgentState)
    graph.add_node("parse_request", parse_request)
    graph.add_node("plan_tools", plan_tools)
    graph.add_node("ground_answer", ground_answer)
    graph.add_edge(START, "parse_request")
    graph.add_edge("parse_request", "plan_tools")
    graph.add_edge("plan_tools", "ground_answer")
    graph.add_edge("ground_answer", END)
    return graph.compile()
