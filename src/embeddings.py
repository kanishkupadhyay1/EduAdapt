"""Stage 5 - Turn text into embeddings (lists of numbers that capture meaning).

Beginner explanation
--------------------
An *embedding model* reads a piece of text and outputs a fixed-length list of
numbers, called a *vector* (for all-MiniLM-L6-v2: 384 numbers). Texts with
similar MEANING get similar vectors, even if they share no words, so
"how do I store a memory address?" ends up close to a paragraph about
pointers. Searching then means: embed the question, find the stored vectors
closest to it.

"Closeness" is measured with *cosine similarity* (a number from about 0 to 1;
higher = more similar). We ask the model to normalise vectors to length 1,
which makes cosine similarity equal to a simple multiplication and keeps the
scores comparable.

This file
---------
* loads the model ONCE (loading takes seconds), only when first needed,
* encodes many chunks at a time (batching is much faster),
* encodes a user query and remembers recent queries so the same question
  is not computed twice,
* lets you choose the model by name (default is set in config.py).

The first time a model is used it is downloaded from the internet and stored
in your computer's cache. After that it works offline.
"""

import logging
from collections import OrderedDict
from typing import Protocol

from src import config

logger = logging.getLogger(__name__)


class EmbedderProtocol(Protocol):
    """What the rest of the code expects from an embedder.

    Any object with these three members works (our real Embedder, or the
    small fake one used in tests)."""

    @property
    def dimension(self) -> int: ...

    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, query: str) -> list[float]: ...


class Embedder:
    """Sentence-transformer embedding model with lazy loading + query cache."""

    def __init__(
        self,
        model_name: str = config.EMBEDDING_MODEL_NAME,
        batch_size: int = config.EMBEDDING_BATCH_SIZE,
        query_cache_size: int = config.QUERY_CACHE_SIZE,
        local_files_only: bool = False,
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self._query_cache_size = query_cache_size
        self._local_files_only = local_files_only
        self._model = None  # loaded on first use
        self._query_cache: OrderedDict[str, list[float]] = OrderedDict()

    # -- model loading ------------------------------------------------------
    @property
    def model(self):
        """The loaded SentenceTransformer (loaded only once)."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise ImportError(
                    "sentence-transformers is not installed. It should already be in the "
                    "team environment; check you are using the right Python/venv."
                ) from exc
            logger.info("Loading embedding model '%s' (first run downloads it)...", self.model_name)
            try:
                self._model = SentenceTransformer(
                    self.model_name, local_files_only=self._local_files_only
                )
            except Exception as exc:
                raise RuntimeError(
                    f"Could not load embedding model '{self.model_name}'. The first run needs "
                    "an internet connection to download it (afterwards it is cached). "
                    f"Original error: {exc}"
                ) from exc
        return self._model

    @property
    def dimension(self) -> int:
        """How many numbers each vector has (384 for all-MiniLM-L6-v2)."""
        return int(self.model.get_sentence_embedding_dimension())

    # -- encoding -----------------------------------------------------------
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Encode many texts (e.g. all chunks) -> list of vectors."""
        if not texts:
            return []
        vectors = self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return vectors.tolist()

    def embed_query(self, query: str) -> list[float]:
        """Encode one user question. Recent questions are cached."""
        key = query.strip()
        if not key:
            raise ValueError("Query is empty.")
        if key in self._query_cache:
            self._query_cache.move_to_end(key)
            return self._query_cache[key]
        vector = self.embed_texts([key])[0]
        self._query_cache[key] = vector
        if len(self._query_cache) > self._query_cache_size:
            self._query_cache.popitem(last=False)
        return vector
