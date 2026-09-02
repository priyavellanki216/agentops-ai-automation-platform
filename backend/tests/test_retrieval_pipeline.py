import pytest

from backend.app.services.ingestion import chunk_document, embed_text
from backend.app.services.retrieval import build_pgvector_query
from backend.app.tool_handlers import search_knowledge_base


def test_chunk_document_preserves_metadata() -> None:
    chunks = chunk_document("doc-1", "Policy", "internal", "one two three four five", chunk_size=12, overlap=3, metadata={"team": "support"})
    assert len(chunks) >= 2
    assert all(chunk.metadata["team"] == "support" for chunk in chunks)


def test_pgvector_query_supports_source_and_metadata_filters() -> None:
    sql, params = build_pgvector_query([0.0] * 1536, source="runbooks", metadata={"team": "support"}, limit=5)
    assert "d.source = :source" in sql
    assert "d.metadata @> CAST(:metadata AS jsonb)" in sql
    assert params["source"] == "runbooks"


def test_search_knowledge_base_executes_and_gates_stored_chunk_results() -> None:
    def executor(sql: str, params: dict[str, object]) -> list[dict[str, object]]:
        assert "ORDER BY c.embedding" in sql
        assert "d.metadata @> CAST(:metadata AS jsonb)" in sql
        assert params["limit"] == 5
        assert params["metadata"] == '{"team": "support"}'
        return [{"document_id": "d1", "title": "Runbook", "section": "Auth", "source": "internal", "relevance": .93, "content": "Rotate the session key.", "metadata": {"team": "support"}}]
    result = search_knowledge_base("How do I rotate a session key?", "viewer", [0.0] * 1536, {"team": "support"}, executor)
    assert result.ok is True
    assert result.evidence[0]["relevance"] == .93


def test_embedding_requires_provider_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="EMBEDDING_PROVIDER_UNAVAILABLE"):
        embed_text("hello")
