"""Stage 8 - The hand-off point to Member 1: ``rag.retrieve(query, top_k)``.

!!! READ THIS FIRST !!!
Member 1 owns the real RAGDocument / RAGContext / RAGInterface definitions,
and we have NOT seen them yet. So the three classes in the block marked
"TEMPORARY CONTRACT" below are PLACEHOLDERS. Their field names are our best
guess (based on the metadata the task requires) and are NOT final.

When Member 1 sends the real definitions, change ONLY these two places:
  1. Replace the "TEMPORARY CONTRACT" block with an import of the real classes.
  2. Update ``to_rag_document()`` (and ``format_for_prompt()``) to use the
     real field names.
Nothing else in the pipeline (loader, chunker, embedder, Qdrant, retriever)
knows about these classes, so nothing else has to change.

No agent logic here: retrieval is one fixed lookup.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src import config
from src.embeddings import Embedder, EmbedderProtocol
from src.retriever import Retriever
from src.vector_store import VectorStore

logger = logging.getLogger(__name__)


# ==========================================================================
# TEMPORARY CONTRACT - REPLACE WITH MEMBER 1'S DEFINITIONS (field names NOT final)
# ==========================================================================
@dataclass
class RAGDocument:
    """One retrieved curriculum chunk (placeholder definition)."""

    text: str
    score: float
    source: str
    page: int | None
    module: str
    topic: str
    chunk_id: str


@dataclass
class RAGContext:
    """Everything retrieved for one question (placeholder definition)."""

    query: str
    documents: list[RAGDocument] = field(default_factory=list)


class RAGInterface(ABC):
    """Placeholder for Member 1's abstract interface."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int = config.TOP_K) -> RAGContext:
        """Return source-aware curriculum context for a question."""
# ==========================================================================
# END OF TEMPORARY CONTRACT
# ==========================================================================


def to_rag_document(result: dict[str, Any]) -> RAGDocument:
    """THE adapter: converts one retriever result dict into a RAGDocument.

    This is the only function that maps our data onto the contract's field
    names. Edit it when the real contract arrives."""
    return RAGDocument(
        text=result["text"],
        score=result["score"],
        source=result["source"],
        page=result["page"],
        module=result["module"],
        topic=result["topic"],
        chunk_id=result["chunk_id"],
    )


class PPSCurriculumRAG(RAGInterface):
    """Concrete RAG interface over the PPS curriculum vector database."""

    def __init__(self, retriever: Retriever, store: VectorStore | None = None) -> None:
        self._retriever = retriever
        self._store = store  # kept only so close() can release the database

    @classmethod
    def from_defaults(
        cls,
        db_path: Path | str | None = None,
        collection_name: str = config.COLLECTION_NAME,
        embedder: EmbedderProtocol | None = None,
        model_name: str = config.EMBEDDING_MODEL_NAME,
    ) -> "PPSCurriculumRAG":
        """Open the existing database and build a ready-to-use interface."""
        store = VectorStore(path=db_path, collection_name=collection_name)
        if not store.collection_exists() or store.count() == 0:
            store.close()
            raise RuntimeError(
                "The PPS vector database is empty or missing. Put PPS files in "
                "data/raw/pps/ and run: python scripts/ingest.py"
            )
        embedder = embedder or Embedder(model_name=model_name)
        return cls(Retriever(embedder, store), store)

    def retrieve(self, query: str, top_k: int = config.TOP_K) -> RAGContext:
        """Retrieve the top_k most relevant PPS chunks for ``query``."""
        results = self._retriever.retrieve(query, top_k=top_k)
        return RAGContext(query=query, documents=[to_rag_document(r) for r in results])

    @staticmethod
    def format_for_prompt(context: RAGContext) -> str:
        """Plain-text version of the context, with source labels, that
        Member 1 can paste into the Mistral prompt (optional helper)."""
        if not context.documents:
            return "(No relevant PPS curriculum material was found.)"
        blocks = []
        for number, doc in enumerate(context.documents, start=1):
            page = f", page {doc.page}" if doc.page is not None else ""
            blocks.append(
                f"[Source {number}: {doc.source}{page} | {doc.module} | {doc.topic}]\n{doc.text}"
            )
        return "\n\n".join(blocks)

    def close(self) -> None:
        """Release the vector database folder."""
        if self._store is not None:
            self._store.close()
