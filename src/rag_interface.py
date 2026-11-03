"""PPS Curriculum RAG implementation.

Implements the canonical EduAdapt RAG interface owned by the platform
architecture.
"""

from pathlib import Path
from typing import Any

from src import config
from src.eduadapt.interfaces.rag import (
    RAGContext,
    RAGDocument,
    RAGInterface,
)
from src.embeddings import Embedder, EmbedderProtocol
from src.retriever import Retriever
from src.vector_store import VectorStore


def to_rag_document(result: dict[str, Any]) -> RAGDocument:
    """Convert one retriever result into the canonical RAGDocument."""
    return RAGDocument(
        doc_id=result["chunk_id"],
        content=result["text"],
        source=result["source"],
        score=result["score"],
        page=result["page"],
        module=result["module"],
        topic=result["topic"],
    )


class PPSCurriculumRAG(RAGInterface):
    """Concrete RAG interface over the PPS curriculum vector database."""

    def __init__(
        self,
        retriever: Retriever,
        store: VectorStore | None = None,
    ) -> None:
        self._retriever = retriever
        self._store = store

    @classmethod
    def from_defaults(
        cls,
        db_path: Path | str | None = None,
        collection_name: str = config.COLLECTION_NAME,
        embedder: EmbedderProtocol | None = None,
        model_name: str = config.EMBEDDING_MODEL_NAME,
    ) -> "PPSCurriculumRAG":
        """Open the existing database and build a ready-to-use interface."""
        store = VectorStore(
            path=db_path,
            collection_name=collection_name,
        )

        if not store.collection_exists() or store.count() == 0:
            store.close()
            raise RuntimeError(
                "The PPS vector database is empty or missing. "
                "Put PPS files in data/raw/pps/ and run: "
                "python scripts/ingest.py"
            )

        embedder = embedder or Embedder(model_name=model_name)

        return cls(
            Retriever(embedder, store),
            store,
        )

    def retrieve(
        self,
        query: str,
        top_k: int = config.TOP_K,
    ) -> RAGContext:
        """Retrieve the top_k most relevant PPS chunks for a query."""
        results = self._retriever.retrieve(
            query,
            top_k=top_k,
        )

        return RAGContext(
            query=query,
            documents=[
                to_rag_document(result)
                for result in results
            ],
        )

    @staticmethod
    def format_for_prompt(context: RAGContext) -> str:
        """Format retrieved context for use in the teaching prompt."""
        if not context.documents:
            return "(No relevant PPS curriculum material was found.)"

        blocks: list[str] = []

        for number, doc in enumerate(context.documents, start=1):
            page = f", page {doc.page}" if doc.page is not None else ""
            module = f" | {doc.module}" if doc.module else ""
            topic = f" | {doc.topic}" if doc.topic else ""

            blocks.append(
                f"[Source {number}: {doc.source}{page}{module}{topic}]\n"
                f"{doc.content}"
            )

        return "\n\n".join(blocks)

    def close(self) -> None:
        """Release the vector database folder."""
        if self._store is not None:
            self._store.close()