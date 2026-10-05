"""Stage 3 tests: document loading + preprocessing.

IMPORTANT: every document in this file is FAKE and exists only for testing.
It is NOT PPS curriculum content and is never used by the real pipeline.
These tests need no internet and no external services.
"""

import ast
import json
import logging
from pathlib import Path

import pytest
from tests.helpers import make_pdf

from eduadapt.rag import config
from eduadapt.rag.document_loader import (
    DocumentLoadError,
    detect_module,
    load_document,
    load_documents,
)
from eduadapt.rag.preprocessing import (
    clean_text,
    detect_heading,
    is_code_line,
    preprocess_pages,
    remove_repeated_lines,
)

# A fake C snippet used to prove code is preserved character-for-character.
FAKE_C_CODE = (
    "#include <stdio.h>\n"
    "\n"
    "int main() {\n"
    "    int x = 10;\n"
    "    int *p = &x;\n"
    '    printf("Value: %d\\n", *p);\n'
    "    return 0;\n"
    "}"
)


# ===========================================================================
# Python version (project requirement: Python 3.11.0)
# ===========================================================================
def test_python_version_guard_rejects_other_versions():
    with pytest.raises(RuntimeError):
        config.check_python_version((3, 12, 0))
    with pytest.raises(RuntimeError):
        config.check_python_version((3, 10, 11))
    config.check_python_version((3, 11, 0))  # exactly the team version: fine


def test_python_version_guard_warns_on_other_311_patch(caplog):
    with caplog.at_level(logging.WARNING, logger="eduadapt.rag.config"):
        config.check_python_version((3, 11, 9))
    assert "3.11.0" in caplog.text


def test_source_files_use_only_python_311_syntax():
    """Parse every src/ and scripts/ file as Python 3.11 code. Newer-only
    syntax (e.g. 3.12 'type X = ...' statements) would fail here."""
    root = Path(config.MODULE_ROOT)
    files = list((root / "src").rglob("*.py")) + list((root / "scripts").rglob("*.py"))
    assert files
    for file in files:
        ast.parse(file.read_text(encoding="utf-8"), filename=str(file), feature_version=(3, 11))


# ===========================================================================
# Document loading
# ===========================================================================
def test_loads_text_file_with_metadata(tmp_path):
    (tmp_path / "module_2_fake.txt").write_text("Fake test text.", encoding="utf-8")
    pages, problems = load_documents(tmp_path)
    assert problems == []
    assert len(pages) == 1
    page = pages[0]
    assert page["text"] == "Fake test text."
    assert page["source"] == "module_2_fake.txt"
    assert page["page"] is None  # text files have no page numbers
    assert page["module"] == "Module 2"
    assert page["topic"] == config.UNKNOWN_LABEL


def test_loads_pdf_pages_with_page_numbers(tmp_path):
    pdf = make_pdf([["Fake first page."], ["Fake second page."]])
    (tmp_path / "module_1_fake.pdf").write_bytes(pdf)
    pages, problems = load_documents(tmp_path)
    assert problems == []
    assert [p["page"] for p in pages] == [1, 2]
    assert "Fake first page." in pages[0]["text"]
    assert "Fake second page." in pages[1]["text"]
    assert all(p["source"] == "module_1_fake.pdf" for p in pages)
    assert all(p["module"] == "Module 1" for p in pages)


def test_loads_multiple_documents_including_subfolders(tmp_path):
    (tmp_path / "a.txt").write_text("Fake A", encoding="utf-8")
    sub = tmp_path / "Module 3"
    sub.mkdir()
    (sub / "b.md").write_text("Fake B", encoding="utf-8")
    pages, problems = load_documents(tmp_path)
    assert problems == []
    assert {p["source"] for p in pages} == {"a.txt", "b.md"}
    by_source = {p["source"]: p for p in pages}
    assert by_source["a.txt"]["module"] == config.UNKNOWN_LABEL
    assert by_source["b.md"]["module"] == "Module 3"  # taken from the folder name


def test_detect_module_examples():
    assert detect_module(Path("module_4_pointers.pdf")) == "Module 4"
    assert detect_module(Path("Module-04.pdf")) == "Module 4"
    assert detect_module(Path("Unit 2/notes.pdf")) == "Unit 2"
    assert detect_module(Path("notes.pdf")) == config.UNKNOWN_LABEL


def test_curriculum_map_overrides_module_and_topic(tmp_path):
    (tmp_path / "notes.txt").write_text("Fake text", encoding="utf-8")
    mapping = {"notes.txt": {"module": "Module 9", "topic": "Fake Topic"}}
    (tmp_path / "curriculum_map.json").write_text(json.dumps(mapping), encoding="utf-8")
    pages, _ = load_documents(tmp_path)
    assert pages[0]["module"] == "Module 9"
    assert pages[0]["topic"] == "Fake Topic"


def test_broken_curriculum_map_is_ignored(tmp_path):
    (tmp_path / "module_1.txt").write_text("Fake text", encoding="utf-8")
    (tmp_path / "curriculum_map.json").write_text("{not valid json", encoding="utf-8")
    pages, problems = load_documents(tmp_path)
    assert len(pages) == 1 and problems == []
    assert pages[0]["module"] == "Module 1"


def test_corrupt_pdf_is_skipped_but_other_files_still_load(tmp_path):
    (tmp_path / "broken.pdf").write_bytes(b"this is not a real pdf at all")
    (tmp_path / "good.txt").write_text("Fake good text", encoding="utf-8")
    pages, problems = load_documents(tmp_path)
    assert [p["source"] for p in pages] == ["good.txt"]
    assert len(problems) == 1
    assert problems[0][0] == "broken.pdf"


def test_pdf_without_text_is_reported_as_problem(tmp_path):
    (tmp_path / "blank.pdf").write_bytes(make_pdf([[]]))
    pages, problems = load_documents(tmp_path)
    assert pages == []
    assert "no extractable text" in problems[0][1]


def test_empty_text_file_is_reported_as_problem(tmp_path):
    (tmp_path / "empty.txt").write_text("   \n", encoding="utf-8")
    _, problems = load_documents(tmp_path)
    assert problems and problems[0][0] == "empty.txt"


def test_unsupported_file_types_are_ignored(tmp_path):
    (tmp_path / "picture.png").write_bytes(b"\x89PNG")
    pages, problems = load_documents(tmp_path)
    assert pages == [] and problems == []


def test_load_document_rejects_unsupported_type(tmp_path):
    path = tmp_path / "data.xyz"
    path.write_text("x", encoding="utf-8")
    with pytest.raises(DocumentLoadError):
        load_document(path)


def test_missing_folder_gives_helpful_error(tmp_path):
    with pytest.raises(FileNotFoundError) as info:
        load_documents(tmp_path / "does_not_exist")
    assert "PPS data folder not found" in str(info.value)


def test_empty_folder_returns_nothing_without_crashing(tmp_path):
    pages, problems = load_documents(tmp_path)
    assert pages == [] and problems == []


# ===========================================================================
# Preprocessing
# ===========================================================================
def test_c_code_is_preserved_exactly():
    text = "Fake explanation sentence.\n\n" + FAKE_C_CODE + "\n\nAnother fake sentence."
    cleaned = clean_text(text)
    assert FAKE_C_CODE in cleaned  # character-for-character, indentation included


def test_programming_symbols_survive():
    snippet = "int *p = &arr[0]; if (a < b && c > d) { x = y; }"
    cleaned = clean_text(snippet)
    for symbol in "*&#{}()[];<>":
        if symbol in snippet:
            assert symbol in cleaned
    assert cleaned == snippet


def test_case_is_never_changed():
    cleaned = clean_text("The macro NULL and the type FILE stay as written.\nint Main_Value = 0;")
    assert "NULL" in cleaned and "FILE" in cleaned and "Main_Value" in cleaned


def test_extra_whitespace_in_prose_is_collapsed():
    cleaned = clean_text("A    sentence   with \t odd    spacing.\n\n\n\n\nNext paragraph.")
    assert cleaned == "A sentence with odd spacing.\n\nNext paragraph."


def test_page_numbers_and_decoration_lines_are_removed():
    cleaned = clean_text("Fake sentence.\n12\nPage 3 of 10\n----------\nAnother sentence.")
    assert cleaned == "Fake sentence.\nAnother sentence."


def test_hyphenated_line_break_is_joined():
    assert clean_text("a fake pro-\ngramming word") == "a fake programming word"


def test_ligatures_and_invisible_characters_are_fixed():
    cleaned = clean_text("\ufb01rst \ufb02ow\u200b co\u00admputer\u00a0text")
    assert cleaned == "first flow computer text"


def test_smart_quotes_fixed_in_prose_but_code_left_alone():
    cleaned = clean_text("He said \u201cfake\u201d.\nchar c = '\u2019';")
    assert 'He said "fake".' in cleaned
    assert "char c = '\u2019';" in cleaned  # code line untouched


def test_is_code_line_examples():
    for code in ["#include <stdio.h>", "int x = 5;", "}", "if (x > 0) {", "int main()",
                 "// a comment", "*p = 5;", 'printf("hi");']:
        assert is_code_line(code), code
    for prose in ["This is an ordinary sentence.", "- a list item;", "\u2022 another item;", ""]:
        assert not is_code_line(prose), prose


def test_repeated_headers_and_footers_are_removed_but_code_is_kept():
    unique = ["alpha", "bravo", "charlie", "delta"]
    pages = [
        {
            "text": f"FAKE COURSE HEADER\nUnique {word} sentence here.\nreturn 0;\nPage {i + 1}",
            "source": "f.pdf", "page": i + 1, "module": "Module 1",
            "topic": "Unknown", "file_path": "f.pdf",
        }
        for i, word in enumerate(unique)
    ]
    result = remove_repeated_lines(pages)
    for page, word in zip(result, unique):
        assert "FAKE COURSE HEADER" not in page["text"]
        assert "Page" not in page["text"]
        assert f"Unique {word} sentence here." in page["text"]
        assert "return 0;" in page["text"]  # repeated, but it is code: kept


def test_preprocess_pages_keeps_metadata_and_does_not_modify_input():
    original = [{
        "text": "  Fake   text  \n" + FAKE_C_CODE, "source": "s.pdf", "page": 7,
        "module": "Module 4", "topic": "Fake Topic", "file_path": "s.pdf",
    }]
    snapshot = json.loads(json.dumps(original))
    result = preprocess_pages(original)
    assert original == snapshot  # input unchanged
    assert len(result) == 1
    for key in ("source", "page", "module", "topic", "file_path"):
        assert result[0][key] == original[0][key]
    assert FAKE_C_CODE in result[0]["text"]


def test_pages_that_become_empty_are_dropped():
    pages = [{"text": "12\n-----", "source": "s.pdf", "page": 1, "module": "Unknown",
              "topic": "Unknown", "file_path": "s.pdf"}]
    assert preprocess_pages(pages) == []


def test_detect_heading_examples():
    assert detect_heading("4.2 Pointer arithmetic") == "Pointer arithmetic"
    assert detect_heading("Module 4: Fake Title") == "Module 4: Fake Title"
    assert detect_heading("ARRAYS AND STRINGS") == "ARRAYS AND STRINGS"
    assert detect_heading("Pointers") == "Pointers"
    assert detect_heading("This is an ordinary sentence about something.") is None
    assert detect_heading("int x = 5;") is None
    assert detect_heading("1. declare the variable first") is None


def test_end_to_end_load_then_preprocess(tmp_path):
    pdf = make_pdf([
        ["Fake heading", "Some   fake   words."],
        ["int x = 5;", "return 0;"],
    ])
    (tmp_path / "module_5_fake.pdf").write_bytes(pdf)
    pages, problems = load_documents(tmp_path)
    cleaned = preprocess_pages(pages)
    assert problems == []
    assert [p["page"] for p in cleaned] == [1, 2]
    assert "Some fake words." in cleaned[0]["text"]
    assert "int x = 5;" in cleaned[1]["text"]
    assert all(p["module"] == "Module 5" for p in cleaned)
