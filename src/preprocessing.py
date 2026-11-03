"""Stage 3b - Clean extracted text WITHOUT damaging C code.

The key idea
------------
Text from a PDF is a mix of ordinary explanation ("prose") and C code. They
need different treatment:

  * PROSE lines  -> tidy: collapse extra spaces, drop page numbers and other
                    obvious noise, glue back words split by a line-end hyphen.
  * CODE lines   -> left alone (only invisible trailing spaces are removed).

We never lowercase anything and never strip punctuation, so symbols such as
*  &  #  { }  ( )  [ ]  ;  < >  survive untouched.

The course has C units AND Python units (Python, NumPy, Pandas), so both
languages are recognised. Python matters most: its meaning depends on
INDENTATION, so Python lines must never be re-spaced.

Deciding whether a line is code is a *heuristic* (an educated guess based on
tell-tale signs like a trailing ';' or a '#include'). It is deliberately
cautious: when a prose line is mistaken for code, the only cost is that its
spacing is not tidied. We tune it when real PPS files are available.
"""

import logging
import re
from collections import Counter
from typing import Any

from src import config

logger = logging.getLogger(__name__)

PageDict = dict[str, Any]

# --------------------------------------------------------------------------
# Step 1: character-level normalisation
# --------------------------------------------------------------------------
_LIGATURES = {
    "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl",
}
# zero-width characters and the "soft hyphen" are invisible junk from PDFs
_INVISIBLE = {ord(c): None for c in ("\u200b", "\u200c", "\u200d", "\u2060", "\ufeff", "\u00ad")}
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0e-\x1f\x7f]")
_SMART_QUOTES = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'}


def normalize_characters(text: str) -> str:
    """Fix invisible/odd characters. Safe for code (changes no visible symbol)."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n")
    text = text.replace("\u00a0", " ")  # non-breaking space -> normal space
    text = text.translate(_INVISIBLE)
    for ligature, plain in _LIGATURES.items():
        text = text.replace(ligature, plain)
    return _CONTROL_CHARS.sub("", text)


# --------------------------------------------------------------------------
# Step 2: telling code lines from prose lines
# --------------------------------------------------------------------------
_PREPROCESSOR = re.compile(r"^#\s*(include|define|undef|ifdef|ifndef|if|elif|else|endif|pragma)\b")
_BULLET = re.compile(r"^(?:[\u2022\u00b7\u25e6\u25aa\u25cf\u25cb\u25a0\u25a1\u2013\u2014-]|\*)\s")
_CONTROL_STATEMENT = re.compile(r"^(?:if|for|while|switch)\s*\(.*\)\s*\{?$")
_FUNCTION_HEADER = re.compile(
    r"^(?:static\s+|const\s+|unsigned\s+)*(?:void|int|char|float|double|long|short)"
    r"\s*\*?\s*[A-Za-z_]\w*\(.*\)\s*\{?$"
)


# --- Python (Units 4-5 of the SRM syllabus) ---
_PY_IMPORT = re.compile(r"^(?:import\s+[\w., ]+|from\s+[\w.]+\s+import\s+.+)$")
_PY_BLOCK_HEADER = re.compile(
    r"^(?:def\s+\w+\(.*\)\s*(?:->\s*[\w.\[\], ]+)?:"
    r"|class\s+\w+.*:"
    r"|for\s+[\w, ()]+\s+in\s+.+:"
    r"|(?:if|elif|while)\s+.*[=<>!()\[\]].*:"
    r"|(?:else|try|finally):"
    r"|except\b.*:"
    r"|with\s+.+\s+as\s+\w+:)$"
)
_PY_PRINT_OR_PROMPT = re.compile(r"^(?:print\(.*\)|>>>\s.*)$")
_PY_LIBRARY_CALL = re.compile(r"^(?:np|pd|plt|numpy|pandas|df)\.[A-Za-z_]\w*")
_PY_ASSIGNMENT = re.compile(r"^[a-z_]\w*(?:\[[^\]]*\])?\s*=\s*[^=\s].*[^.,:;\s]$")


def _is_python_line(s: str) -> bool:
    return bool(
        _PY_IMPORT.match(s) or _PY_BLOCK_HEADER.match(s) or _PY_PRINT_OR_PROMPT.match(s)
        or _PY_LIBRARY_CALL.match(s) or _PY_ASSIGNMENT.match(s)
    )


def is_code_line(line: str) -> bool:
    """Return True if the line looks like a line of C or Python code."""
    s = line.strip()
    if not s:
        return False
    if _BULLET.match(s):  # "• item;" or "- item;" is a list item, not code
        return False
    if s.startswith(("//", "/*", "*/")):
        return True
    if _PREPROCESSOR.match(s):
        return True
    if s in ("{", "}", "};", "else", "do"):
        return True
    if s.endswith((";", "{", "}")):
        return True
    if _CONTROL_STATEMENT.match(s) or _FUNCTION_HEADER.match(s):
        return True
    return _is_python_line(s)


def classify_lines(lines: list[str]) -> list[str]:
    """Label each line "blank", "code" or "prose"."""
    kinds: list[str] = []
    previous = "blank"
    for line in lines:
        if not line.strip():
            kind = "blank"
        elif is_code_line(line):
            kind = "code"
        elif previous == "code" and (line.startswith("\t") or line.startswith("  ")):
            kind = "code"  # indented continuation of a multi-line statement
        else:
            kind = "prose"
        kinds.append(kind)
        previous = kind
    return kinds


# --------------------------------------------------------------------------
# Step 3: cleaning prose lines
# --------------------------------------------------------------------------
_PAGE_NUMBER = re.compile(r"^(?:page\s*)?\d{1,4}(?:\s*(?:of|/)\s*\d{1,4})?$", re.IGNORECASE)
_DECORATION = re.compile(r"^[\s.\-_=~*\u2022\u00b7]+$")  # "-----", ".....", "_____"
_HYPHEN_AT_END = re.compile(r"[A-Za-z]-$")


def clean_prose_line(line: str) -> str | None:
    """Tidy one prose line. Returns None if the line is pure noise."""
    s = re.sub(r"[ \t]+", " ", line).strip()
    if not s or _PAGE_NUMBER.match(s) or _DECORATION.match(s):
        return None
    for fancy, plain in _SMART_QUOTES.items():
        s = s.replace(fancy, plain)
    return s


def clean_text(text: str) -> str:
    """Clean one page/section of text. Code lines are preserved exactly
    (apart from invisible trailing spaces)."""
    lines = normalize_characters(text).split("\n")
    kinds = classify_lines(lines)

    cleaned: list[tuple[str, str]] = []
    for line, kind in zip(lines, kinds):
        if kind == "code":
            cleaned.append((line.rstrip(), "code"))
        elif kind == "blank":
            cleaned.append(("", "blank"))
        else:
            prose = clean_prose_line(line)
            if prose is not None:
                cleaned.append((prose, "prose"))

    # Join words split across lines: "pro-" + "gramming" -> "programming".
    merged: list[tuple[str, str]] = []
    for line, kind in cleaned:
        if (
            merged and kind == "prose" and merged[-1][1] == "prose"
            and _HYPHEN_AT_END.search(merged[-1][0]) and line[:1].islower()
        ):
            merged[-1] = (merged[-1][0][:-1] + line, "prose")
        else:
            merged.append((line, kind))

    # Never keep more than one blank line in a row.
    output: list[str] = []
    for line, _kind in merged:
        if line == "" and (not output or output[-1] == ""):
            continue
        output.append(line)
    while output and output[-1] == "":
        output.pop()
    return "\n".join(output)


# --------------------------------------------------------------------------
# Step 4: repeated headers / footers across the pages of one PDF
# --------------------------------------------------------------------------
def _repeat_key(line: str) -> str:
    """Digits become '#', so 'Page 3' and 'Page 4' count as the same line."""
    return re.sub(r"\d+", "#", line.strip().lower())


def remove_repeated_lines(pages: list[PageDict]) -> list[PageDict]:
    """Remove short lines (running headers/footers) that repeat on many pages
    of the same file. Code lines are never removed. Returns new dictionaries."""
    by_file: dict[str, list[int]] = {}
    for index, page in enumerate(pages):
        by_file.setdefault(page["file_path"], []).append(index)

    result = [dict(page) for page in pages]
    for indexes in by_file.values():
        if len(indexes) < config.REPEATED_LINE_MIN_PAGES:
            continue
        counts: Counter[str] = Counter()
        for i in indexes:
            keys_on_page = {
                _repeat_key(line)
                for line in pages[i]["text"].split("\n")
                if line.strip()
                and len(line.strip()) <= config.REPEATED_LINE_MAX_LENGTH
                and not is_code_line(line)
            }
            counts.update(keys_on_page)

        threshold = config.REPEATED_LINE_FRACTION * len(indexes)
        noise = {key for key, count in counts.items() if count >= threshold}
        if not noise:
            continue
        for i in indexes:
            kept = [
                line for line in pages[i]["text"].split("\n")
                if is_code_line(line) or _repeat_key(line) not in noise
            ]
            result[i]["text"] = "\n".join(kept)
    return result


# --------------------------------------------------------------------------
# Step 5: the one function the rest of the pipeline calls
# --------------------------------------------------------------------------
def preprocess_pages(pages: list[PageDict]) -> list[PageDict]:
    """Clean all pages. Returns NEW dictionaries (inputs are not modified).

    Pages that are empty after cleaning are dropped. All metadata (source,
    page, module, topic, file_path) is carried over unchanged.
    """
    normalized = [{**page, "text": normalize_characters(page["text"])} for page in pages]
    without_repeats = remove_repeated_lines(normalized)

    cleaned_pages: list[PageDict] = []
    for page in without_repeats:
        text = clean_text(page["text"])
        if text.strip():
            cleaned_pages.append({**page, "text": text})
    dropped = len(pages) - len(cleaned_pages)
    if dropped:
        logger.info("Dropped %d page(s) that were empty after cleaning.", dropped)
    return cleaned_pages


# --------------------------------------------------------------------------
# Heading detection (used by chunking in Stage 4 to find the "topic")
# --------------------------------------------------------------------------
_NUMBERING = re.compile(r"^\d+(?:\.\d+)*[.)]?\s+")
_MULTI_LEVEL = re.compile(r"^\d+\.\d+")
_KEYWORD_HEADING = re.compile(r"^(?:module|unit|chapter|topic|section)\s+\d+\b", re.IGNORECASE)
_SMALL_WORDS = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the", "to", "vs", "with"}
_WORD_OK = re.compile(r"[A-Za-z0-9'&/\-]+")


def _is_title_case(text: str) -> bool:
    words = text.split()
    if not words:
        return False
    for position, word in enumerate(words):
        if position > 0 and word.lower() in _SMALL_WORDS:
            continue
        if not _WORD_OK.fullmatch(word) or not word[0].isupper():
            return False
    return True


def detect_heading(line: str) -> str | None:
    """If the line looks like a section heading, return its text (without
    any leading number); otherwise None. A heuristic - to be tuned on real files."""
    s = line.strip()
    if not 3 <= len(s) <= 80 or is_code_line(s):
        return None
    if s.endswith((".", ",", ";")):
        return None
    s = s.rstrip(":").strip()

    if _KEYWORD_HEADING.match(s):  # "Module 4: Pointers"
        return s

    numbered = _NUMBERING.match(s)
    if numbered:
        rest = s[numbered.end():]
        if _MULTI_LEVEL.match(s) and rest[:1].isupper() and len(rest.split()) <= 10:
            return rest  # "4.2 Pointer arithmetic"
        if _is_title_case(rest) and len(rest.split()) <= 6:
            return rest  # "4 Pointers"
        return None

    words = s.split()
    letters = [c for c in s if c.isalpha()]
    if letters and s == s.upper() and len(words) <= 8 and (len(words) >= 2 or len(letters) >= 5):
        return s  # "ARRAYS AND STRINGS"
    if len(words) <= 6 and _is_title_case(s):
        return s  # "Pointer Arithmetic"
    return None
