"""Text embeddings kept apart from the chat model.

fastembed loads BAAI/bge-small-en-v1.5 locally. The hashing embedder is the
stand-in used by tests and by EMBEDDING_PROVIDER=hash. It uses a stable
feature hash, so a query and a passage agree across processes.
"""

import hashlib
import re

TOKEN = re.compile(r"[a-z0-9]+")
HASH_DIMENSION = 512


class HashingEmbedder:
    dimension = HASH_DIMENSION

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [_hash_vector(text) for text in texts]


class FastEmbedder:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        self._dimension = 0

    @property
    def dimension(self) -> int:
        if not self._dimension:
            self._dimension = len(self.embed(["dimension"])[0])
        return self._dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(model_name=self.model_name)
        rows = []
        for vector in self._model.embed(texts):
            rows.append([float(value) for value in vector])
        if rows and not self._dimension:
            self._dimension = len(rows[0])
        return rows


def embedder_from_settings(settings) -> HashingEmbedder | FastEmbedder:
    provider = (settings.embedding_provider or "fastembed").strip().lower()
    if provider == "hash":
        return HashingEmbedder()
    if provider == "fastembed":
        return FastEmbedder(settings.embedding_model)
    raise ValueError(f"Embedding provider '{settings.embedding_provider}' is not supported.")


def _hash_vector(text: str) -> list[float]:
    tokens = TOKEN.findall(text.lower())
    vector = [0.0] * HASH_DIMENSION
    grams = list(tokens)
    grams.extend(f"{left}_{right}" for left, right in zip(tokens, tokens[1:]))
    compact = re.sub(r"[^a-z0-9 ]", "", text.lower())
    grams.extend(compact[index : index + 4] for index in range(max(len(compact) - 3, 0)))
    if not grams:
        return vector
    for gram in grams:
        digest = hashlib.blake2b(gram.encode("utf-8"), digest_size=8).digest()
        number = int.from_bytes(digest, "little")
        vector[number % HASH_DIMENSION] += 1.0
    norm = sum(value * value for value in vector) ** 0.5
    if norm == 0:
        return vector
    return [value / norm for value in vector]
