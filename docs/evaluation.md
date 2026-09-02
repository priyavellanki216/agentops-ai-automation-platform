# Evaluation

The evaluation runner maintains a 30-case benchmark inventory with expected tools and evidence domains. When measured per-case JSON is supplied, it calculates tool-selection accuracy, argument accuracy, answer correctness, groundedness, retrieval precision/recall, task success, failure rate, average latency, and p95 latency.

A baseline and current metric artifact can be compared with configured minimum and maximum thresholds. CI requires both artifacts and fails closed when they are absent, preventing a green result from an unmeasured run. JSON and Markdown reports include the evaluation trace ID. The repository does not fabricate benchmark scores.
