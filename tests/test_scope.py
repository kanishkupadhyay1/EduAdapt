"""Consistency checks between the syllabus scope file and the evaluation queries.
(Pure file checks - no model, no database.)"""

import json
from pathlib import Path

from src import config

ROOT = Path(config.MODULE_ROOT)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_scope_file_lists_five_units_with_topics():
    scope = _load(ROOT / "curriculum" / "srm_21CSS101J_scope.json")
    assert [u["unit"] for u in scope["units"]] == [f"Unit {n}" for n in range(1, 6)]
    assert all(u["topics"] for u in scope["units"])


def test_every_evaluation_query_points_at_a_real_syllabus_unit():
    scope = _load(ROOT / "curriculum" / "srm_21CSS101J_scope.json")
    valid = {u["unit"] for u in scope["units"]}
    queries = _load(ROOT / "evaluation" / "test_queries.json")["queries"]
    assert len(queries) >= 10
    ids = [q["id"] for q in queries]
    assert len(ids) == len(set(ids))
    for q in queries:
        assert q["query"].strip()
        assert set(q["expected_modules"]) <= valid
