"""Stage 3a - Load PPS curriculum files into a simple internal format.

What this file does
-------------------
Reads every supported file (PDF, TXT, MD) in a folder and returns a list of
"page dictionaries". One dictionary = one PDF page (or one whole text file):

    {
        "text":      "...raw extracted text...",
        "source":    "module_4_pointers.pdf",   # file name
        "page":      18,                        # None for .txt / .md files
        "module":    "Module 4",                # from file/folder name or map
        "topic":     "Unknown",                 # filled in later (chunking)
        "file_path": "module_4_pointers.pdf",   # path relative to data folder
    }

Files that cannot be read (corrupt, password-protected, scanned images with
no text...) are SKIPPED with a clear message. One bad file never stops the
others from loading.

Optional: place a ``curriculum_map.json`` next to your files to set the exact
module/topic names yourself, for example:

    {
        "module_4_pointers.pdf": {"module": "Module 4", "topic": "Pointers"}
    }
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from pptx import Presentation

from eduadapt.rag import config

logger = logging.getLogger(__name__)

# A "page dictionary" (see above) and a "problem" = (file name, reason).
PageDict = dict[str, Any]
Problem = tuple[str, str]

# Matches things like "module_4", "Module 4", "module-04", "unit2", "pps u5".
_MODULE_PATTERN = re.compile(r"(module|unit|\bu)[\s_\-]*0*(\d+)", re.IGNORECASE)


class DocumentLoadError(Exception):
    """Raised when ONE file cannot be turned into usable text."""


def detect_module(relative_path: Path) -> str:
    """Guess the module name from the file name, then from its folders.

    ``module_4_pointers.pdf``      -> "Module 4"
    ``Module 3/lecture_notes.pdf`` -> "Module 3"
    ``notes.pdf``                  -> "Unknown"  (we never guess)
    """
    folders_innermost_first = list(reversed(relative_path.parts[:-1]))
    for name in [relative_path.stem, *folders_innermost_first]:
        match = _MODULE_PATTERN.search(name)
        if match:
            kind = match.group(1).lower()
            label = "Unit" if kind in ("unit", "u") else match.group(1).capitalize()
            return f"{label} {int(match.group(2))}"
    return config.UNKNOWN_LABEL


def load_curriculum_map(data_dir: Path) -> dict[str, dict[str, str]]:
    """Read the optional curriculum_map.json (returns {} if absent/invalid)."""
    map_path = data_dir / config.CURRICULUM_MAP_FILENAME
    if not map_path.is_file():
        return {}
    try:
        data = json.loads(map_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Ignoring %s - could not read it: %s", map_path.name, exc)
        return {}
    if not isinstance(data, dict):
        logger.warning("Ignoring %s - expected a JSON object.", map_path.name)
        return {}
    return {key: value for key, value in data.items() if isinstance(value, dict)}


def _read_pdf_pages(path: Path) -> list[tuple[int, str]]:
    """Return [(page_number, text), ...] for pages that contain text."""
    reader = PdfReader(str(path))
    if reader.is_encrypted and reader.decrypt("") == 0:
        raise DocumentLoadError("PDF is password-protected")

    pages: list[tuple[int, str]] = []
    for number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # one bad page must not kill the whole file
            logger.warning("%s page %d: text extraction failed (%s)", path.name, number, exc)
            continue
        if text.strip():
            pages.append((number, text))
    return pages


def _read_pptx_slides(path: Path) -> list[tuple[int, str]]:
    """Return [(slide_number, text), ...] for slides that contain text."""
    try:
        prs = Presentation(str(path))
    except Exception as exc:
        raise DocumentLoadError(f"could not read presentation ({type(exc).__name__}: {exc})") from exc

    slides: list[tuple[int, str]] = []
    for number, slide in enumerate(prs.slides, start=1):
        texts: list[str] = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                t = shape.text.strip()
                if t:
                    texts.append(t)
            elif shape.has_table:
                for row in shape.table.rows:
                    row_t = " | ".join(c.text.strip() for c in row.cells if c.text.strip())
                    if row_t:
                        texts.append(row_t)
        slide_text = "\n".join(texts).strip()
        if slide_text:
            slides.append((number, slide_text))
    return slides


def _read_text_file(path: Path) -> str:
    """Read a .txt/.md file. Tries UTF-8 first, then Windows encoding."""
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def load_document(
    path: Path | str,
    data_dir: Path | str | None = None,
    curriculum_map: dict[str, dict[str, str]] | None = None,
) -> list[PageDict]:
    """Load ONE file and return its page dictionaries.

    Raises DocumentLoadError (with a readable reason) if the file is unusable.
    """
    path = Path(path)
    base = Path(data_dir) if data_dir else path.parent
    try:
        relative = path.relative_to(base)
    except ValueError:
        relative = Path(path.name)

    overrides = {}
    if curriculum_map:
        overrides = curriculum_map.get(relative.as_posix()) or curriculum_map.get(path.name) or {}
    module = overrides.get("module") or detect_module(relative)
    topic = overrides.get("topic") or config.UNKNOWN_LABEL

    suffix = path.suffix.lower()
    try:
        if suffix == ".pdf":
            sections: list[tuple[int | None, str]] = list(_read_pdf_pages(path))
            if not sections:
                raise DocumentLoadError(
                    "no extractable text (the PDF may be a scan/images only)"
                )
        elif suffix == ".pptx":
            sections = list(_read_pptx_slides(path))
            if not sections:
                raise DocumentLoadError(
                    "no extractable text (the presentation may contain images only)"
                )
        elif suffix in (".txt", ".md"):
            text = _read_text_file(path)
            if not text.strip():
                raise DocumentLoadError("file is empty")
            sections = [(None, text)]
        else:
            raise DocumentLoadError(f"unsupported file type '{suffix}'")
    except DocumentLoadError:
        raise
    except Exception as exc:  # corrupt PDF, permission error, etc.
        raise DocumentLoadError(f"could not read file ({type(exc).__name__}: {exc})") from exc

    return [
        {
            "text": text,
            "source": path.name,
            "page": page_number,
            "module": module,
            "topic": topic,
            "file_path": relative.as_posix(),
        }
        for page_number, text in sections
    ]


def load_documents(data_dir: Path | str | None = None) -> tuple[list[PageDict], list[Problem]]:
    """Load every supported file under ``data_dir`` (sub-folders included).

    Returns ``(pages, problems)``:
      pages    - all page dictionaries from all readable files
      problems - [(file, reason), ...] for files that had to be skipped
    """
    folder = Path(data_dir) if data_dir else config.RAW_DATA_DIR
    if not folder.is_dir():
        raise FileNotFoundError(
            f"PPS data folder not found: {folder}\n"
            "Create it and put your PPS files (PDF/TXT/MD) inside."
        )

    curriculum_map = load_curriculum_map(folder)
    files = sorted(
        p for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in config.SUPPORTED_EXTENSIONS
    )
    if not files:
        logger.warning(
            "No PDF/TXT/MD files found in %s. Place your PPS curriculum files there.", folder
        )

    pages: list[PageDict] = []
    problems: list[Problem] = []
    for file_path in files:
        name = file_path.relative_to(folder).as_posix()
        try:
            loaded = load_document(file_path, data_dir=folder, curriculum_map=curriculum_map)
        except DocumentLoadError as exc:
            logger.warning("Skipping %s: %s", name, exc)
            problems.append((name, str(exc)))
            continue
        logger.info("Loaded %s (%d page(s)/section(s))", name, len(loaded))
        pages.extend(loaded)
    return pages, problems
