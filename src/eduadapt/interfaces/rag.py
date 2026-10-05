"""Interface contract for external RAG module.

Owned by the RAG team member. This module only consumes retrieved context.
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


class RAGContext(BaseModel):
    """Aggregated retrieval context returned by the RAG module."""

    query: str
    documents: List[RAGDocument] = Field(default_factory=list)

    def to_context_str(self) -> str:
        """Helper to format retrieved documents as prompt context."""
        return "\n\n".join(
            f"[Source: {doc.source}]\n{doc.content}" for doc in self.documents
        )


class RAGInterface(ABC):
    """Abstract interface defining the contract with the external RAG module."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 3) -> RAGContext:
        """Retrieve relevant context chunks for a query."""
        pass
