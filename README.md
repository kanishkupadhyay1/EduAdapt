# EduAdapt: Adaptive Learning Platform

EduAdapt is an intelligent, adaptive learning platform for the **Programming for Problem Solving (PPS)** C programming curriculum.

This branch integrates **Member 1's Generative AI Module** with **Member 2's PPS Curriculum Retrieval-Augmented Generation (RAG) Module**.

---

## 📌 Architectural Scope & Module Ownership

- **Non-Agentic Deterministic Architecture**: EduAdapt uses direct, deterministic prompting and retrieval pipelines. It does **not** employ autonomous multi-agent loops or agentic frameworks.
- **Course Focus**: Scoped strictly to the **Programming for Problem Solving (PPS)** C curriculum.
- **Module Ownership**:
  - **Member 1 (GenAI & Teaching Personalization)**:
    - LLM Inference abstraction & clients (Ollama + Mistral 7B, mock fallback)
    - Prompt template management & student-aware prompt rendering
    - Pedagogical content generation & misconception-aware instruction
    - Automated feedback & hints on C code submissions
    - Dynamic roadmap planner
    - PPS teaching benchmark (20 questions) & automated evaluation harness (C reference safety checks)
  - **Member 2 (PPS Curriculum RAG Module)**:
    - Multi-format curriculum document loader (`.pdf`, `.txt`, `.md`)
    - Ligature normalization and C-code-preserving preprocessing
    - Semantic chunker with C code block integrity
    - Dense vector embeddings (`sentence-transformers/all-MiniLM-L6-v2`)
    - Local persistent vector storage (`Qdrant`)
    - Offline semantic retrieval engine & prompt context adapter
    - Retrieval evaluation (Hit@K, Recall@K, MRR)
  - **Member 3 (Student Modeling & Learning Twin)**:
    - Knowledge tracing, mastery estimation, student twin state persistence
  - **Member 4 (Accessibility)**:
    - Modality adaptation, audio narration, and assistive adapters

---

## 📂 Project Directory Structure

```text
EduAdapt/
├── .env.example                     # Environment configuration template
├── .gitignore                        # Git exclusion rules
├── README.md                         # Project documentation
├── requirements.txt                  # Unified project dependencies
├── data/
│   ├── benchmark/                    # PPS GenAI benchmark & rubric
│   │   ├── pps_benchmark_20.json     # 20 curated PPS evaluation problems
│   │   └── manual_review_rubric.md   # Pedagogical manual review rubric
│   ├── mock/                         # Mock payloads for unit tests
│   │   ├── sample_problem.json
│   │   ├── sample_rag_context.json
│   │   └── sample_student.json
│   ├── raw/pps/                      # Raw PPS curriculum documents (.pdf/.txt/.md)
│   └── processed/                    # Processed curriculum chunks (chunks.jsonl)
├── evaluation/                       # Retrieval evaluation harness
│   ├── evaluate_retrieval.py         # Hit@K / Recall@K / MRR metrics
│   └── test_queries.json             # Retrieval evaluation query templates
├── scripts/
│   ├── run_pps_evaluation.py         # GenAI automated benchmark test runner
│   ├── run_real_mistral_eval.py      # Live Mistral 7B baseline evaluation runner
│   └── rag/                          # RAG pipeline operations
│       ├── ingest.py                 # Index PPS curriculum into Qdrant
│       ├── preview_documents.py      # Dry-run text extraction & cleaning
│       └── query.py                  # CLI query tool for retrieval
├── src/
│   └── eduadapt/                     # Core Python application package
│       ├── config.py                 # Core application settings
│       ├── main.py                   # Service factory & module wiring
│       ├── inference/                # LLM client abstractions (Ollama, Mock)
│       ├── prompts/                  # Prompt templates & manager
│       ├── teaching/                 # Personalized teaching generation
│       ├── feedback/                 # Code feedback evaluator
│       ├── roadmap/                  # Learning roadmap generator
│       ├── evaluation/               # C execution & automated evaluation runner
│       ├── interfaces/               # Canonical team contracts
│       │   ├── rag.py                # Canonical RAGInterface, RAGDocument, RAGContext
│       │   ├── student_model.py      # Student profile contract
│       │   └── accessibility.py      # Accessibility contract
│       └── rag/                      # Member 2 PPS Curriculum RAG
│           ├── config.py             # RAG-specific parameters
│           ├── document_loader.py    # Multi-format document parser
│           ├── preprocessing.py      # Text cleaner & code detector
│           ├── chunking.py           # Topic & code-aware chunker
│           ├── embeddings.py         # Sentence-Transformers embedder
│           ├── vector_store.py       # Local embedded Qdrant store
│           ├── retriever.py          # Semantic similarity search
│           └── rag_interface.py      # PPSCurriculumRAG adapter
├── tests/
│   ├── helpers.py                    # Test helpers (HashingEmbedder, mock PDF)
│   ├── test_smoke.py                 # GenAI core smoke tests
│   ├── test_ollama.py                # Ollama client & live inference tests
│   ├── test_evaluation.py            # Evaluation & C executor tests
│   ├── test_loading_and_preprocessing.py # RAG document loader & text cleaning tests
│   └── test_retrieval.py             # RAG chunking, store, and retrieval tests
└── vector_db/                        # Local Qdrant persistent storage (.gitignored)
```

---

## ⚙️ Environment Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Key settings:
   - `LLM_PROVIDER`: `mock` (default for CI/tests) or `ollama` (for live inference)
   - `LLM_MODEL_NAME`: `mistral:7b-instruct` (or `mock-pps-model`)
   - `APP_ENV`: `development` | `testing` | `production`

---

## 🚀 Usage

### 1. Run Complete Test Suite
```bash
python -m pytest tests/ -v
```

### 2. Ingest PPS Curriculum (When PDFs are added)
```bash
python scripts/rag/ingest.py
```

### 3. Query the Curriculum Knowledge Base
```bash
python scripts/rag/query.py "Explain pointers in C" --top-k 5
```

### 4. Run the Teaching Generator Application
```bash
python -m eduadapt.main
```
