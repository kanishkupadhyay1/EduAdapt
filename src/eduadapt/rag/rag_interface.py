"""PPS Curriculum RAG hand-off interface implementing EduAdapt canonical contract.

Connects Member 2's semantic retrieval pipeline to Member 1's TeachingGenerator
via the canonical RAGInterface contract defined in eduadapt.interfaces.rag.
Strictly non-agentic: retrieval is a single deterministic semantic vector search.
"""

import logging
from pathlib import Path
from typing import Any, Optional

from eduadapt.interfaces.rag import RAGDocument, RAGContext, RAGInterface
from eduadapt.rag import config
from eduadapt.rag.embeddings import Embedder, EmbedderProtocol
from eduadapt.rag.retriever import Retriever
from eduadapt.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


def to_rag_document(result: dict[str, Any]) -> RAGDocument:
    """Adapter converting retriever result dictionary into canonical RAGDocument.

    Maps:
      - chunk_id -> doc_id
      - text     -> content
      - source   -> source
      - score    -> score
      - page, module, topic preserved as optional metadata
    """
    return RAGDocument(
        doc_id=str(result.get("chunk_id", "")),
        content=str(result.get("text", "")),
        source=str(result.get("source", "")),
        score=float(result["score"]) if result.get("score") is not None else None,
        page=result.get("page"),
        module=result.get("module"),
        topic=result.get("topic"),
    )


class PPSCurriculumRAG(RAGInterface):
    """Concrete RAG interface over the PPS curriculum vector database."""

    def __init__(self, retriever: Retriever, store: Optional[VectorStore] = None) -> None:
        self._retriever = retriever
        self._store = store

    @classmethod
    def from_defaults(
        cls,
        db_path: Path | str | None = None,
        collection_name: str = config.COLLECTION_NAME,
        embedder: Optional[EmbedderProtocol] = None,
        model_name: str = config.EMBEDDING_MODEL_NAME,
        allow_empty: bool = False,
    ) -> Optional["PPSCurriculumRAG"]:
        """Open the existing database and build a ready-to-use interface.

        If allow_empty is False (default) and the database is missing/empty, raises RuntimeError.
        If allow_empty is True, logs a warning and returns None.
        """
        store = VectorStore(path=db_path, collection_name=collection_name)
        if not store.collection_exists() or store.count() == 0:
            store.close()
            if not allow_empty:
                raise RuntimeError(
                    "The PPS vector database is empty or missing. Put PPS files in "
                    "data/raw/pps/ and run: python scripts/rag/ingest.py"
                )
            logger.warning(
                "PPS vector database at %s is empty or missing. Curriculum RAG is disabled.",
                db_path or config.VECTOR_DB_DIR,
            )
            return None

        embedder = embedder or Embedder(model_name=model_name)
        return cls(Retriever(embedder, store), store)

    def retrieve(self, query: str, top_k: int = config.TOP_K) -> RAGContext:
        """Retrieve the top_k most relevant PPS chunks for a query."""
        results = self._retriever.retrieve(query, top_k=top_k)
        return RAGContext(
            query=query,
            documents=[to_rag_document(r) for r in results],
        )

    @staticmethod
    def format_for_prompt(context: RAGContext) -> str:
        """Plain-text version of the context formatted with source labels."""
        return context.format_for_prompt()

    def close(self) -> None:
        """Release the vector database folder."""
        if self._store is not None:
            self._store.close()


class EmptyRAG(RAGInterface):
    """Graceful fallback RAG module returning empty context when DB is unindexed."""

    def retrieve(self, query: str, top_k: int = 3) -> RAGContext:
        """Return empty RAGContext gracefully."""
        return RAGContext(query=query, documents=[])
