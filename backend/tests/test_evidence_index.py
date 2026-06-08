import uuid
from datetime import datetime, timedelta, timezone

from qdrant_client import QdrantClient

from app.mcp import tools
from app.research.chunks import chunk_text, clean_text
from app.research.embeddings import HashingEmbedder
from app.research.index import EvidenceIndex

SLEEP = (
    "Adults who slept seven hours recalled 20 percent more word pairs than adults "
    "who slept four hours. The study measured memory consolidation after sleep."
)
STEEL = (
    "The steel mill reported quarterly revenue of 4 billion dollars after shipping "
    "finished coils to industrial customers across the region."
)
SLEEP_URL = "https://example.edu/sleep-study"
STEEL_URL = "https://example.edu/steel-revenue"


def _index() -> EvidenceIndex:
    return EvidenceIndex(QdrantClient(":memory:"), HashingEmbedder(), "evidence-test")


def _source(url: str, text: str, retrieved_at: str | None = None) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "url": url,
        "title": url,
        "content": text,
        "retrieved_at": retrieved_at or datetime.now(timezone.utc).isoformat(),
    }


def test_chunks_keep_the_cleaned_passage():
    raw = "  Sleep   supports\nmemory.\x00  "
    assert clean_text(raw) == "Sleep supports memory."
    pieces = chunk_text(SLEEP + " " + ("detail " * 200), size=240, overlap=40)
    assert len(pieces) > 1
    assert all(piece == " ".join(piece.split()) for piece in pieces)


def test_ingestion_stores_source_metadata_and_retrieves_the_passage():
    index = _index()
    session_id = str(uuid.uuid4())
    source = _source(SLEEP_URL, SLEEP)
    assert index.upsert_source(session_id, source) >= 1

    hits = index.search("memory consolidation after sleep", session_id)
    assert hits
    assert hits[0]["url"] == SLEEP_URL
    assert hits[0]["source_id"] == source["id"]
    assert hits[0]["session_id"] == session_id
    assert hits[0]["title"] == SLEEP_URL
    assert "20 percent" in hits[0]["text"]
    assert hits[0]["from_memory"] is False
    assert hits[0]["possibly_outdated"] is False


def test_metadata_filter_keeps_another_sessions_unrelated_passage_out():
    index = _index()
    sleep_session = str(uuid.uuid4())
    steel_session = str(uuid.uuid4())
    index.upsert_source(sleep_session, _source(SLEEP_URL, SLEEP))
    index.upsert_source(steel_session, _source(STEEL_URL, STEEL))

    about_steel = index.search("quarterly steel mill revenue and coils", sleep_session)
    assert any(hit["url"] == STEEL_URL and hit["from_memory"] for hit in about_steel)
    assert all(hit["url"] != SLEEP_URL for hit in about_steel)

    about_sleep = index.search("sleep memory consolidation word pairs", steel_session)
    assert any(hit["url"] == SLEEP_URL and hit["session_id"] == sleep_session for hit in about_sleep)
    assert all(hit["url"] != STEEL_URL for hit in about_sleep)


def test_old_passage_is_marked_outdated_and_a_fresh_copy_is_reused():
    index = _index()
    session_id = str(uuid.uuid4())
    old = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    index.upsert_source(session_id, _source(SLEEP_URL, SLEEP, retrieved_at=old))

    stored = index.lookup_url(SLEEP_URL)
    assert stored is not None
    assert stored["possibly_outdated"] is True
    hits = index.search("sleep and memory consolidation", session_id)
    assert hits[0]["possibly_outdated"] is True

    calls = {"count": 0}

    def fetch(url, limit):
        calls["count"] += 1
        return SLEEP

    tools.get_index.cache_clear()
    original_index = tools.get_index
    original_fetch = tools.fetch_page_text
    tools.get_index = lambda: index
    tools.fetch_page_text = fetch
    try:
        fresh_session = str(uuid.uuid4())
        first = tools.retrieve_source(SLEEP_URL, 4000, fresh_session, str(uuid.uuid4()), "Sleep study")
        assert calls["count"] == 1
        assert first["reused"] is False
        second = tools.retrieve_source(SLEEP_URL, 4000, str(uuid.uuid4()), str(uuid.uuid4()), "Sleep study")
        assert calls["count"] == 1
        assert second["reused"] is True
        assert second["text"]
    finally:
        tools.get_index = original_index
        tools.fetch_page_text = original_fetch
        tools.get_index.cache_clear()


def test_retrieve_rejects_a_bad_url_and_search_rejects_a_bad_session():
    try:
        tools.retrieve_source("notaurl")
        raise AssertionError("expected a bad url to fail")
    except tools.ToolInputError as exc:
        assert "http" in str(exc)
    try:
        tools.search_evidence("sleep", "not-a-session")
        raise AssertionError("expected a bad session to fail")
    except tools.ToolInputError as exc:
        assert "session_id" in str(exc)
