"""Tests for chunking, embeddings, vector store, retrieval, RAGContext,
ingestion and evaluation metrics.

IMPORTANT: all documents here are FAKE test text ("alpha widget", "beta
gadget"...). They are NOT PPS curriculum and are never used by the real
pipeline. Tests use a tiny fake embedder, so they need no internet, no model
download and no external APIs. (Loading documents and C-code preservation are
tested in test_loading_and_preprocessing.py.)
"""

import json
import sys
from pathlib import Path

import pytest
from tests.helpers import HashingEmbedder

from eduadapt.rag import config
from eduadapt.rag.chunking import chunk_pages
from eduadapt.rag.embeddings import Embedder
from eduadapt.rag.preprocessing import preprocess_pages
from eduadapt.interfaces.rag import RAGContext, RAGDocument
from eduadapt.rag.rag_interface import PPSCurriculumRAG
from eduadapt.rag.retriever import Retriever
from eduadapt.rag.vector_store import VectorStore

ROOT = Path(config.MODULE_ROOT)
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "rag"))
sys.path.insert(0, str(ROOT / "evaluation"))
import evaluate_retrieval as ev  # noqa: E402
import ingest  # noqa: E402

FAKE_C_BLOCK = "#include <stdio.h>\nint main() {\n    int banana = 1;\n    return 0;\n}"

FAKE_DOCUMENT = f"""FAKE ALPHA TOPIC

The alpha widget stores a banana value. Banana values are kept inside the alpha widget.

{FAKE_C_BLOCK}

FAKE BETA TOPIC

The beta gadget counts cherries. Cherry counting happens inside the beta gadget loop.
"""

REQUIRED_CHUNK_KEYS = {"chunk_id", "text", "source", "page", "module", "topic"}


def fake_pages(text: str = FAKE_DOCUMENT) -> list[dict]:
    return [{
        "text": text, "source": "module_7_fake.txt", "page": None,
        "module": "Module 7", "topic": config.UNKNOWN_LABEL, "file_path": "module_7_fake.txt",
    }]


@pytest.fixture
def embedder() -> HashingEmbedder:
    return HashingEmbedder()


@pytest.fixture
def fake_chunks() -> list[dict]:
    return chunk_pages(preprocess_pages(fake_pages()))


@pytest.fixture
def populated_store(tmp_path, embedder, fake_chunks):
    store = VectorStore(path=tmp_path / "db", collection_name="test_collection")
    store.create_collection(embedder.dimension)
    store.upsert_chunks(fake_chunks, embedder.embed_texts([c["text"] for c in fake_chunks]))
    yield store
    store.close()


# ===========================================================================
# Chunking
# ===========================================================================
def test_every_chunk_has_required_metadata(fake_chunks):
    assert fake_chunks
    for chunk in fake_chunks:
        assert REQUIRED_CHUNK_KEYS <= set(chunk)
        assert chunk["text"].strip()
        assert chunk["source"] == "module_7_fake.txt"
        assert chunk["module"] == "Module 7"


def test_topics_come_from_headings_and_are_not_mixed(fake_chunks):
    topics = {c["topic"] for c in fake_chunks}
    assert topics == {"FAKE ALPHA TOPIC", "FAKE BETA TOPIC"}
    for chunk in fake_chunks:
        assert not ("alpha" in chunk["text"].lower() and "beta gadget" in chunk["text"].lower())


def test_c_code_block_stays_in_one_chunk_unchanged(fake_chunks):
    holders = [c for c in fake_chunks if "#include" in c["text"]]
    assert len(holders) == 1
    assert FAKE_C_BLOCK in holders[0]["text"]


def test_chunk_ids_are_unique_and_readable(fake_chunks):
    ids = [c["chunk_id"] for c in fake_chunks]
    assert len(ids) == len(set(ids))
    assert all(i.startswith("module_7_fake_txt-full-c") for i in ids)


def test_page_numbers_are_kept_for_pdf_style_pages():
    pages = [
        {"text": "FAKE ALPHA TOPIC\n\nThe alpha widget text.", "source": "f.pdf", "page": 3,
         "module": "Module 1", "topic": config.UNKNOWN_LABEL, "file_path": "f.pdf"},
        {"text": "More alpha widget text on the next page.", "source": "f.pdf", "page": 4,
         "module": "Module 1", "topic": config.UNKNOWN_LABEL, "file_path": "f.pdf"},
    ]
    chunks = chunk_pages(pages)
    assert [c["page"] for c in chunks] == [3, 4]
    assert chunks[1]["topic"] == "FAKE ALPHA TOPIC"  # topic carries onto the next page
    assert chunks[0]["chunk_id"] == "f_pdf-p3-c1"


def test_long_text_is_split_with_overlap():
    sentences = " ".join(f"Sentence number {i} talks about the fake gizmo." for i in range(80))
    chunks = chunk_pages(fake_pages(sentences), chunk_size=300, chunk_overlap=60)
    assert len(chunks) > 5
    for chunk in chunks:
        assert len(chunk["text"]) <= 300 + 60 + 5
    for before, after in zip(chunks, chunks[1:]):
        shared = set(before["text"].split()[-6:]) & set(after["text"].split()[:12])
        assert shared, "consecutive chunks should overlap"


def test_huge_code_block_is_split_only_between_lines():
    code = "\n".join(f"    value_{i} = {i};" for i in range(200))
    chunks = chunk_pages(fake_pages(code), chunk_size=300, chunk_overlap=0)
    assert len(chunks) > 1
    rebuilt = "\n\n".join(c["text"] for c in chunks)
    for line in code.split("\n"):
        assert line.rstrip() in rebuilt


def test_chunking_rejects_bad_settings():
    with pytest.raises(ValueError):
        chunk_pages(fake_pages(), chunk_size=0)
    with pytest.raises(ValueError):
        chunk_pages(fake_pages(), chunk_size=100, chunk_overlap=100)


def test_curriculum_map_topic_is_not_overridden_by_headings():
    pages = fake_pages()
    pages[0]["topic"] = "Mapped Topic"
    assert {c["topic"] for c in chunk_pages(preprocess_pages(pages))} == {"Mapped Topic"}


# ===========================================================================
# Embeddings
# ===========================================================================
def test_fake_embedder_gives_expected_dimensions_and_unit_length(embedder):
    vectors = embedder.embed_texts(["alpha widget", "beta gadget"])
    assert len(vectors) == 2
    assert all(len(v) == embedder.dimension == 64 for v in vectors)
    assert sum(x * x for x in vectors[0]) == pytest.approx(1.0)


def test_embedder_caches_repeated_queries():
    emb = Embedder()  # model is NOT loaded here (lazy)
    calls = []

    def fake_embed_texts(texts):
        calls.append(texts)
        return [[0.1, 0.2, 0.3] for _ in texts]

    emb.embed_texts = fake_embed_texts  # replace the real (slow) encoding
    assert emb.embed_query("same question") == emb.embed_query("  same question ")
    assert len(calls) == 1
    with pytest.raises(ValueError):
        emb.embed_query("   ")


def test_embedder_does_not_load_model_until_needed():
    assert Embedder()._model is None


def test_real_model_has_384_dimensions_if_already_downloaded():
    """Uses the real model ONLY if it is already cached on this computer;
    never downloads anything during tests."""
    pytest.importorskip("sentence_transformers")
    try:
        emb = Embedder(local_files_only=True)
        dimension = emb.dimension
    except Exception:
        pytest.skip("Embedding model not in the local cache yet (run scripts/ingest.py once).")
    assert dimension == 384
    assert len(emb.embed_texts(["int *p = &x;"])[0]) == 384


# ===========================================================================
# Vector store (local Qdrant)
# ===========================================================================
def test_vector_store_creates_and_counts(populated_store, fake_chunks):
    assert populated_store.collection_exists()
    assert populated_store.count() == len(fake_chunks)


def test_vector_store_persists_on_disk(tmp_path, embedder, fake_chunks):
    path = tmp_path / "db"
    with VectorStore(path=path, collection_name="persist") as store:
        store.create_collection(embedder.dimension)
        store.upsert_chunks(fake_chunks, embedder.embed_texts([c["text"] for c in fake_chunks]))
    with VectorStore(path=path, collection_name="persist") as reopened:  # a "new session"
        assert reopened.count() == len(fake_chunks)
        hit = reopened.search(embedder.embed_query("alpha widget banana"), top_k=1)[0]
        assert hit["payload"]["chunk_id"]


def test_same_chunk_id_overwrites_instead_of_duplicating(populated_store, embedder, fake_chunks):
    before = populated_store.count()
    populated_store.upsert_chunks(fake_chunks, embedder.embed_texts([c["text"] for c in fake_chunks]))
    assert populated_store.count() == before


def test_rebuild_wipes_old_chunks(populated_store, embedder):
    populated_store.create_collection(embedder.dimension, rebuild=True)
    assert populated_store.count() == 0


def test_vector_size_mismatch_gives_helpful_error(populated_store):
    with pytest.raises(ValueError, match="rebuild"):
        populated_store.create_collection(vector_size=999)


def test_upsert_checks_matching_lengths(populated_store, fake_chunks):
    with pytest.raises(ValueError):
        populated_store.upsert_chunks(fake_chunks, [])


def test_search_on_missing_collection_explains_how_to_fix(tmp_path):
    with VectorStore(path=tmp_path / "db", collection_name="nope") as store:
        assert store.count() == 0
        with pytest.raises(RuntimeError, match="ingest"):
            store.search([0.0] * 4, top_k=1)


# ===========================================================================
# Retrieval
# ===========================================================================
def test_retrieval_returns_top_k_results_with_metadata(populated_store, embedder):
    retriever = Retriever(embedder, populated_store)
    results = retriever.retrieve("alpha widget banana", top_k=2)
    assert len(results) == 2
    for result in results:
        assert {"text", "score", "source", "page", "module", "topic", "chunk_id"} <= set(result)
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_retrieval_ranks_the_matching_topic_first(populated_store, embedder):
    retriever = Retriever(embedder, populated_store)
    assert retriever.retrieve("beta gadget cherries", top_k=3)[0]["topic"] == "FAKE BETA TOPIC"
    assert retriever.retrieve("alpha widget banana", top_k=3)[0]["topic"] == "FAKE ALPHA TOPIC"


def test_top_k_is_configurable_and_capped_by_database_size(populated_store, embedder, fake_chunks):
    retriever = Retriever(embedder, populated_store, default_top_k=1)
    assert len(retriever.retrieve("alpha")) == 1
    assert len(retriever.retrieve("alpha", top_k=50)) == len(fake_chunks)


def test_min_score_filters_weak_matches(populated_store, embedder):
    retriever = Retriever(embedder, populated_store)
    assert retriever.retrieve("completely unrelated zebra", top_k=5, min_score=0.99) == []


def test_retrieval_rejects_bad_input(populated_store, embedder):
    retriever = Retriever(embedder, populated_store)
    with pytest.raises(ValueError):
        retriever.retrieve("   ")
    with pytest.raises(ValueError):
        retriever.retrieve("alpha", top_k=0)


# ===========================================================================
# RAG interface / RAGContext  (placeholder contract - see rag_interface.py)
# ===========================================================================
def test_rag_context_has_expected_fields(populated_store, embedder):
    rag = PPSCurriculumRAG(Retriever(embedder, populated_store))
    context = rag.retrieve(query="alpha widget banana", top_k=2)
    assert isinstance(context, RAGContext)
    assert context.query == "alpha widget banana"
    assert 1 <= len(context.documents) <= 2
    doc = context.documents[0]
    assert isinstance(doc, RAGDocument)
    for attribute in ("text", "score", "source", "page", "module", "topic", "chunk_id"):
        assert hasattr(doc, attribute)
    assert doc.source == "module_7_fake.txt" and doc.module == "Module 7"


def test_format_for_prompt_contains_source_labels(populated_store, embedder):
    rag = PPSCurriculumRAG(Retriever(embedder, populated_store))
    text = rag.format_for_prompt(rag.retrieve("alpha widget banana", top_k=1))
    assert "module_7_fake.txt" in text and "Module 7" in text and "alpha widget" in text
    assert "No relevant" in rag.format_for_prompt(RAGContext(query="x", documents=[]))


def test_from_defaults_refuses_empty_database(tmp_path, embedder):
    with pytest.raises(RuntimeError, match="ingest"):
        PPSCurriculumRAG.from_defaults(db_path=tmp_path / "empty_db", embedder=embedder)


# ===========================================================================
# Ingestion pipeline (files -> Qdrant -> RAGContext), all fake + local
# ===========================================================================
def _ingest(tmp_path, embedder, **kwargs):
    data = tmp_path / "pps"
    data.mkdir(exist_ok=True)
    (data / "module_7_fake.txt").write_text(FAKE_DOCUMENT, encoding="utf-8")
    return ingest.run_ingestion(
        data_dir=data, db_path=tmp_path / "db", collection_name="t",
        embedder=embedder, processed_dir=tmp_path / "processed", **kwargs,
    )


def test_ingestion_builds_database_and_retrieval_works_end_to_end(tmp_path, embedder):
    summary = _ingest(tmp_path, embedder)
    assert summary["chunks_in_database"] == summary["chunks_created"] > 0
    lines = (tmp_path / "processed" / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
    assert REQUIRED_CHUNK_KEYS <= set(json.loads(lines[0]))

    rag = PPSCurriculumRAG.from_defaults(db_path=tmp_path / "db", collection_name="t", embedder=embedder)
    try:
        context = rag.retrieve("beta gadget cherries", top_k=3)
    finally:
        rag.close()
    assert context.documents[0].topic == "FAKE BETA TOPIC"


def test_ingestion_twice_does_not_duplicate_and_rebuild_works(tmp_path, embedder):
    first = _ingest(tmp_path, embedder)
    second = _ingest(tmp_path, embedder)
    assert second["chunks_in_database"] == first["chunks_in_database"]
    third = _ingest(tmp_path, embedder, rebuild=True)
    assert third["chunks_in_database"] == first["chunks_in_database"]


def test_ingestion_without_documents_gives_clear_error(tmp_path, embedder):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(RuntimeError, match="No readable PPS pages"):
        ingest.run_ingestion(data_dir=empty, db_path=tmp_path / "db", embedder=embedder,
                             processed_dir=tmp_path / "p")


def test_ingestion_respects_chunk_settings(tmp_path, embedder):
    big = _ingest(tmp_path, embedder, chunk_size=2000, chunk_overlap=0)
    small_dir = tmp_path / "small"
    small_dir.mkdir()
    small = _ingest(small_dir, embedder, chunk_size=80, chunk_overlap=10, rebuild=True)
    assert small["chunks_created"] > big["chunks_created"]


# ===========================================================================
# Evaluation metrics (pure functions, no database needed)
# ===========================================================================
def _res(topic, source="s.pdf", module="Module 1"):
    return {"topic": topic, "source": source, "module": module, "score": 0.5, "page": 1}


def test_metrics_for_first_hit():
    spec = {"id": "x", "query": "q", "expected_topics": ["Pointers"]}
    results = [_res("Pointers"), _res("Arrays"), _res("Loops")]
    assert ev.score_query(spec, results, k=3) == {"hit": 1.0, "recall": 1.0, "rr": 1.0}


def test_metrics_for_third_rank_hit_and_miss():
    spec = {"id": "x", "query": "q", "expected_topics": ["Pointers"]}
    third = [_res("Arrays"), _res("Loops"), _res("Pointers basics")]  # substring match counts
    assert ev.score_query(spec, third, k=3)["rr"] == pytest.approx(1 / 3)
    assert ev.score_query(spec, third, k=2)["hit"] == 0.0  # outside top 2
    miss = [_res("Arrays"), _res("Loops")]
    assert ev.score_query(spec, miss, k=2) == {"hit": 0.0, "recall": 0.0, "rr": 0.0}


def test_topic_matching_is_a_case_insensitive_substring_check():
    spec = {"id": "x", "query": "q", "expected_topics": ["pointers"]}
    assert ev.is_relevant(spec, _res("POINTERS and Addresses"))
    assert not ev.is_relevant(spec, _res("Pointer arithmetic"))  # "pointers" is not inside it


def test_recall_counts_share_of_expected_items_found():
    spec = {"id": "x", "query": "q", "expected_topics": ["Pointers", "Arrays"]}
    assert ev.score_query(spec, [_res("Pointers"), _res("Loops")], k=2)["recall"] == 0.5


def test_unfilled_template_queries_are_skipped():
    queries = [{"id": "a", "query": "q", "expected_topics": [], "expected_sources": [], "expected_modules": []}]
    report = ev.evaluate(queries, lambda q, k: [], top_k=5)
    assert report["details"] == [] and report["skipped"] == ["a"]


def test_evaluate_aggregates_over_ready_queries():
    queries = [
        {"id": "a", "query": "qa", "expected_topics": ["Pointers"]},
        {"id": "b", "query": "qb", "expected_sources": ["x.pdf"]},
    ]
    data = {"qa": [_res("Pointers")], "qb": [_res("Loops", source="y.pdf")]}
    report = ev.evaluate(queries, lambda q, k: data[q], top_k=3)
    assert report["by_k"][3]["queries"] == 2
    assert report["by_k"][3]["hit_rate"] == 0.5 and report["by_k"][3]["mrr"] == 0.5
