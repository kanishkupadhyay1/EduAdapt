"""Evaluate RETRIEVAL quality against evaluation/test_queries.json.

These are RETRIEVAL metrics (did the search find the right curriculum
material?). They are NOT "LLM accuracy" and say nothing about how well
Mistral answers.

For each query we look at the top K results and check them against what you
declared as expected (topics / source files / modules):

  * a result is RELEVANT if it matches ANY expected topic, source or module
    (case-insensitive; topics match if one contains the other)
  * Hit@K    1 if at least one relevant result is in the top K, else 0
  * Recall@K share of the expected items (topics/sources/modules) that appear
             somewhere in the top K results
  * MRR      1 / rank of the first relevant result (0 if none): 1.0 = first.

Run from the member2_rag folder:
    python evaluation/evaluate_retrieval.py
    python evaluation/evaluate_retrieval.py --top-k 5 --output evaluation/last_report.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from eduadapt.rag import config  # noqa: E402

DEFAULT_QUERIES = Path(__file__).resolve().parent / "test_queries.json"
Result = dict[str, Any]
Spec = dict[str, Any]


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _topic_match(expected: str, actual: str) -> bool:
    e, a = _norm(expected), _norm(actual)
    return bool(e and a and (e in a or a in e))


def expected_items(spec: Spec) -> list[tuple[str, str]]:
    """List of (kind, value) the query expects. Empty => query is not ready."""
    items: list[tuple[str, str]] = []
    for kind, key in (("topic", "expected_topics"), ("source", "expected_sources"), ("module", "expected_modules")):
        items += [(kind, v) for v in spec.get(key, []) if _norm(v)]
    return items


def item_matches(item: tuple[str, str], result: Result) -> bool:
    kind, value = item
    if kind == "topic":
        return _topic_match(value, result.get("topic", ""))
    return _norm(value) == _norm(result.get("source" if kind == "source" else "module", ""))


def is_relevant(spec: Spec, result: Result) -> bool:
    return any(item_matches(item, result) for item in expected_items(spec))


def score_query(spec: Spec, results: list[Result], k: int) -> dict[str, float]:
    """Hit@k, Recall@k and reciprocal rank for ONE query."""
    top = results[:k]
    items = expected_items(spec)
    first_rank = next((i for i, r in enumerate(results, 1) if is_relevant(spec, r)), None)
    hit = 1.0 if any(is_relevant(spec, r) for r in top) else 0.0
    covered = sum(1 for item in items if any(item_matches(item, r) for r in top))
    recall = covered / len(items) if items else 0.0
    rr = 1.0 / first_rank if first_rank else 0.0
    return {"hit": hit, "recall": recall, "rr": rr}


def summarize(per_query: list[dict[str, float]]) -> dict[str, float]:
    n = len(per_query)
    if n == 0:
        return {"queries": 0, "hit_rate": 0.0, "mean_recall": 0.0, "mrr": 0.0}
    return {
        "queries": n,
        "hit_rate": sum(q["hit"] for q in per_query) / n,
        "mean_recall": sum(q["recall"] for q in per_query) / n,
        "mrr": sum(q["rr"] for q in per_query) / n,
    }


def evaluate(queries: list[Spec], retrieve_fn, top_k: int) -> dict[str, Any]:
    """Run all ready queries. ``retrieve_fn(query, top_k) -> list[Result]``."""
    ready = [q for q in queries if expected_items(q)]
    skipped = [q["id"] for q in queries if not expected_items(q)]
    details = []
    for spec in ready:
        results = retrieve_fn(spec["query"], top_k)
        details.append({"spec": spec, "results": results, "scores": score_query(spec, results, top_k)})
    ks = sorted({k for k in (1, 3, top_k) if k <= top_k})
    by_k = {
        k: summarize([score_query(d["spec"], d["results"], k) for d in details]) for k in ks
    }
    return {"top_k": top_k, "details": details, "skipped": skipped, "by_k": by_k}


def print_report(report: dict[str, Any]) -> None:
    print("=" * 70)
    print("PPS RETRIEVAL EVALUATION (retrieval metrics - NOT LLM accuracy)")
    print("=" * 70)
    for d in report["details"]:
        spec, results, s = d["spec"], d["results"], d["scores"]
        expected = ", ".join(f"{k}={v}" for k, v in expected_items(spec))
        print(f"\nQuery: {spec['query']}")
        print(f"Expected: {expected}")
        print(f"Top {report['top_k']} retrieved:")
        for rank, r in enumerate(results, 1):
            mark = "  <- relevant" if is_relevant(spec, r) else ""
            page = f"p{r['page']}" if r.get("page") is not None else "-"
            print(f"  {rank}. {r['topic']} | {r['source']} {page} | score {r['score']:.3f}{mark}")
        print(f"  => Hit@{report['top_k']}={s['hit']:.0f}  Recall@{report['top_k']}={s['recall']:.2f}  RR={s['rr']:.2f}")
    if report["skipped"]:
        print(f"\nSkipped (no expected_* filled in yet): {', '.join(report['skipped'])}")
    print("\n" + "-" * 70)
    if not report["details"]:
        print("No evaluable queries. Fill in expected_topics/sources/modules in")
        print("evaluation/test_queries.json using the REAL curriculum (see its _README).")
        return
    for k, m in report["by_k"].items():
        print(f"K={k}: Hit rate={m['hit_rate']:.2f}  Mean Recall@K={m['mean_recall']:.2f}  MRR={m['mrr']:.2f}  ({m['queries']} queries)")
    print("(MRR is computed over the retrieved list of length top_k.)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate PPS retrieval.")
    parser.add_argument("--queries", default=str(DEFAULT_QUERIES))
    parser.add_argument("--top-k", type=int, default=config.TOP_K)
    parser.add_argument("--db-path", default=str(config.VECTOR_DB_DIR))
    parser.add_argument("--collection", default=config.COLLECTION_NAME)
    parser.add_argument("--model", default=config.EMBEDDING_MODEL_NAME)
    parser.add_argument("--output", default=None, help="Optional JSON file to save the report")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    data = json.loads(Path(args.queries).read_text(encoding="utf-8"))
    queries = data["queries"] if isinstance(data, dict) else data
    if not any(expected_items(q) for q in queries):
        print_report({"top_k": args.top_k, "details": [], "skipped": [q["id"] for q in queries], "by_k": {}})
        return

    from eduadapt.rag.embeddings import Embedder
    from eduadapt.rag.retriever import Retriever
    from eduadapt.rag.vector_store import VectorStore

    try:
        with VectorStore(path=args.db_path, collection_name=args.collection) as store:
            if store.count() == 0:
                print("ERROR: the vector database is empty. Run: python scripts/ingest.py")
                sys.exit(1)
            retriever = Retriever(Embedder(model_name=args.model), store)
            report = evaluate(queries, lambda q, k: retriever.retrieve(q, top_k=k), args.top_k)
    except (RuntimeError, ImportError) as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    print_report(report)
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        print(f"\nReport saved to {args.output}")


if __name__ == "__main__":
    main()
