"""Stage 4 - Split cleaned pages into small, meaningful "chunks".

Why chunk at all?
-----------------
A search engine for meaning works best on small pieces that each talk about
ONE idea. If we stored a whole 40-page PDF as one item, every question would
match it "a little" and nothing precisely. So we cut the text into chunks of
roughly one or two paragraphs and search over those.

How this file decides where to cut (in order of preference)
-----------------------------------------------------------
1. A new HEADING starts a new topic -> a chunk never mixes two topics.
2. A new PAGE starts a new chunk (so every chunk has ONE exact page number).
3. Inside a topic we keep whole paragraphs together.
4. A C code block is kept in ONE piece whenever it fits within
   CODE_BLOCK_MAX_FACTOR x chunk_size; only a huge block is split, and then
   only between lines.
5. A paragraph that is too long is split between sentences, and only as a
   last resort between words.

chunk_size   = target maximum length in characters (default 900)
chunk_overlap = characters of the previous chunk repeated at the start of the
                next one (default 150), only for explanation text, never code.

Because of overlap, a chunk can reach about chunk_size + chunk_overlap
characters, and a code block may be longer. chunk_size is a target, not a
strict wall.
"""

import logging
import re
from typing import Any

from eduadapt.rag import config
from eduadapt.rag.preprocessing import classify_lines, detect_heading

logger = logging.getLogger(__name__)

PageDict = dict[str, Any]
Chunk = dict[str, Any]

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


# --------------------------------------------------------------------------
# Step A: cut a page into "units" (a paragraph, or a block of code)
# --------------------------------------------------------------------------
def _split_into_units(text: str, start_topic: str, fixed_topic: bool) -> tuple[list[dict[str, str]], str]:
    """Split page text into units: [{"kind", "text", "topic"}, ...].

    ``topic`` on each unit is the topic in force where that unit starts.
    Returns (units, topic_at_end_of_page) so the next page can continue it.
    """
    lines = text.split("\n")
    kinds = classify_lines(lines)

    units: list[dict[str, str]] = []
    topic = start_topic
    buffer: list[str] = []
    buffer_kind = "prose"
    buffer_topic = topic
    buffer_is_heading_only = False

    def flush() -> None:
        nonlocal buffer, buffer_is_heading_only
        body = "\n".join(buffer).strip("\n")
        if body.strip():
            units.append({"kind": buffer_kind, "text": body, "topic": buffer_topic})
        buffer = []
        buffer_is_heading_only = False

    def next_nonblank_kind(index: int) -> str:
        for later in range(index + 1, len(lines)):
            if kinds[later] != "blank":
                return kinds[later]
        return "blank"

    for index, (line, kind) in enumerate(zip(lines, kinds)):
        if kind == "blank":
            if buffer_kind == "code" and buffer and next_nonblank_kind(index) == "code":
                buffer.append("")  # blank line INSIDE a code block: keep it
            else:
                flush()
            continue

        if kind == "code":
            if buffer_kind != "code" or not buffer:
                flush()
                buffer_kind, buffer_topic = "code", topic
            buffer.append(line)
            continue

        # prose line
        heading = detect_heading(line)
        if heading is not None:
            if not buffer_is_heading_only:
                flush()
            if not fixed_topic:
                topic = heading
            buffer_kind, buffer_topic = "prose", topic
            buffer = [line.strip()]
            buffer_is_heading_only = True
            continue

        if buffer_kind != "prose" or not buffer:
            flush()
            buffer_kind, buffer_topic = "prose", topic
        buffer.append(line)
        buffer_is_heading_only = False

    flush()
    return units, topic


# --------------------------------------------------------------------------
# Step B: break units that are too long
# --------------------------------------------------------------------------
def _split_long_prose(text: str, chunk_size: int) -> list[str]:
    """Split long prose between sentences (words only as a last resort)."""
    pieces: list[str] = []
    current = ""
    for sentence in _SENTENCE_END.split(text.replace("\n", " ")):
        sentence = sentence.strip()
        if not sentence:
            continue
        # A single sentence longer than chunk_size: cut between words.
        while len(sentence) > chunk_size:
            cut = sentence.rfind(" ", 0, chunk_size)
            cut = cut if cut > 0 else chunk_size
            if current:
                pieces.append(current)
                current = ""
            pieces.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if current and len(current) + 1 + len(sentence) > chunk_size:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return pieces


def _split_long_code(text: str, max_length: int) -> list[str]:
    """Split a huge code block between lines (never inside a line)."""
    pieces: list[str] = []
    current: list[str] = []
    length = 0
    for line in text.split("\n"):
        if current and length + len(line) + 1 > max_length:
            pieces.append("\n".join(current))
            current, length = [], 0
        current.append(line)
        length += len(line) + 1
    if current:
        pieces.append("\n".join(current))
    return pieces


def _tail_for_overlap(text: str, overlap: int) -> str:
    """Last ``overlap`` characters of text, starting at a word boundary."""
    if overlap <= 0 or len(text) <= overlap:
        return text.strip() if overlap > 0 else ""
    tail = text[-overlap:]
    first_space = tail.find(" ")
    if first_space != -1:
        tail = tail[first_space + 1:]
    return tail.strip()


# --------------------------------------------------------------------------
# Step C: pack units into chunks
# --------------------------------------------------------------------------
def _pack_units(units: list[dict[str, str]], chunk_size: int, overlap: int) -> list[tuple[str, str]]:
    """Greedily pack units into chunks. Returns [(text, topic), ...]."""
    max_code = int(chunk_size * config.CODE_BLOCK_MAX_FACTOR)

    # Break oversized units first.
    sized: list[dict[str, str]] = []
    for unit in units:
        if unit["kind"] == "prose" and len(unit["text"]) > chunk_size:
            sized += [{**unit, "text": p} for p in _split_long_prose(unit["text"], chunk_size)]
        elif unit["kind"] == "code" and len(unit["text"]) > max_code:
            sized += [{**unit, "text": p} for p in _split_long_code(unit["text"], max_code)]
        else:
            sized.append(unit)

    chunks: list[tuple[str, str]] = []
    parts: list[str] = []          # texts inside the chunk being built
    length = 0
    topic = ""
    last_kind = "prose"
    has_new_content = False

    def emit(carry_overlap: bool) -> None:
        nonlocal parts, length, has_new_content
        if has_new_content:
            # strip only blank lines (never leading spaces: they are code indentation)
            chunks.append(("\n\n".join(parts).strip("\n").rstrip(), topic))
        carried = ""
        if carry_overlap and has_new_content and last_kind == "prose" and overlap > 0:
            carried = _tail_for_overlap(parts[-1], overlap)
        parts = [carried] if carried else []
        length = len(carried)
        has_new_content = False

    for unit in sized:
        if has_new_content and unit["topic"] != topic:
            emit(carry_overlap=False)                      # topic changed
        if has_new_content and length + 2 + len(unit["text"]) > chunk_size:
            emit(carry_overlap=True)                       # chunk is full
        topic = unit["topic"]
        parts.append(unit["text"])
        length += len(unit["text"]) + (2 if len(parts) > 1 else 0)
        last_kind = unit["kind"]
        has_new_content = True
    emit(carry_overlap=False)
    return chunks


# --------------------------------------------------------------------------
# Step D: the function the rest of the pipeline calls
# --------------------------------------------------------------------------
def _make_id_prefix(file_path: str) -> str:
    """'Module 4/ptr.pdf' -> 'Module_4_ptr_pdf'."""
    return re.sub(r"[^A-Za-z0-9]+", "_", file_path).strip("_")


def chunk_pages(
    pages: list[PageDict],
    chunk_size: int = config.CHUNK_SIZE,
    chunk_overlap: int = config.CHUNK_OVERLAP,
) -> list[Chunk]:
    """Turn cleaned page dictionaries into chunk dictionaries.

    Every chunk has: chunk_id, text, source, page, module, topic, file_path.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive number of characters.")
    if not 0 <= chunk_overlap < chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and smaller than chunk_size.")

    chunks: list[Chunk] = []
    topic_by_file: dict[str, str] = {}
    counter_by_page: dict[tuple[str, Any], int] = {}

    for page in pages:
        file_path = page["file_path"]
        fixed_topic = page.get("topic", config.UNKNOWN_LABEL) != config.UNKNOWN_LABEL
        start_topic = page["topic"] if fixed_topic else topic_by_file.get(file_path, config.UNKNOWN_LABEL)

        units, end_topic = _split_into_units(page["text"], start_topic, fixed_topic)
        topic_by_file[file_path] = end_topic

        for text, topic in _pack_units(units, chunk_size, chunk_overlap):
            key = (file_path, page["page"])
            counter_by_page[key] = counter_by_page.get(key, 0) + 1
            page_label = f"p{page['page']}" if page["page"] is not None else "full"
            chunks.append({
                "chunk_id": f"{_make_id_prefix(file_path)}-{page_label}-c{counter_by_page[key]}",
                "text": text,
                "source": page["source"],
                "page": page["page"],
                "module": page["module"],
                "topic": topic or config.UNKNOWN_LABEL,
                "file_path": file_path,
            })

    logger.info("Created %d chunk(s) from %d page(s).", len(chunks), len(pages))
    return chunks
