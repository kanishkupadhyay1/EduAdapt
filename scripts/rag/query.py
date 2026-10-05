"""Ask the PPS knowledge base a question and print the retrieved chunks.

Run from the member2_rag folder:

    python scripts/query.py "Explain pointers in C"
    python scripts/query.py "What is a loop?" --top-k 3
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'src'))

from eduadapt.rag import config  # noqa: E402
from eduadapt.rag.rag_interface import PPSCurriculumRAG  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the PPS curriculum RAG.")
    parser.add_argument("query", help="Your question, in quotes")
    parser.add_argument("--top-k", type=int, default=config.TOP_K)
    parser.add_argument("--db-path", default=str(config.VECTOR_DB_DIR))
    parser.add_argument("--collection", default=config.COLLECTION_NAME)
    parser.add_argument("--model", default=config.EMBEDDING_MODEL_NAME)
    parser.add_argument("--chars", type=int, default=300, help="Preview length per chunk")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    try:
        rag = PPSCurriculumRAG.from_defaults(
            db_path=args.db_path, collection_name=args.collection, model_name=args.model
        )
    except (RuntimeError, ValueError, ImportError) as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
    try:
        context = rag.retrieve(args.query, top_k=args.top_k)
    finally:
        rag.close()

    print(f"\nQuery: {context.query}")
    for rank, doc in enumerate(context.documents, start=1):
        page = f"page {doc.page}" if doc.page is not None else "no page"
        print(f"\n{rank}. score={doc.score:.3f} | {doc.source} ({page}) | {doc.module} | {doc.topic}")
        print("   " + doc.text[: args.chars].replace("\n", "\n   "))


if __name__ == "__main__":
    main()
