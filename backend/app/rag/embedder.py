"""Pluggable embedding interface.

Default: local `sentence-transformers` model (bge-small-en-v1.5, 384 dims).
Alternative: OpenAI text-embedding-3-small (1536 dims — set EMBED_DIM=1536).

The chosen provider must produce vectors with EMBED_DIM dimensions to match the
`chunks.embedding` column.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings


class EmbeddingProvider:
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class LocalEmbedder(EmbeddingProvider):
    """sentence-transformers, CPU friendly. Loaded lazily on first use."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        self.dim = self._model.get_sentence_embedding_dimension() or settings.embed_dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vecs = self._model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=32,
        )
        return [v.tolist() for v in vecs]


class OpenAIEmbedder(EmbeddingProvider):
    def __init__(self, model_name: str) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = model_name
        # text-embedding-3-small = 1536, text-embedding-3-large = 3072
        self.dim = settings.embed_dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        resp = self._client.embeddings.create(model=self._model, input=texts)
        return [d.embedding for d in resp.data]


@lru_cache(maxsize=1)
def get_embedder() -> EmbeddingProvider:
    if settings.embed_provider == "openai":
        return OpenAIEmbedder(settings.openai_embed_model)
    return LocalEmbedder(settings.embed_model_local)
