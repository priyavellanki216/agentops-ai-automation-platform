from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DocumentChunk:
    document_id: str
    title: str
    section: str
    source: str
    content: str
    metadata: dict[str, Any]


def chunk_document(
    document_id: str,
    title: str,
    source: str,
    text: str,
    *,
    section: str = "body",
    chunk_size: int = 900,
    overlap: int = 120,
    metadata: dict[str, Any] | None = None,
) -> list[DocumentChunk]:
    if chunk_size <= overlap or chunk_size < 1:
        raise ValueError("CHUNK_CONFIG_INVALID: chunk_size must be greater than overlap")
    normalized = " ".join(text.split())
    chunks: list[DocumentChunk] = []
    step = chunk_size - overlap
    for start in range(0, len(normalized), step):
        content = normalized[start : start + chunk_size]
        if content:
            chunks.append(DocumentChunk(document_id, title, section, source, content, metadata or {}))
    return chunks


def embed_text(text: str) -> list[float]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("EMBEDDING_PROVIDER_UNAVAILABLE: configure OPENAI_API_KEY")
    from openai import OpenAI

    response = OpenAI(api_key=api_key).embeddings.create(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"), input=text
    )
    return response.data[0].embedding
