"""Stage 3 helper: load + clean your PPS files and show a short preview.

Run from the member2_rag folder:
    python scripts/preview_documents.py
    python scripts/preview_documents.py --data-dir "C:\\path\\to\\pps_files"

This does NOT build the vector database (that comes in later stages).
It only lets you SEE what the loader and cleaner produce.
"""

import argparse
import logging
import sys
from pathlib import Path

# Make "import src..." work when running `python scripts/preview_documents.py`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config  # noqa: E402
from src.document_loader import load_documents  # noqa: E402
from src.preprocessing import preprocess_pages  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview loaded + cleaned PPS documents.")
    parser.add_argument("--data-dir", default=str(config.RAW_DATA_DIR), help="Folder with PPS files")
    parser.add_argument("--chars", type=int, default=400, help="Preview length per file")
    args = parser.parse_args()

    # Avoid crashes when printing special characters in the Windows console.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    pages, problems = load_documents(args.data_dir)
    cleaned = preprocess_pages(pages)

    print(f"\nLoaded {len(pages)} page(s); {len(cleaned)} remain after cleaning.")
    if problems:
        print("\nFiles that were skipped:")
        for name, reason in problems:
            print(f"  - {name}: {reason}")

    shown: set[str] = set()
    for page in cleaned:
        if page["file_path"] in shown:
            continue
        shown.add(page["file_path"])
        print("\n" + "=" * 70)
        print(f"{page['source']} | page {page['page']} | {page['module']} | topic: {page['topic']}")
        print("-" * 70)
        print(page["text"][: args.chars])


if __name__ == "__main__":
    main()
