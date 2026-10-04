# Member 2 - PPS Curriculum RAG (NLP module)


## 1. What this module does

It turns the **real PPS (Programming for Problem Solving) course material** into a searchable
knowledge base and, given a student's question, returns the most relevant pieces of that
material together with where they came from (file, page, module, topic).

```
PPS files -> load -> clean -> chunk -> embed -> Qdrant (local) -> retrieve -> RAGContext
```

It works **independently of Member 1's Mistral code**. It is a plain, fixed pipeline - no agents,
no autonomous decisions, no LLM calls.

## 2. What "RAG" means

**R**etrieval-**A**ugmented **G**eneration. A language model only knows what it saw during
training. Before it answers, we first *retrieve* the relevant paragraphs from our own course
material and hand them to the model, so its answer is grounded in the curriculum. **This module
does the retrieval half.** Member 1's Mistral does the generation half.

Key words:
* **Chunk** - a small piece of the curriculum (one or two paragraphs, or one code example).
* **Embedding** - a list of numbers (384 for the default model) capturing a text's meaning.
  Similar meaning = similar numbers.
* **Vector database (Qdrant)** - stores the embeddings plus the chunk text/metadata and quickly
  finds the closest ones to a question. We use its *local* mode: just a folder, no server/account.
* **Cosine similarity ("score")** - how close two embeddings are; higher = more similar.

## 3. Folder structure

```
member2_rag/
  data/raw/pps/        <- PUT YOUR PPS PDFs HERE
  data/processed/      <- chunks.jsonl is written here (readable dump of all chunks)
  src/
    config.py          settings in one place (+ Python-version check)
    document_loader.py read PDF/TXT/MD files -> page dictionaries
    preprocessing.py   clean text safely (C code preserved), heading detection
    chunking.py        topic-aware chunks with metadata
    embeddings.py      sentence-transformer wrapper (loads once, caches queries)
    vector_store.py    local persistent Qdrant
    retriever.py       question -> top-k results with scores
    rag_interface.py   RAGContext hand-off (TEMPORARY contract, see section 11)
  scripts/
    ingest.py          build/refresh the knowledge base (one command)
    query.py           ask a question from the command line
    preview_documents.py  look at loaded + cleaned text (no database)
  evaluation/
    test_queries.json  TEMPLATE of queries (expected_* must be filled from real curriculum)
    evaluate_retrieval.py  Hit@K / Recall@K / MRR report
  tests/               pytest tests (fake data only, no internet)
  vector_db/           the Qdrant database (created by ingest.py, not committed)
```

## 4. Installation

Run in the VS Code terminal (Ctrl + `), inside the `member2_rag` folder:

```
python --version
pip install -r requirements.txt
```
`python --version` must show 3.11.x (team standard: 3.11.0). Do not change your Python version.
The first time the embedding model is used it is downloaded once (~90 MB, needs internet) and
then cached for offline use.

## 5. Where to put the PPS PDFs

Copy your real curriculum files into **`data/raw/pps/`**. Supported: `.pdf`, `.txt`, `.md`
(text-based PDFs only; scanned/image-only PDFs are skipped with a message).

Naming helps the module detect the **module** automatically:
`module_1_introduction.pdf`, `Module 4 - Pointers.pdf`, or a folder `Module 3/notes.pdf`
all give "Module 1", "Module 4", "Module 3". Otherwise the module is "Unknown" (never guessed).

The **topic** is detected from headings in the text (e.g. `4.2 Pointer arithmetic`,
`ARRAYS AND STRINGS`). If detection is poor on your files, create
`data/raw/pps/curriculum_map.json` to set names yourself:

```json
{
  "module_4_pointers.pdf": {"module": "Module 4", "topic": "Pointers"}
}
```
(A topic given here is used for the whole file and overrides heading detection.)

Nothing in this repository is real curriculum content. Test files use obviously fake text.

## 6. Build the vector database

```
python scripts/ingest.py
```
Reads the files, cleans, chunks, embeds and stores everything in `vector_db/`, and writes a
readable `data/processed/chunks.jsonl` so you can inspect exactly what was indexed.
Options: `--data-dir`, `--collection`, `--chunk-size`, `--chunk-overlap`, `--model`, `--rebuild`.

Use `--rebuild` after deleting/renaming files, changing chunk settings or changing the model,
so no stale chunks remain. Only one program can open the Qdrant folder at a time.

**Chunk size/overlap defaults** (in `src/config.py`): 900 characters with 150 overlap. The default
embedding model (`all-MiniLM-L6-v2`) reads about 256 tokens (~1000 characters) and ignores the
rest, so 900 keeps each chunk fully "visible" while holding about one idea. 150 (~15%) overlap
repeats the end of one chunk at the start of the next so ideas on a boundary are not lost.
C code is never overlapped and kept in one piece when it fits (up to 2x the chunk size).

## 7. Run retrieval

```
python scripts/query.py "Explain pointers in C" --top-k 5
```

## 8. Run the evaluation

1. Ingest the real PPS files.
2. Open `data/processed/chunks.jsonl`, find which topic/source/module truly covers each query,
   and fill `expected_topics` / `expected_sources` / `expected_modules` in
   `evaluation/test_queries.json` (queries with all three empty are skipped).
3. Run:
```
python evaluation/evaluate_retrieval.py --top-k 5
```
Reports **Hit@K**, **Recall@K** and **MRR**. These are *retrieval* metrics, not LLM accuracy.
A result counts as relevant if it matches ANY expected topic (case-insensitive substring),
source file, or module.

## 9. Run the tests

```
python -m pytest -v
```
No internet or model download is needed (a fake embedder is used). One test checks the real
model's 384 dimensions and runs only if the model is already cached; otherwise it is skipped.

## 10. Example query and output

The values below show the **format** only (placeholders, not real curriculum):

```
Query: Explain pointers in C

1. score=0.912 | <file>.pdf (page <n>) | Module <n> | <detected topic>
   <first 300 characters of the chunk>

2. score=0.874 | <file>.pdf (page <n>) | Module <n> | <detected topic>
   ...
```

## 11. How Member 1 will consume RAGContext

```python
from src.rag_interface import PPSCurriculumRAG

rag = PPSCurriculumRAG.from_defaults()              # opens the existing vector_db
context = rag.retrieve(query="Explain pointers in C", top_k=5)
for doc in context.documents:
    print(doc.source, doc.page, doc.module, doc.topic, doc.score, doc.text)

curriculum_block = rag.format_for_prompt(context)   # ready-to-paste text with source labels
rag.close()                                         # release the database folder
```
Put `curriculum_block` into the Mistral prompt (e.g. "Use ONLY this PPS material: ...").

**IMPORTANT - the contract is TEMPORARY.** `RAGDocument`, `RAGContext` and `RAGInterface` in
`src/rag_interface.py` are placeholders because Member 1's real definitions have not been seen
yet. When they arrive, replace the block marked `TEMPORARY CONTRACT` and update the single
function `to_rag_document()` (and `format_for_prompt()`). Nothing else changes.

Notes for integration: keep one `PPSCurriculumRAG` open per process (Qdrant local mode allows one
opener at a time); the package is named `src`, so rename it or add the package path if it clashes
with another top-level `src` in the combined repo.

## Known limitations / to tune on real files

* Code-vs-prose and heading detection are heuristics; check `chunks.jsonl` on the real PDFs.
* Scanned PDFs need OCR (not included). PDF text extraction may lose code indentation.
* A chunk never spans two pages, so a paragraph continuing across a page break becomes two chunks.
* A lone number on its own line is treated as a page number and removed.
