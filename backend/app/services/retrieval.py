from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: str
    title: str
    section: str
    source: str
    relevance: float
    content: str
    metadata: dict[str, Any]


class EvidenceInsufficient(Exception):
    pass


def build_pgvector_query(
    embedding: list[float], source: str | None = None, metadata: dict[str, str] | None = None, limit: int = 5
) -> tuple[str, dict[str, Any]]:
    """Build a parameterized cosine-distance query; callers bind values via a DB driver."""
    if not embedding or len(embedding) != 1536:
        raise ValueError("EMBEDDING_INVALID: expected a 1536-dimensional embedding")
    if not 1 <= limit <= 20:
        raise ValueError("LIMIT_INVALID: retrieval limit must be between 1 and 20")
    sql = "SELECT d.id AS document_id, d.title, c.section, d.source, 1 - (c.embedding <=> :embedding) AS relevance, c.content, d.metadata FROM document_chunks c JOIN documents d ON d.id = c.document_id"
    params: dict[str, Any] = {"embedding": embedding, "limit": limit}
    filters: list[str] = []
    if source:
        filters.append("d.source = :source")
        params["source"] = source
    if metadata:
        filters.append("d.metadata @> CAST(:metadata AS jsonb)")
        params["metadata"] = json.dumps(metadata)
    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += " ORDER BY c.embedding <=> :embedding LIMIT :limit"
    return sql, params


def evidence_gate(
    chunks: list[RetrievedChunk], minimum_score: float = 0.72, minimum_chunks: int = 1
) -> list[RetrievedChunk]:
    accepted = [chunk for chunk in chunks if chunk.relevance >= minimum_score]
    if len(accepted) < minimum_chunks:
        raise EvidenceInsufficient("EVIDENCE_INSUFFICIENT: no grounded answer should be generated")
    return accepted
