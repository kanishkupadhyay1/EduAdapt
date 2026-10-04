"""Central settings for the Member 2 RAG module.

Putting settings in ONE file means we never have the same number or path
typed in several places. Later stages (chunk size, embedding model, Qdrant
collection name, ...) will add their settings here too.
"""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# ---- Python version -------------------------------------------------------
# The team environment is exactly Python 3.11.0 (major, minor, micro).
REQUIRED_PYTHON = (3, 11, 0)

# ---- Folders --------------------------------------------------------------
# MODULE_ROOT is the member2_rag/ folder, wherever it sits on your computer.
MODULE_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = MODULE_ROOT / "data" / "raw" / "pps"
PROCESSED_DATA_DIR = MODULE_ROOT / "data" / "processed"

# ---- Document loading -----------------------------------------------------
SUPPORTED_EXTENSIONS = (".pdf", ".txt", ".md")
CURRICULUM_MAP_FILENAME = "curriculum_map.json"
UNKNOWN_LABEL = "Unknown"

# ---- Preprocessing --------------------------------------------------------
# A short line that shows up on at least this share of a PDF's pages (and the
# PDF has at least MIN_PAGES pages) is treated as a repeated header/footer.
REPEATED_LINE_FRACTION = 0.5
REPEATED_LINE_MIN_PAGES = 3
REPEATED_LINE_MAX_LENGTH = 80

# ---- Chunking -------------------------------------------------------------
# Sizes are in CHARACTERS. all-MiniLM-L6-v2 reads about 256 tokens (~1000
# characters) and ignores the rest, so 900 keeps a whole chunk inside what
# the model can "see". 150 (~15%) overlap repeats the end of one chunk at the
# start of the next so ideas on a boundary are not lost.
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
# A C code block may be this many times longer than CHUNK_SIZE before we
# are willing to split it (we prefer keeping code in one piece).
CODE_BLOCK_MAX_FACTOR = 2.0

# ---- Embeddings -----------------------------------------------------------
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # 384 numbers per text
EMBEDDING_BATCH_SIZE = 32
QUERY_CACHE_SIZE = 256

# ---- Vector store (local Qdrant) -----------------------------------------
VECTOR_DB_DIR = MODULE_ROOT / "vector_db"
COLLECTION_NAME = "pps_curriculum"
UPSERT_BATCH_SIZE = 64

# ---- Retrieval ------------------------------------------------------------
TOP_K = 5


def check_python_version(version_info: tuple[int, int, int] | None = None) -> None:
    """Enforce the team's Python version.

    - Not Python 3.11.x          -> raise RuntimeError (stop immediately).
    - 3.11.x but not exactly .0  -> log a warning (same 3.11 release line,
      but different from the team's reference environment).
    """
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
