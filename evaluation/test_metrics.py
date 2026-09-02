from evaluation.run import compare_versions, metric_summary


def test_metric_summary_uses_measured_case_results() -> None:
    metrics = metric_summary([
        {"task_success": True, "failure": False, "groundedness": .9, "tool_selection_accuracy": 1, "latency_ms": 100},
        {"task_success": False, "failure": True, "groundedness": .5, "tool_selection_accuracy": 0, "latency_ms": 200},
    ])
    assert metrics["task_success_rate"] == .5
    assert metrics["failure_rate"] == .5
    assert metrics["p95_latency_ms"] == 100


def test_ci_gate_requires_measured_artifacts() -> None:
    result = compare_versions({}, {}, {"minimum_task_success": .85})
    assert result["status"] == "not_run"
    assert "required" in result["message"]


def test_compare_versions_fails_only_on_configured_regressions() -> None:
    result = compare_versions(
        {"task_success_rate": .95, "groundedness": .95, "failure_rate": .01, "p95_latency_ms": 100},
        {"task_success_rate": .8, "groundedness": .91, "failure_rate": .02, "p95_latency_ms": 110},
        {"minimum_task_success": .85, "minimum_groundedness": .90, "maximum_failure_rate": .05, "maximum_latency_regression": .20},
    )
    assert result["status"] == "fail"
    assert result["regressions"][0]["metric"] == "task_success_rate"
