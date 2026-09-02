"""Deterministic evaluation entry point with measured-only regression gates."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from backend.app.observability.tracing import TraceEnvelope
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from backend.app.observability.tracing import TraceEnvelope


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    query: str
    expected_tools: tuple[str, ...]
    expected_evidence: str


CASES = [
    EvaluationCase(f"case-{i:02d}", query, tuple(tools), evidence)
    for i, (query, tools, evidence) in enumerate(
        [
            ("Compare support tickets by customer segment", ["query_database"], "support_tickets"),
            ("Find unresolved high priority tickets", ["query_database"], "support_tickets"),
            ("Summarize failed transactions last week", ["get_financial_summary", "calculate_metrics"], "transactions"),
            ("Compare campaigns across regions", ["query_database", "calculate_metrics"], "campaigns"),
            ("Identify product areas with most incidents", ["get_product_metrics", "query_database"], "incidents"),
            ("Find customer invoice exposure", ["get_customer", "get_financial_summary"], "invoices"),
        ]
        * 5,
        start=1,
    )
]


def metric_summary(results: list[dict[str, Any]]) -> dict[str, float]:
    """Calculate metrics from measured per-case results; missing values stay excluded."""
    if not results:
        return {}

    def average(key: str) -> float:
        values = [float(item[key]) for item in results if item.get(key) is not None]
        return sum(values) / len(values) if values else 0.0

    successes = [item for item in results if item.get("task_success") is not None]
    failures = [item for item in results if item.get("failure")]
    return {
        "tool_selection_accuracy": average("tool_selection_accuracy"),
        "tool_argument_accuracy": average("tool_argument_accuracy"),
        "answer_correctness": average("answer_correctness"),
        "groundedness": average("groundedness"),
        "retrieval_precision": average("retrieval_precision"),
        "retrieval_recall": average("retrieval_recall"),
        "task_success_rate": sum(bool(item["task_success"]) for item in successes) / len(successes)
        if successes
        else 0.0,
        "failure_rate": len(failures) / len(results),
        "average_latency_ms": average("latency_ms"),
        "p95_latency_ms": sorted(float(item["latency_ms"]) for item in results if item.get("latency_ms") is not None)[
            max(0, int(len(results) * 0.95) - 1)
        ]
        if any(item.get("latency_ms") is not None for item in results)
        else 0.0,
    }


def compare_versions(
    baseline: dict[str, float], current: dict[str, float], thresholds: dict[str, float]
) -> dict[str, Any]:
    """Return pass/fail without inventing a baseline or current run."""
    if not baseline or not current:
        return {
            "status": "not_run",
            "regressions": [],
            "message": "Both measured baseline and current metrics are required.",
        }
    regressions: list[dict[str, float | str]] = []
    for metric, minimum in (
        ("task_success_rate", thresholds.get("minimum_task_success", 0.0)),
        ("groundedness", thresholds.get("minimum_groundedness", 0.0)),
    ):
        if current.get(metric, 0.0) < minimum:
            regressions.append({"metric": metric, "value": current.get(metric, 0.0), "threshold": minimum})
    if current.get("failure_rate", 0.0) > thresholds.get("maximum_failure_rate", 1.0):
        regressions.append(
            {
                "metric": "failure_rate",
                "value": current.get("failure_rate", 0.0),
                "threshold": thresholds.get("maximum_failure_rate", 1.0),
            }
        )
    baseline_latency = baseline.get("p95_latency_ms", 0.0)
    if baseline_latency and current.get("p95_latency_ms", 0.0) > baseline_latency * (
        1 + thresholds.get("maximum_latency_regression", 1.0)
    ):
        regressions.append(
            {"metric": "p95_latency_ms", "value": current.get("p95_latency_ms", 0.0), "baseline": baseline_latency}
        )
    return {"status": "fail" if regressions else "pass", "regressions": regressions}


def load_thresholds(path: Path) -> dict[str, float]:
    thresholds: dict[str, float] = {}
    if not path.exists():
        return thresholds
    for line in path.read_text().splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.strip().split(":", 1)
        try:
            thresholds[key.strip()] = float(value.strip())
        except ValueError:
            continue
    return thresholds


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="evaluation/config.yaml")
    parser.add_argument("--input", help="JSON file containing measured per-case results")
    parser.add_argument("--baseline", help="JSON file containing measured baseline metrics")
    parser.add_argument("--fail-on-regression", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).parent
    trace = TraceEnvelope(agent_version="evaluation")
    trace.event("evaluation_started", case_count=len(CASES), input_supplied=bool(args.input))
    results = json.loads(Path(args.input).read_text()) if args.input else []
    baseline = json.loads(Path(args.baseline).read_text()) if args.baseline else {}
    current = metric_summary(results) if isinstance(results, list) else results.get("metrics", {})
    thresholds = {
        "minimum_task_success": 0.85,
        "minimum_groundedness": 0.90,
        "maximum_failure_rate": 0.05,
        "maximum_latency_regression": 0.20,
    }
    thresholds.update(load_thresholds(Path(args.config)))
    comparison = compare_versions(baseline, current, thresholds)
    if args.fail_on_regression and (not results or not baseline):
        comparison = {
            "status": "fail",
            "regressions": [
                {
                    "metric": "evaluation_artifacts",
                    "message": "Measured current and baseline artifacts are required for CI.",
                }
            ],
        }
    trace.event("evaluation_metrics_computed", measured=bool(results), status=comparison["status"], metrics=current)
    trace_payload = trace.finish()
    payload = {
        "status": comparison["status"],
        "measured": bool(results),
        "case_count": len(CASES),
        "metrics": current,
        "comparison": comparison,
        "trace_id": trace_payload["trace_id"],
        "generated_at": datetime.now(UTC).isoformat(),
        "cases": [asdict(case) for case in CASES],
    }
    (root / "results").mkdir(exist_ok=True)
    (root / "reports").mkdir(exist_ok=True)
    (root / "results/latest.json").write_text(json.dumps(payload, indent=2) + "\n")
    (root / "reports/report.md").write_text(
        "# AgentOps evaluation report\n\n"
        + (
            "Measured metrics are reported below.\n\n"
            if results
            else "No provider-backed run has been supplied; metrics are intentionally not fabricated.\n\n"
        )
        + f"Case inventory: **{len(CASES)}**\n\nTrace ID: **{trace_payload['trace_id']}**\n\nStatus: **{comparison['status'].upper()}**\n\n```json\n{json.dumps(current, indent=2)}\n```\n"
    )
    return 1 if args.fail_on_regression and comparison["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
