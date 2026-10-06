"""Build (or refresh) the PPS knowledge base with ONE command.

    raw PPS files -> load -> clean -> chunk -> embed -> store in Qdrant

Run from the member2_rag folder:

    python scripts/ingest.py                    # add/refresh
    python scripts/ingest.py --rebuild          # wipe the database, build fresh
    python scripts/ingest.py --data-dir "C:\\my\\pps" --chunk-size 900 --chunk-overlap 150

Use --rebuild whenever you delete/rename files, change chunk settings, or
change the embedding model, so no stale chunks are left behind.
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path

# Make "import src..." work when running `python scripts/ingest.py`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config  # noqa: E402
from src.chunking import chunk_pages  # noqa: E402
from src.document_loader import load_documents  # noqa: E402
from src.embeddings import Embedder, EmbedderProtocol  # noqa: E402
from src.preprocessing import preprocess_pages  # noqa: E402
from src.vector_store import VectorStore  # noqa: E402

logger = logging.getLogger("ingest")


def run_ingestion(
    data_dir: Path | str | None = None,
    db_path: Path | str | None = None,
    collection_name: str = config.COLLECTION_NAME,
    chunk_size: int = config.CHUNK_SIZE,
    chunk_overlap: int = config.CHUNK_OVERLAP,
    rebuild: bool = False,
    embedder: EmbedderProtocol | None = None,
    processed_dir: Path | str | None = None,
    allow_unmapped: bool = False,
) -> dict:
    """Run the whole pipeline. Returns a small summary dictionary."""
    pages, problems = load_documents(data_dir)

    # Scope enforcement: only Unit 1-5 material belongs in the corpus.
    if not allow_unmapped:
        mapped = [p for p in pages if p["module"] in config.UNIT_LABELS]
        skipped_files = sorted({p["file_path"] for p in pages} - {p["file_path"] for p in mapped})
        for name in skipped_files:
            reason = ("not mapped to Unit 1-5, so it was skipped (name it unit_N_...pdf or list it "
                      "in curriculum_map.json; use --allow-unmapped to include it anyway)")
            logger.warning("Skipping %s: %s", name, reason)
            problems.append((name, reason))
        pages = mapped

    if not pages:
        raise RuntimeError(
            "No readable PPS pages were found, so nothing was indexed. Put your PPS PDF/TXT/MD "
            f"files in {data_dir or config.RAW_DATA_DIR} (see README) and run again."
        )
    cleaned = preprocess_pages(pages)
    chunks = chunk_pages(cleaned, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not chunks:
        raise RuntimeError("Cleaning removed all text, so there are no chunks to index.")

    # Warn (never delete) when a chunk's heading is a topic the syllabus excludes.
    out_of_scope = re.compile(config.OUT_OF_SCOPE_HEADING_PATTERN, re.IGNORECASE)
    scope_warnings = [(c["chunk_id"], c["topic"]) for c in chunks if out_of_scope.match(c["topic"].strip())]
    for chunk_id, topic in scope_warnings:
        logger.warning("Out-of-scope topic %r in chunk %s - not in the syllabus; consider removing that material.", topic, chunk_id)

    # Save the chunks as readable JSON Lines so you can inspect what was indexed.
    out_dir = Path(processed_dir) if processed_dir else config.PROCESSED_DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    chunk_file = out_dir / "chunks.jsonl"
    with chunk_file.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    embedder = embedder or Embedder()
    logger.info("Embedding %d chunk(s)...", len(chunks))
    vectors = embedder.embed_texts([c["text"] for c in chunks])

    with VectorStore(path=db_path, collection_name=collection_name) as store:
        store.create_collection(vector_size=len(vectors[0]), rebuild=rebuild)
        store.upsert_chunks(chunks, vectors)
        total = store.count()

    return {
        "pages_loaded": len(pages),
        "pages_after_cleaning": len(cleaned),
        "chunks_created": len(chunks),
        "chunks_in_database": total,
        "skipped_files": problems,
        "out_of_scope_warnings": scope_warnings,
        "chunk_file": str(chunk_file),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the PPS curriculum vector database.")
    parser.add_argument("--data-dir", default=str(config.RAW_DATA_DIR), help="Folder with PPS files")
    parser.add_argument("--db-path", default=str(config.VECTOR_DB_DIR), help="Where to store the database")
    parser.add_argument("--collection", default=config.COLLECTION_NAME, help="Qdrant collection name")
    parser.add_argument("--chunk-size", type=int, default=config.CHUNK_SIZE, help="Target chunk size (characters)")
    parser.add_argument("--chunk-overlap", type=int, default=config.CHUNK_OVERLAP, help="Overlap (characters)")
    parser.add_argument("--model", default=config.EMBEDDING_MODEL_NAME, help="Embedding model name")
    parser.add_argument("--allow-unmapped", action="store_true", help="Also index files that are not mapped to Unit 1-5")
    parser.add_argument("--rebuild", action="store_true", help="Delete and recreate the collection")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        summary = run_ingestion(
            data_dir=args.data_dir, db_path=args.db_path, collection_name=args.collection,
            chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap, rebuild=args.rebuild, allow_unmapped=args.allow_unmapped,
            embedder=Embedder(model_name=args.model),
        )
    except (RuntimeError, ValueError, FileNotFoundError, ImportError) as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)

    print("\nIngestion finished.")
    print(f"  Pages loaded:          {summary['pages_loaded']} ({summary['pages_after_cleaning']} after cleaning)")
    print(f"  Chunks created:        {summary['chunks_created']}")
    print(f"  Chunks in database:    {summary['chunks_in_database']}")
    print(f"  Readable chunk dump:   {summary['chunk_file']}")
    if summary["out_of_scope_warnings"]:
        print("  WARNING - topics not in the syllabus were found (see log above):")
        for chunk_id, topic in summary["out_of_scope_warnings"]:
            print(f"    - {topic} ({chunk_id})")
    if summary["skipped_files"]:
        print("  Skipped files:")
        for name, reason in summary["skipped_files"]:
            print(f"    - {name}: {reason}")


if __name__ == "__main__":
    main()
