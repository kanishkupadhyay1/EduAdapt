"""Stage 6 - Store chunk vectors in a LOCAL, PERSISTENT Qdrant database.

Beginner explanation
--------------------
A vector database stores vectors together with extra information (here:
the chunk text and its metadata, called the "payload") and can quickly answer
"which stored vectors are closest to this one?". We use Qdrant in its
local mode: it keeps everything in a normal folder on your disk
(``vector_db/``). No server, no Docker, no cloud account.

Things to know
--------------
* A collection is like a table: it holds all our PPS chunks.
* Local mode lets only ONE program open the folder at a time. Always call
  ``close()`` (or use ``with VectorStore(...) as store:``) when finished,
  otherwise the next program gets a "locked" error.
* Re-adding a chunk with the same ``chunk_id`` OVERWRITES it (no duplicates).
* Rebuilding clears the existing collection's points before ingestion.
"""

import logging
import uuid
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src import config

logger = logging.getLogger(__name__)

# Fixed namespace so the same chunk_id always becomes the same Qdrant point id.
_ID_NAMESPACE = uuid.UUID("6f1c5a0e-7d62-4a53-9f3e-2c8b1a4d9e10")


def chunk_id_to_point_id(chunk_id: str) -> str:
    """Qdrant needs UUID/integer ids; derive a stable UUID from chunk_id."""
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
        except RuntimeError as exc:
            raise RuntimeError(
                f"Could not open the vector database at {self.path}. "
                f"Another program may be using it "
                f"(close other scripts/terminals) - original error: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "VectorStore":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        """Release the database folder."""
        self.client.close()

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def collection_exists(self) -> bool:
        """Return True when the collection exists."""
        return self.client.collection_exists(self.collection_name)

    def delete_collection(self) -> None:
        """Delete the collection when it exists."""
        if self.collection_exists():
            self.client.delete_collection(self.collection_name)
            logger.info(
                "Deleted collection '%s'.",
                self.collection_name,
            )

    def vector_size(self) -> int | None:
        """Return vector length of the existing collection."""
        if not self.collection_exists():
            return None

        params = self.client.get_collection(
            self.collection_name
        ).config.params.vectors

        return int(params.size)  # type: ignore[union-attr]

    def _clear_points(self) -> None:
        """Delete every point from the current collection.

        The collection itself remains available with the same vector schema.
        """
        if not self.collection_exists():
            return

        while True:
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=False,
                with_vectors=False,
            )

            if not points:
                break

            point_ids = [point.id for point in points]

            self.client.delete(
                collection_name=self.collection_name,
                points_selector=point_ids,
                wait=True,
            )

        logger.info(
            "Cleared all points from collection '%s'.",
            self.collection_name,
        )

    def create_collection(
        self,
        vector_size: int,
        rebuild: bool = False,
    ) -> None:
        """Create or reuse the collection.

        rebuild=True:
            Clear all existing points and prepare the collection for
            fresh ingestion.

        rebuild=False:
            Reuse an existing collection when its vector size matches.
            Otherwise raise a helpful error.
        """
        if rebuild and self.collection_exists():
            existing = self.vector_size()

            if existing != vector_size:
                raise ValueError(
                    f"Collection '{self.collection_name}' stores "
                    f"{existing} number vectors but the current embedding "
                    f"model produces {vector_size}. A different embedding "
                    "dimension requires rebuilding the vector database "
                    "with a fresh database directory."
                )

            self._clear_points()
            return

        if self.collection_exists():
            existing = self.vector_size()

            if existing != vector_size:
                raise ValueError(
                    f"Collection '{self.collection_name}' stores "
                    f"{existing} number vectors but the current embedding "
                    f"model produces {vector_size}. You probably changed "
                    "the embedding model - rebuild the database "
                    "(python scripts/ingest.py --rebuild)."
                )

            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

        logger.info(
            "Created collection '%s' (vector size %d).",
            self.collection_name,
            vector_size,
        )

    # ------------------------------------------------------------------
    # Writing
    # ------------------------------------------------------------------

    def upsert_chunks(
        self,
        chunks: list[dict[str, Any]],
        vectors: list[list[float]],
        batch_size: int = config.UPSERT_BATCH_SIZE,
    ) -> int:
        """Store chunks and their vectors."""
        if len(chunks) != len(vectors):
            raise ValueError(
                f"Got {len(chunks)} chunks but {len(vectors)} vectors."
            )

        for start in range(0, len(chunks), batch_size):
            batch = [
                PointStruct(
                    id=chunk_id_to_point_id(chunk["chunk_id"]),
                    vector=vector,
                    payload=dict(chunk),
                )
                for chunk, vector in zip(
                    chunks[start : start + batch_size],
                    vectors[start : start + batch_size],
                )
            ]

            self.client.upsert(
                collection_name=self.collection_name,
                points=batch,
            )

        return len(chunks)

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def count(self) -> int:
        """Return the exact number of stored chunks."""
        if not self.collection_exists():
            return 0

        return int(
            self.client.count(
                self.collection_name,
                exact=True,
            ).count
        )

    def search(
        self,
        query_vector: list[float],
        top_k: int = config.TOP_K,
    ) -> list[dict[str, Any]]:
        """Return the top_k closest chunks."""
        if not self.collection_exists():
            raise RuntimeError(
                f"Collection '{self.collection_name}' does not exist "
                f"in {self.path}. "
                "Build it first with: python scripts/ingest.py"
            )

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True,
        )

        return [
            {
                "score": float(point.score),
                "payload": dict(point.payload or {}),
            }
            for point in response.points
        ]