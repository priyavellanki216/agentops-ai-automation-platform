from __future__ import annotations

import os
from typing import Any


class LLMUnavailable(RuntimeError):
    pass


def generate_grounded_answer(query: str, evidence: list[dict[str, Any]]) -> str:
    """Call OpenAI only when configured; never answer without evidence."""
    if not evidence:
        raise LLMUnavailable("EVIDENCE_INSUFFICIENT: answer generation requires evidence")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "OpenAI provider is not configured; evidence collection completed without generating an answer."
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        input=[
            {"role": "system", "content": "Answer only from supplied evidence. Cite source IDs in square brackets."},
            {"role": "user", "content": f"Question: {query}\nEvidence: {evidence}"},
        ],
    )
    return response.output_text
