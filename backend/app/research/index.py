"""Qdrant storage for source passages and earlier research memory.

One collection holds every session. A search for the current session uses a
lower similarity bar. A passage from another session is returned only when it
is clearly similar, and it is labelled with that session. Unrelated topics
fall under the bar and are not returned.
"""

import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import PROJECT_ROOT, get_settings
from app.research.chunks import chunk_text, clean_text
from app.research.embeddings import embedder_from_settings

_NAMESPACE = uuid.UUID("6c8d1c0a-7c1e-4a4e-9b1a-1f0a0b0c0d0e")


class EvidenceIndex:
    def __init__(self, client: QdrantClient, embedder, collection: str):
        self.client = client
        self.embedder = embedder
        self.collection = collection
        self._ready = False

    def upsert_source(self, session_id: str, source: dict) -> int:
        session_id = _required_id(session_id, "session_id")
        url = (source.get("url") or "").strip()
        text = clean_text(source.get("content") or source.get("snippet") or "")
        if not url or not text:
            return 0
        settings = get_settings()
        pieces = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        if not pieces:
            return 0
        self._ensure()
        self._delete_source(session_id, url)
        retrieved_at = source.get("retrieved_at") or _now()
        vectors = self.embedder.embed(pieces)
        points = []
        for index, (piece, vector) in enumerate(zip(pieces, vectors)):
            points.append(
                PointStruct(
                    id=str(uuid.uuid5(_NAMESPACE, f"{session_id}|{url}|{index}")),
                    vector=vector,
                    payload={
                        "session_id": session_id,
                        "source_id": source.get("id") or "",
                        "url": url,
                        "title": source.get("title") or url,
                        "domain": source.get("domain") or "",
                        "author": source.get("author") or "",
                        "published_on": source.get("published_on") or "",
                        "retrieved_at": retrieved_at,
                        "chunk_index": index,
                        "text": piece,
                    },
                )
            )
        self.client.upsert(collection_name=self.collection, points=points)
        return len(points)

    def lookup_url(self, url: str) -> dict | None:
        url = (url or "").strip()
        if not url or not self._exists():
            return None
        points, _offset = self.client.scroll(
            collection_name=self.collection,
            scroll_filter=Filter(must=[FieldCondition(key="url", match=MatchValue(value=url))]),
            limit=64,
            with_payload=True,
        )
        if not points:
            return None
        newest = max(points, key=lambda point: point.payload.get("retrieved_at") or "")
        retrieved_at = newest.payload.get("retrieved_at") or ""
        same_copy = [
            point
            for point in points
            if point.payload.get("session_id") == newest.payload.get("session_id")
            and point.payload.get("retrieved_at") == retrieved_at
        ]
        same_copy.sort(key=lambda point: point.payload.get("chunk_index") or 0)
        return {
            "text": " ".join(point.payload.get("text") or "" for point in same_copy).strip(),
            "retrieved_at": retrieved_at,
            "possibly_outdated": _is_outdated(retrieved_at),
            "session_id": newest.payload.get("session_id") or "",
            "source_id": newest.payload.get("source_id") or "",
            "title": newest.payload.get("title") or "",
            "url": url,
        }

    def search(self, query: str, session_id: str, limit: int = 4) -> list[dict]:
        query = clean_text(query)
        session_id = (session_id or "").strip()
        if not query or not session_id or not self._exists():
            return []
        settings = get_settings()
        vector = self.embedder.embed([query])[0]
        current = self._query(
            vector,
            Filter(must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))]),
            limit,
            settings.retrieval_min_score,
        )
        memory = self._query(
            vector,
            Filter(must_not=[FieldCondition(key="session_id", match=MatchValue(value=session_id))]),
            limit,
            settings.memory_min_score,
        )
        passages = [_passage(hit, from_memory=False) for hit in current]
        passages.extend(_passage(hit, from_memory=True) for hit in memory)
        passages.sort(key=lambda item: item["score"], reverse=True)
        return passages[:limit]

    def _query(self, vector, query_filter, limit: int, threshold: float):
        response = self.client.query_points(
            collection_name=self.collection,
            query=vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=threshold,
            with_payload=True,
        )
        return list(response.points)

    def _ensure(self) -> None:
        if self._ready:
            return
        size = self.embedder.dimension
        if self.client.collection_exists(self.collection):
            current = _vector_size(self.client.get_collection(self.collection))
            if current != size:
                self.client.delete_collection(self.collection)
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=size, distance=Distance.COSINE),
            )
        self._ready = True

    def _exists(self) -> bool:
        if self._ready:
            return True
        return self.client.collection_exists(self.collection)

    def _delete_source(self, session_id: str, url: str) -> None:
        self.client.delete(
            collection_name=self.collection,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(key="session_id", match=MatchValue(value=session_id)),
                        FieldCondition(key="url", match=MatchValue(value=url)),
                    ]
                )
            ),
        )


def _passage(hit, *, from_memory: bool) -> dict:
    payload = hit.payload or {}
    retrieved_at = payload.get("retrieved_at") or ""
    return {
        "text": payload.get("text") or "",
        "url": payload.get("url") or "",
        "title": payload.get("title") or "",
        "source_id": payload.get("source_id") or "",
        "session_id": payload.get("session_id") or "",
        "score": round(float(hit.score), 4),
        "retrieved_at": retrieved_at,
        "possibly_outdated": _is_outdated(retrieved_at),
        "from_memory": from_memory,
    }


def _is_outdated(retrieved_at: str) -> bool:
    if not retrieved_at:
        return True
    try:
        when = datetime.fromisoformat(retrieved_at)
    except ValueError:
        return True
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    window = timedelta(days=get_settings().memory_fresh_days)
    return datetime.now(timezone.utc) - when > window


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _required_id(value: str, name: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except ValueError as exc:
        raise ValueError(f"{name} must be a UUID.") from exc


def _vector_size(info) -> int:
    vectors = info.config.params.vectors
    if hasattr(vectors, "size"):
        return int(vectors.size)
    if isinstance(vectors, dict) and vectors:
        first = next(iter(vectors.values()))
        return int(first.size)
    return 0


@lru_cache
def get_index() -> EvidenceIndex:
    settings = get_settings()
    if settings.qdrant_url:
        client = QdrantClient(url=settings.qdrant_url, timeout=10)
    elif settings.qdrant_path == ":memory:":
        client = QdrantClient(":memory:")
    else:
        path = settings.qdrant_path or str(PROJECT_ROOT / ".qdrant")
        client = QdrantClient(path=path, timeout=10)
    return EvidenceIndex(
        client=client,
        embedder=embedder_from_settings(settings),
        collection=settings.qdrant_collection,
    )
