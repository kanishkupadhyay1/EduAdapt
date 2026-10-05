"""Central settings for the PPS Curriculum RAG module.

Manages chunk sizes, embedding model, vector store path, and retrieval parameters.
Namespaced inside eduadapt.rag to preserve clean module boundaries.
"""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# ---- Python version -------------------------------------------------------
# The team environment is Python 3.11.x (reference: 3.11.0).
REQUIRED_PYTHON = (3, 11, 0)

# ---- Folders --------------------------------------------------------------
# MODULE_ROOT is the repository root directory
MODULE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RAW_DATA_DIR = MODULE_ROOT / "data" / "raw" / "pps"
PROCESSED_DATA_DIR = MODULE_ROOT / "data" / "processed"

# ---- Document loading -----------------------------------------------------
SUPPORTED_EXTENSIONS = (".pdf", ".txt", ".md")
CURRICULUM_MAP_FILENAME = "curriculum_map.json"
UNKNOWN_LABEL = "Unknown"

# ---- Preprocessing --------------------------------------------------------
REPEATED_LINE_FRACTION = 0.5
REPEATED_LINE_MIN_PAGES = 3
REPEATED_LINE_MAX_LENGTH = 80

# ---- Chunking -------------------------------------------------------------
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
CODE_BLOCK_MAX_FACTOR = 2.0

# ---- Embeddings -----------------------------------------------------------
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_BATCH_SIZE = 32
QUERY_CACHE_SIZE = 256

# ---- Vector store (local Qdrant) -----------------------------------------
VECTOR_DB_DIR = MODULE_ROOT / "vector_db"
COLLECTION_NAME = "pps_curriculum"
UPSERT_BATCH_SIZE = 64

# ---- Retrieval ------------------------------------------------------------
TOP_K = 5


def check_python_version(version_info: tuple[int, int, int] | None = None) -> None:
    """Enforce the team's Python version (3.11.x)."""
    major, minor, micro = version_info or tuple(sys.version_info[:3])
    required_major, required_minor, required_micro = REQUIRED_PYTHON

    if (major, minor) != (required_major, required_minor):
        raise RuntimeError(
            f"This project requires Python {required_major}.{required_minor}."
            f"{required_micro} but you are running Python "
            f"{major}.{minor}.{micro}. Please use the team's Python 3.11.0 "
            "environment (do not upgrade or downgrade Python)."
        )
    if micro != required_micro:
        logger.warning(
            "Team reference is Python %d.%d.%d; you are running %d.%d.%d. "
            "Same 3.11 release line, but please use 3.11.0 for final results.",
            required_major, required_minor, required_micro, major, minor, micro,
        )
