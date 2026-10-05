"""Interface contract for external RAG module.

Canonical contract owned by the platform architecture.
Consumed by the teaching generator and implemented by the PPS Curriculum RAG module.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field


class RAGDocument(BaseModel):
    """A single retrieved context chunk."""

    doc_id: str
    content: str
    source: str
    score: Optional[float] = None
    page: Optional[int] = None
    module: Optional[str] = None
    topic: Optional[str] = None

    @property
    def text(self) -> str:
        """Alias for content to support Member 2 interface."""
        return self.content

    @property
    def chunk_id(self) -> str:
        """Alias for doc_id to support Member 2 interface."""
        return self.doc_id


class RAGContext(BaseModel):
    """Aggregated retrieval context returned by the RAG module."""

    query: str
    documents: List[RAGDocument] = Field(default_factory=list)

    def to_context_str(self) -> str:
        """Helper to format retrieved documents as prompt context."""
        return "\n\n".join(
            f"[Source: {doc.source}]\n{doc.content}" for doc in self.documents
        )

    def format_for_prompt(self) -> str:
        """Helper to format retrieved documents with detailed source labels."""
        if not self.documents:
            return "(No relevant PPS curriculum material was found.)"
        blocks = []
        for number, doc in enumerate(self.documents, start=1):
            page = f", page {doc.page}" if doc.page is not None else ""
            module = f" | {doc.module}" if doc.module else ""
            topic = f" | {doc.topic}" if doc.topic else ""
            blocks.append(
                f"[Source {number}: {doc.source}{page}{module}{topic}]\n{doc.content}"
            )
        return "\n\n".join(blocks)


class RAGInterface(ABC):
    """Abstract interface defining the contract with the external RAG module."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 3) -> RAGContext:
        """Retrieve relevant context chunks for a query."""
        pass
