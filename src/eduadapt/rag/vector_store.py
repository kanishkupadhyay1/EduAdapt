"""Stage 6 - Store chunk vectors in a LOCAL, PERSISTENT Qdrant database.

Beginner explanation
--------------------
A *vector database* stores vectors together with extra information (here:
the chunk text and its metadata, called the "payload") and can quickly answer
"which stored vectors are closest to this one?". We use Qdrant in its
*local mode*: it keeps everything in a normal folder on your disk
(``vector_db/``). No server, no Docker, no cloud account.

Things to know
--------------
* A *collection* is like a table: it holds all our PPS chunks.
* Local mode lets only ONE program open the folder at a time. Always call
  ``close()`` (or use ``with VectorStore(...) as store:``) when finished,
  otherwise the next program gets a "locked" error.
* Re-adding a chunk with the same ``chunk_id`` OVERWRITES it (no duplicates).
  Chunks of files you deleted stay until you rebuild with ``rebuild=True``.
"""

import logging
import uuid
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from eduadapt.rag import config

logger = logging.getLogger(__name__)

# Fixed namespace so the same chunk_id always becomes the same Qdrant point id.
_ID_NAMESPACE = uuid.UUID("6f1c5a0e-7d62-4a53-9f3e-2c8b1a4d9e10")


def chunk_id_to_point_id(chunk_id: str) -> str:
    """Qdrant needs UUID/integer ids; we derive a stable UUID from chunk_id."""
    return str(uuid.uuid5(_ID_NAMESPACE, chunk_id))


class VectorStore:
    """Small wrapper around a local Qdrant collection."""

    def __init__(
        self,
        path: Path | str | None = None,
        collection_name: str = config.COLLECTION_NAME,
    ) -> None:
        self.path = Path(path) if path else config.VECTOR_DB_DIR
        self.collection_name = collection_name
        self.path.mkdir(parents=True, exist_ok=True)
        try:
            self.client = QdrantClient(path=str(self.path))
        except RuntimeError as exc:  # raised when the folder is locked
            raise RuntimeError(
                f"Could not open the vector database at {self.path}. Another program may "
                f"be using it (close other scripts/terminals) - original error: {exc}"
            ) from exc

    # -- context manager (so the folder gets unlocked) ----------------------
    def __enter__(self) -> "VectorStore":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        """Release the database folder."""
        self.client.close()

    # -- collection management ---------------------------------------------
    def collection_exists(self) -> bool:
        return self.client.collection_exists(self.collection_name)

    def delete_collection(self) -> None:
        if self.collection_exists():
            self.client.delete_collection(self.collection_name)
            import gc
            import shutil
            gc.collect()
            coll_path = self.path / "collection" / self.collection_name
            if coll_path.exists():
                shutil.rmtree(coll_path, ignore_errors=True)
            logger.info("Deleted collection '%s'.", self.collection_name)

    def vector_size(self) -> int | None:
        """Vector length of the existing collection (None if it doesn't exist)."""
        if not self.collection_exists():
            return None
        params = self.client.get_collection(self.collection_name).config.params.vectors
        return int(params.size)  # type: ignore[union-attr]

    def create_collection(self, vector_size: int, rebuild: bool = False) -> None:
        """Create the collection if needed.

        rebuild=True  -> delete any existing collection first (clean slate).
        Otherwise an existing collection is reused, but only if its vector
        length matches (a different embedding model needs --rebuild).
        """
        if rebuild:
            self.delete_collection()
        if self.collection_exists():
            existing = self.vector_size()
            if existing != vector_size:
                raise ValueError(
                    f"Collection '{self.collection_name}' stores {existing}-number vectors but the "
                    f"current embedding model produces {vector_size}. You probably changed the "
                    "embedding model - rebuild the database (python scripts/ingest.py --rebuild)."
                )
            return
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        logger.info("Created collection '%s' (vector size %d).", self.collection_name, vector_size)

    # -- writing ------------------------------------------------------------
    def upsert_chunks(
        self,
        chunks: list[dict[str, Any]],
        vectors: list[list[float]],
        batch_size: int = config.UPSERT_BATCH_SIZE,
    ) -> int:
        """Store chunks + their vectors. The whole chunk dict is the payload."""
        if len(chunks) != len(vectors):
            raise ValueError(f"Got {len(chunks)} chunks but {len(vectors)} vectors.")
        for start in range(0, len(chunks), batch_size):
            batch = [
                PointStruct(id=chunk_id_to_point_id(c["chunk_id"]), vector=v, payload=dict(c))
                for c, v in zip(chunks[start:start + batch_size], vectors[start:start + batch_size])
            ]
            self.client.upsert(collection_name=self.collection_name, points=batch)
        return len(chunks)

    # -- reading ------------------------------------------------------------
    def count(self) -> int:
        if not self.collection_exists():
            return 0
        return int(self.client.count(self.collection_name, exact=True).count)

    def search(self, query_vector: list[float], top_k: int = config.TOP_K) -> list[dict[str, Any]]:
        """Return the top_k closest chunks as [{"score": float, "payload": dict}, ...]."""
        if not self.collection_exists():
            raise RuntimeError(
                f"Collection '{self.collection_name}' does not exist in {self.path}. "
                "Build it first with: python scripts/ingest.py"
            )
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True,
        )
        return [{"score": float(p.score), "payload": dict(p.payload or {})} for p in response.points]
