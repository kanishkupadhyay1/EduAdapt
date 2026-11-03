"""Stage 7 - Semantic retrieval: question in, best-matching chunks out.

The steps are always the same (no decisions, no loops, no LLM calls):

    question -> embedding -> Qdrant nearest-neighbour search -> readable results

``score`` is cosine similarity: higher = closer in meaning. Roughly 1.0 means
almost identical meaning and values near 0 mean unrelated. Treat scores as a
RANKING aid, not as a probability: what counts as "good enough" depends on
the model and the material, so check real scores on real PPS queries.
"""

import logging
from typing import Any

from src import config
from src.embeddings import EmbedderProtocol
from src.vector_store import VectorStore

logger = logging.getLogger(__name__)

Result = dict[str, Any]


class Retriever:
    """Finds the PPS chunks most relevant to a natural-language question."""

    def __init__(
        self,
        embedder: EmbedderProtocol,
        store: VectorStore,
        default_top_k: int = config.TOP_K,
    ) -> None:
        self.embedder = embedder
        self.store = store
        self.default_top_k = default_top_k

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        min_score: float | None = None,
    ) -> list[Result]:
        """Return up to ``top_k`` results, best first.

        Each result: {"text", "score", "source", "page", "module", "topic", "chunk_id"}.
        ``min_score`` (optional) drops results scoring below it.
        """
        if not query or not query.strip():
            raise ValueError("Query is empty. Ask a question such as 'Explain pointers in C'.")
        k = self.default_top_k if top_k is None else top_k
        if k < 1:
            raise ValueError("top_k must be at least 1.")

        hits = self.store.search(self.embedder.embed_query(query), top_k=k)
        results: list[Result] = []
        for hit in hits:
            payload = hit["payload"]
            if min_score is not None and hit["score"] < min_score:
                continue
            results.append({
                "text": payload.get("text", ""),
                "score": hit["score"],
                "source": payload.get("source", config.UNKNOWN_LABEL),
                "page": payload.get("page"),
                "module": payload.get("module", config.UNKNOWN_LABEL),
                "topic": payload.get("topic", config.UNKNOWN_LABEL),
                "chunk_id": payload.get("chunk_id", ""),
            })
        return results
