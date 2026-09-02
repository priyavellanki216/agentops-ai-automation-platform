import pytest

from backend.app.services.llm import LLMUnavailable, generate_grounded_answer


def test_llm_adapter_requires_evidence() -> None:
    with pytest.raises(LLMUnavailable, match="EVIDENCE_INSUFFICIENT"):
        generate_grounded_answer("What happened?", [])
