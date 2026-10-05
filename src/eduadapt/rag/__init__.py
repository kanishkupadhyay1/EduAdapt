"""PPS Curriculum Retrieval-Augmented Generation (RAG) module.

Namespaced integration of Member 2's semantic curriculum retrieval.
"""

from eduadapt.rag.rag_interface import (
    PPSCurriculumRAG,
    EmptyRAG,
    to_rag_document,
)
from eduadapt.rag.retriever import Retriever
from eduadapt.rag.vector_store import VectorStore
from eduadapt.rag.embeddings import Embedder
from eduadapt.rag.chunking import chunk_pages
from eduadapt.rag.preprocessing import preprocess_pages
from eduadapt.rag.document_loader import load_documents

__all__ = [
    "PPSCurriculumRAG",
    "EmptyRAG",
    "Retriever",
    "VectorStore",
    "Embedder",
    "chunk_pages",
    "preprocess_pages",
    "load_documents",
    "to_rag_document",
]
