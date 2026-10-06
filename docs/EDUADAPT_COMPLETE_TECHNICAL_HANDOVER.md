# EduAdapt: Complete Technical Handover & System Architecture Guide

> **Document Type**: Technical Handover, Architectural Reference, and Evaluation Audit  
> **Target Audience**: EduAdapt Engineering Team (Members 1, 2, 3, 4) & Academic Evaluators  
> **Course Domain**: Programming for Problem Solving (PPS) — C Programming  
> **Repository Branch**: `feature/member1-genai-review2` (integrated with `origin/main`)  
> **Verification Status**: Verified against live repository codebase, unit test suite (103 passing tests), live FastAPI backend, React 19 frontend, and benchmark artifacts  
> **Strict Architectural Constraint**: **SINGLE, NON-AGENTIC GENERATIVE AI ARCHITECTURE**. No autonomous agents, agent loops, multi-agent frameworks (e.g., CrewAI, AutoGen, LangGraph), or tool-calling autonomous agents exist in this repository.

---

## Executive Summary

**EduAdapt** is an intelligent, deterministic adaptive learning platform developed for the undergraduate first-year engineering course **Programming for Problem Solving (PPS)**, focusing on foundational C programming and problem solving. The platform delivers personalized pedagogical explanations, targeted code examples, post-learning formative quiz assessments, automated feedback, and dynamic milestone learning roadmaps adapted to each student's predicted mastery level, learning pace, and common misconceptions.

### Core Architectural Principle
EduAdapt adheres to a strict **deterministic, non-agentic pipeline**. Rather than delegating control flow to an autonomous LLM agent that decides which tools to call in iterative loops, EduAdapt uses a **single central Large Language Model (Mistral 7B via local Ollama)** embedded within a hardcoded, deterministic application workflow orchestrator (`AdaptiveLearningService`). Every component—from student twin feature extraction and vector retrieval to prompt rendering, code safety verification, HTTP API delivery, and accessibility formatting—is executed in a fixed sequence.

### Ownership Matrix
- **Member 1 (GenAI & Content Generation)**: Local Ollama Mistral 7B inference client, deterministic prompt engineering framework, pedagogical explanation generator, code feedback evaluator, dynamic roadmap planner, 20-question PPS benchmark runner, end-to-end service orchestration (`AdaptiveLearningService`), and FastAPI backend adapter (`src/eduadapt/api.py`).
- **Member 2 (NLP / RAG / Curriculum Intelligence)**: Multi-format PPS document ingestion (`.pptx`, `.pdf`, `.txt`, `.md`), ligature and code-preserving preprocessing, topic-aware chunking, dense vector embeddings (`sentence-transformers/all-MiniLM-L6-v2`), local persistent vector storage (`Qdrant`), and retrieval evaluation engine.
- **Member 3 (Assessment / Student Intelligence / Learning Twin)**: Tabular assessment data analysis, feature engineering (accuracy, time, attempts, learning pace), student profile modeling, and baseline XGBoost mastery classification.
- **Member 4 (Speech / Accessibility / Response Verification)**: Multi-signal response grounding and safety verifier (`ResponseVerifier`), accessible structured content formatter (`AccessibilityFormatter`), optional Whisper voice input, Windows/pyttsx3 voice output hooks, and React 19 academic web dashboard (`frontend/`).

### Current Implementation & Verification Status
- **Test Suite**: **103 passed, 1 warning** across 7 test modules executing in ~24.8 seconds on Python 3.11.0.
- **RAG Knowledge Base**: **5 PPS curriculum PPTX lecture slide decks** (SRM PPS Units 1 through 5, comprising 666 total slides) ingested, cleaned, and chunked into **966 vector embeddings** stored in a local Qdrant collection.
- **Retrieval Performance**: On 10 representative curriculum benchmark queries:
  - **Hit@1 = 1.00 (100%)**, **Mean Recall@1 = 0.72 (72.0%)**, **MRR = 1.00**
  - **Hit@3 = 1.00 (100%)**, **Mean Recall@3 = 0.97 (97.0%)**, **MRR = 1.00**
  - **Hit@5 = 1.00 (100%)**, **Mean Recall@5 = 0.97 (97.0%)**, **MRR = 1.00**
- **GenAI PPS Benchmark**: Tested across 20 curated PPS questions covering 7 curriculum topics using `mistral:7b`:
  - 20/20 successful inferences (0 timeouts, 0 connection drops).
  - Average latency: **26.93 seconds** per response.
  - Automated concept coverage indicator: **84.9%** (automated keyword match indicator; *not* model accuracy).
  - Code safety enforcement: **100% of untrusted LLM code marked `NOT_EXECUTED_UNTRUSTED`** (zero untrusted host execution).
  - Trusted reference execution: **20/20 compiler runs succeeded** using host GCC (`C:\MinGW\bin\gcc.exe`).
  - While-loop termination regression check: **0 regressions detected**.
- **Student Learning Twin**: Baseline XGBoost classifier trained on 24 demonstration assessment records across 6 students. Evaluation accuracy is **33.3%** on a 3-sample test split, reflecting an initial small demo dataset that requires expansion with real classroom cohort data.
- **HTTP API Layer**: **[IMPLEMENTED]** via FastAPI in `src/eduadapt/api.py` exposing `/health`, `/api/student/{student_id}`, and `/api/session/generate`.
- **Frontend Layer**: **[IMPLEMENTED]** via React 19 + Vite in `frontend/`, featuring an academic two-column dashboard rendering all 10 response contract sections, copyable C code blocks, and Vercel-ready build output in `frontend/dist/`.

---

## 1. Full Repository Audit

### 1.1 Repository Tree Structure

```text
EduAdapt/
├── .env                                # Local environment settings (active)
├── .env.example                        # Environment template with defaults
├── .gitignore                          # Git exclusions (vector_db/, caches, etc.)
├── pytest.ini                         # Pytest configuration (testpaths = tests)
├── README.md                           # Top-level project overview & quickstart
├── requirements.txt                   # Consolidated Python dependencies
├── data/
│   ├── assessment_data.csv             # 24 rows of mock assessment data for 6 students (S001-S006)
│   ├── evaluation_results_mistral7b.json # Full benchmark output of 20 questions on Mistral 7B
│   ├── real_model_responses.json       # Inferences across 4 pedagogical PPS scenarios
│   ├── benchmark/
│   │   ├── manual_review_rubric.md     # 5-dimension pedagogical grading rubric for human reviewers
│   │   └── pps_benchmark_20.json       # Curated 20 PPS problems with reference code and criteria
│   ├── mock/
│   │   ├── sample_problem.json         # Mock problem payload for tests
│   │   ├── sample_rag_context.json     # Mock RAG context for unit tests
│   │   └── sample_student.json         # Mock student profile payload
│   ├── processed/
│   │   └── chunks.jsonl                # 966 preprocessed curriculum chunks with slide metadata
│   └── raw/pps/
│       ├── Unit 1 PPS.pptx             # PPS Unit 1: Problem solving, flowcharts, data types (132 slides)
│       ├── PPS Unit 2.pptx             # PPS Unit 2: Control statements, arrays, pointers (206 slides)
│       ├── PPS Unit 3.pptx             # PPS Unit 3: Strings, functions, parameter passing (105 slides)
│       ├── UNIT 4-PPS.pptx             # PPS Unit 4: Python fundamentals, data structures (163 slides)
│       └── pps u5.pptx                 # PPS Unit 5: NumPy, Pandas, DataFrames (60 slides)
├── docs/
│   └── EDUADAPT_COMPLETE_TECHNICAL_HANDOVER.md # This comprehensive technical handover guide
├── evaluation/
│   ├── evaluate_retrieval.py           # Evaluates Hit@K, Recall@K, and MRR for RAG
│   └── test_queries.json               # 10 benchmark queries with expected topics, files, and units
├── frontend/                           # React 19 + Vite Academic Web Dashboard
│   ├── .env                            # Frontend environment configuration (VITE_API_BASE_URL)
│   ├── .env.example                    # Frontend environment template
│   ├── .gitignore                      # Node & build exclusions
│   ├── .oxlintrc.json                  # Oxlint configuration
│   ├── index.html                      # HTML root template
│   ├── package.json                    # Frontend dependencies (React 19, Vite, Oxlint)
│   ├── package-lock.json               # Lockfile
│   ├── README.md                       # Frontend architecture and setup guide
│   ├── vite.config.js                  # Vite bundler configuration
│   ├── dist/                           # Production static build assets (Vercel ready)
│   └── src/
│       ├── App.jsx                     # Root React application component
│       ├── index.css                   # Minimalist academic CSS styling
│       ├── main.jsx                    # Vite application entrypoint
│       ├── api/
│       │   └── learningApi.js          # API client for EduAdapt FastAPI backend
│       ├── assets/                     # Static SVGs and hero assets
│       ├── components/
│       │   ├── AccessibilityPanel.jsx  # Formatted screen-reader summary & transcript
│       │   ├── AssessmentPanel.jsx     # Post-learning quiz question & options viewer
│       │   ├── CurriculumContext.jsx   # Retrieved PPS RAG slides & relevance scores
│       │   ├── FeedbackPanel.jsx       # Formative code feedback & pedagogical hints
│       │   ├── Header.jsx              # Academic title and active student badge
│       │   ├── LearningControls.jsx    # Topic picker & Top-K RAG chunk slider
│       │   ├── LearningState.jsx       # Student Learning Twin updated state display
│       │   ├── Roadmap.jsx             # Milestone-based learning roadmap progression
│       │   ├── StudentProfile.jsx      # Active student twin metrics (mastery, pace, accuracy)
│       │   ├── TeachingContent.jsx     # Generated teaching explanation & copyable C code
│       │   └── VerificationPanel.jsx   # Grounding ratio, term overlap & safety badges
│       ├── pages/
│       │   └── Dashboard.jsx           # Two-column responsive academic layout
│       └── styles/
│           └── index.css               # Component stylesheet
├── member3/                            # Member 3: Student Modeling & Learning Twin
│   ├── __init__.py
│   ├── assessment.py                   # Calculates student performance statistics from CSV
│   ├── evaluate.py                     # Evaluates saved XGBoost model on train/test split
│   ├── features.py                     # Feature engineering (accuracy, pace, attempts, time)
│   ├── learning_twin.py                # Rule-based difficulty and pace classification
│   ├── student_state.py                # Extracts live student state combining features & XGBoost
│   ├── train_xgboost.py                # Trains XGBClassifier and exports model + label encoder
│   └── update_state.py                 # Simulates student state update after assessment
├── models/
│   └── xgboost_model.pkl               # Serialized model, LabelEncoder, and feature columns
├── scripts/
│   ├── run_full_demo.py                # End-to-end CLI demonstration of the complete 10-step pipeline
│   ├── run_integrated_demo.py          # Intermediate CLI demo combining Twin, RAG, and GenAI
│   ├── run_pps_evaluation.py           # Automated evaluation runner for 20 benchmark questions
│   ├── run_real_mistral_eval.py        # Real Mistral 7B inference runner for 4 scenarios
│   └── rag/
│       ├── ingest.py                   # Ingestion CLI: loads raw files, chunks, embeds into Qdrant
│       ├── preview_documents.py        # CLI dry-run preview of document loading and cleaning
│       └── query.py                    # Standalone CLI semantic query search tool
├── src/
│   └── eduadapt/
│       ├── __init__.py
│       ├── api.py                      # [IMPLEMENTED] FastAPI HTTP API adapter
│       ├── config.py                   # Pydantic Settings (LLM provider, URLs, timeouts)
│       ├── main.py                     # Module factory and entrypoint
│       ├── accessibility/
│       │   ├── __init__.py
│       │   ├── formatter.py            # AccessibilityFormatter: transforms session for screen readers
│       │   ├── speech_input.py         # transcribe_audio: optional Whisper STT hook
│       │   └── speech_output.py        # speak_text: Windows PowerShell / pyttsx3 TTS hook
│       ├── adapters/
│       │   ├── __init__.py
│       │   └── student_twin_adapter.py # LearningTwinAdapter: adapts Member 3 to canonical StudentProfile
│       ├── evaluation/
│       │   ├── __init__.py
│       │   ├── benchmark.py            # Benchmark loader and validator
│       │   ├── c_executor.py           # C compiler discovery, trusted execution, untrusted code isolation
│       │   ├── models.py               # Pydantic schemas for evaluation and execution
│       │   ├── regression.py           # Targeted while-loop termination error detector
│       │   └── runner.py               # Automated evaluation loop for benchmark questions
│       ├── feedback/
│       │   ├── __init__.py
│       │   └── evaluator.py            # FeedbackGenerator: generates hints and diagnostic feedback
│       ├── inference/
│       │   ├── __init__.py
│       │   ├── base.py                 # BaseLLMClient interface, GenerationResult, MockLLMClient
│       │   └── ollama.py               # OllamaLLMClient: calls Ollama HTTP endpoint (/api/generate)
│       ├── interfaces/
│       │   ├── __init__.py
│       │   ├── accessibility.py        # Abstract contract for accessibility services
│       │   ├── rag.py                  # Canonical RAGInterface, RAGDocument, RAGContext
│       │   └── student_model.py        # Canonical StudentModelInterface and StudentProfile
│       ├── prompts/
│       │   ├── __init__.py
│       │   └── templates.py            # PromptManager and 4 parameterized PromptTemplates
│       ├── rag/
│       │   ├── __init__.py
│       │   ├── chunking.py             # Topic-aware and code-preserving chunker
│       │   ├── config.py               # RAG-specific parameters (chunk size, embedder, collections)
│       │   ├── document_loader.py      # Multi-format document parser (.pptx, .pdf, .txt, .md)
│       │   ├── embeddings.py           # SentenceTransformers embedder wrapper with caching
│       │   ├── preprocessing.py        # Text cleaner, repeated line stripper, code detector
│       │   ├── rag_interface.py        # PPSCurriculumRAG: implements canonical RAGInterface
│       │   ├── retriever.py            # Semantic retrieval against Qdrant vector store
│       │   └── vector_store.py         # Qdrant client wrapper for local embedded disk storage
│       ├── roadmap/
│       │   ├── __init__.py
│       │   └── planner.py              # RoadmapGenerator: milestone roadmap creation
│       ├── services/
│       │   ├── __init__.py
│       │   └── adaptive_learning.py    # AdaptiveLearningService: unifies complete pipeline
│       ├── teaching/
│       │   ├── __init__.py
│       │   └── generator.py            # PersonalizedContentGenerator: renders prompts and invokes LLM
│       └── verification/
│           ├── __init__.py
│           └── response_verifier.py    # ResponseVerifier: checks grounding, safety, code detection
├── tests/
│   ├── __init__.py
│   ├── helpers.py                      # Test mocks: HashingEmbedder, dummy PDF generator
│   ├── test_adaptive_learning_service.py # 6 tests: full service session and edge cases
│   ├── test_evaluation.py              # 12 tests: C executor, compiler discovery, regression
│   ├── test_loading_and_preprocessing.py # 30 tests: document loaders, PPTX parser, cleaning
│   ├── test_ollama.py                  # 6 tests: Ollama client configuration, error handling
│   ├── test_retrieval.py               # 38 tests: chunking, embedding, Qdrant store, retrieval
│   ├── test_smoke.py                   # 7 tests: prompt rendering, mock LLM, teaching generator
│   └── test_student_twin_adapter.py    # 4 tests: profile mapping, unknown students, defaults
└── vector_db/                          # Local persistent Qdrant database (966 vectors)
    ├── .lock
    ├── meta.json
    └── collection/
        └── pps_curriculum/
            └── storage.sqlite
```

### 1.2 Repository Statistics & Inventory
- **Total Python Files**: 43 source, test, and script files.
- **Total Frontend Files**: 15 React/Vite JSX, JS, CSS, and configuration files.
- **Total Processed Chunks**: 966 JSON lines (`data/processed/chunks.jsonl`).
- **Total Ingested Curriculum Slides**: 666 slides across 5 PPTX decks.
- **Total Vectors in Local Qdrant**: 966 points (`vector_db/collection/pps_curriculum/`).
- **Benchmark Evaluation Cases**: 20 curated PPS questions (`data/benchmark/pps_benchmark_20.json`).
- **Automated Tests**: 103 unit and integration tests passing in Pytest.
- **HTTP REST API**: **[IMPLEMENTED]** (`src/eduadapt/api.py` via FastAPI).
- **Web Frontend**: **[IMPLEMENTED]** (`frontend/` via React 19 + Vite).

---

## 2. Project Architecture

### 2.1 Non-Agentic Architectural Paradigm

EduAdapt is strictly engineered as a **Deterministic Generative AI System**, explicitly rejecting agentic architectures:
- **No Agentic Loops**: The system does not loop, reflect, re-act, or recursively plan.
- **No Autonomous Tool Calling**: The LLM is never given tools, function-calling schemas, or execution privileges.
- **No Agent Frameworks**: There are zero dependencies on LangChain agents, CrewAI, AutoGen, or LangGraph.
- **Fixed Pipeline**: All control flow is determined by standard Python procedural logic inside `AdaptiveLearningService.run_learning_session()`. The LLM serves strictly as a **text generator** conditioned on curriculum context and student profiles.

### 2.2 System Architecture Diagram

```text
+---------------------------------------------------------------------------------------------------+
|                                       USER / CLIENT LAYER                                         |
|  [IMPLEMENTED] React 19 Academic Web Dashboard (frontend/src/pages/Dashboard.jsx)                 |
|  [IMPLEMENTED] Python CLI Scripts (scripts/run_full_demo.py, scripts/run_pps_evaluation.py)       |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v  HTTP POST /api/session/generate
+---------------------------------------------------------------------------------------------------+
|                                  HTTP REST API LAYER (FastAPI)                                    |
|                                       src/eduadapt/api.py                                         |
|                 Endpoints: /health, /api/student/{id}, /api/session/generate                      |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v  run_learning_session()
+---------------------------------------------------------------------------------------------------+
|               ADAPTIVE LEARNING SERVICE ORCHESTRATOR (Deterministic Controller)                  |
|                           src/eduadapt/services/adaptive_learning.py                             |
+---------------------------------------------------------------------------------------------------+
         |                                |                                   |
         v (Step 1)                       v (Step 2)                          v (Step 3)
+-----------------------+     +--------------------------+     +------------------------------------+
|  STUDENT LEARNING     |     |   PPS CURRICULUM RAG     |     |       PROMPT ENGINEERING           |
|  TWIN (Member 3)      |     |       (Member 2)         |     |           (Member 1)               |
|                       |     |                          |     |                                    |
| assessment_data.csv   |     | Raw PPTX (5 Units, 666s) |     | PromptManager                      |
|        ↓              |     |          ↓               |     | templates.py                       |
| create_features()     |     | Preprocessing & Chunker  |     |                                    |
|        ↓              |     |          ↓               |     | Populates:                         |
| XGBoost Classifier    |     | all-MiniLM-L6-v2 Embedder|     |   - Topic                          |
|        ↓              |     |          ↓               |     |   - Calibrated Mastery Level       |
| Raw Student State     |     | Local Qdrant Vector Store|     |   - Performance History            |
|        ↓              |     |          ↓               |     |   - Identified Misconceptions      |
| LearningTwinAdapter   |     | Top-K Semantic Retriever |     |   - Formatted RAG Context          |
|        ↓              |     |          ↓               |     |   - Preferred Output Format        |
| StudentProfile        |     | RAGContext (3 Chunks)    |     |                                    |
+-----------------------+     +--------------------------+     +------------------------------------+
         |                                |                                   |
         +--------------------------------+-----------------------------------+
                                          |
                                          v (Step 4)
+---------------------------------------------------------------------------------------------------+
|                               LOCAL LLM INFERENCE (Member 1)                                      |
|                  Ollama Service (http://localhost:11434/api/generate)                             |
|                               Model: mistral:7b (Local GGUF)                                      |
|                               Fallback: MockLLMClient                                             |
+---------------------------------------------------------------------------------------------------+
                                          |
                                          v (Generated Explanation Text)
         +--------------------------------+-----------------------------------+
         |                                |                                   |
         v (Step 5)                       v (Step 6)                          v (Step 7)
+-----------------------+     +--------------------------+     +------------------------------------+
| RESPONSE VERIFICATION |     |  POST-LEARNING QUIZ &    |     |       ROADMAP & FEEDBACK           |
|      & SAFETY         |     |   LEARNING TWIN UPDATE   |     |           (Member 1)               |
|      (Member 4)       |     |        (Member 3)        |     |                                    |
|                       |     |                          |     | FeedbackGenerator:                 |
| ResponseVerifier:     |     | Curated PPS Quiz Bank:   |     |   Generates diagnostic hints       |
| - Non-empty check     |     |   Pointers, Loops, etc.  |     |   for student C code               |
| - Lexical overlap vs  |     |          ↓               |     |                                    |
|   retrieved slides    |     | Simulated State Update:  |     | RoadmapGenerator:                  |
| - C code extraction   |     |   Concatenates quiz data |     |   Constructs milestone learning    |
| - Enforces Safety:    |     |   Recomputes features    |     |   stages towards target mastery    |
|   NOT_EXECUTED_       |     |   Re-runs Twin heuristics|     |                                    |
|   UNTRUSTED           |     |   Produces updated state |     |                                    |
| - While-loop check    |     |                          |     |                                    |
+-----------------------+     +--------------------------+     +------------------------------------+
         |                                |                                   |
         +--------------------------------+-----------------------------------+
                                          |
                                          v (Step 8)
+---------------------------------------------------------------------------------------------------+
|                                ACCESSIBILITY FORMATTING (Member 4)                                |
|                              src/eduadapt/accessibility/formatter.py                              |
|                                                                                                   |
|  - Generates plain screen-reader summary text                                                     |
|  - Organizes structured sections (Topic, Level, Explanation, Code, Quiz, Sources)                 |
|  - [OPTIONAL] Audio Input: Whisper STT (openai-whisper)                                           |
|  - [OPTIONAL] Audio Output: Windows PowerShell Speech Synthesis / pyttsx3                         |
+---------------------------------------------------------------------------------------------------+
                                          |
                                          v
+---------------------------------------------------------------------------------------------------+
|                              UNIFIED SESSION RESPONSE CONTRACT                                    |
|  { student, profile, curriculum, teaching, assessment, feedback, learning_state, roadmap, ... }   |
+---------------------------------------------------------------------------------------------------+
```

### 2.3 End-to-End Data Flow
1. **Invocation**: The user selects a topic on the React frontend or CLI, sending `student_id` (e.g., `"S001"`) and target `topic` (e.g., `"Pointers"`).
2. **State Retrieval**: `LearningTwinAdapter` retrieves `S001`'s historical records from `data/assessment_data.csv`, computes statistical aggregates via `member3.features`, predicts mastery category via `models/xgboost_model.pkl`, and maps it into a canonical `StudentProfile`.
3. **Curriculum Retrieval**: `PPSCurriculumRAG` executes dense semantic similarity search against local Qdrant vectors using `all-MiniLM-L6-v2`, retrieving the top-3 most relevant slide chunks.
4. **Prompt Rendering**: `PersonalizedContentGenerator` calibrates cognitive depth (Beginner, Intermediate, Advanced) based on mastery score, formats the RAG slide excerpts, injects identified misconceptions, and compiles the final instruction string.
5. **LLM Inference**: The prompt is dispatched synchronously via HTTP POST to the local Ollama instance hosting `mistral:7b`.
6. **Post-Processing & Verification**: `ResponseVerifier` verifies that content was returned, calculates lexical overlap with the retrieved slides, extracts any C code blocks, strictly marks untrusted code as `NOT_EXECUTED_UNTRUSTED`, and runs regex regression detection.
7. **Assessment & Feedback**: The student is evaluated on a topic quiz question, diagnostic feedback is generated for practice code, and the Learning Twin simulates an updated state.
8. **Roadmap & Accessibility**: `RoadmapGenerator` crafts study milestones, and `AccessibilityFormatter` compiles the unified output dictionary for screen readers and UI consumers.
9. **Display**: The FastAPI backend returns JSON to the React frontend, rendering the two-column dashboard with copyable code snippets, badges, and transcripts.

---

## 3. Team Responsibilities & Ownership Division

| Dimension | Member 1 (GenAI / Content Generation) | Member 2 (NLP / RAG / Curriculum) | Member 3 (Assessment / Student Twin) | Member 4 (Speech / Verification / UI) |
|---|---|---|---|---|
| **Core Responsibility** | LLM inference, prompt engineering, personalized teaching, feedback, roadmap, service wiring, and FastAPI adapter | Curriculum ingestion, text cleaning, chunking, embeddings, Qdrant store, retrieval evaluation | Historical assessment analysis, feature engineering, XGBoost classifier, student state persistence | Grounding verification, host execution safety, screen-reader formatting, optional speech, and React UI |
| **Files Owned** | `src/eduadapt/inference/*`<br>`src/eduadapt/prompts/*`<br>`src/eduadapt/teaching/*`<br>`src/eduadapt/feedback/*`<br>`src/eduadapt/roadmap/*`<br>`src/eduadapt/services/*`<br>`src/eduadapt/adapters/*`<br>`src/eduadapt/api.py`<br>`scripts/run_full_demo.py` | `src/eduadapt/rag/*`<br>`scripts/rag/*`<br>`evaluation/evaluate_retrieval.py`<br>`evaluation/test_queries.json`<br>`data/raw/pps/*`<br>`data/processed/*`<br>`vector_db/*` | `member3/*`<br>`models/xgboost_model.pkl`<br>`data/assessment_data.csv` | `src/eduadapt/verification/*`<br>`src/eduadapt/accessibility/*`<br>`src/eduadapt/evaluation/c_executor.py`<br>`src/eduadapt/evaluation/regression.py`<br>`frontend/*` |
| **Technologies** | Python 3.11, Ollama, Requests, Pydantic, FastAPI, Uvicorn | `sentence-transformers`, `qdrant-client`, `python-pptx`, `pypdf`, regex | `scikit-learn`, `xgboost`, `joblib`, `pandas` | `MinGW/gcc`, PowerShell `System.Speech`, `whisper` (opt), React 19, Vite |
| **Models Used** | `mistral:7b` (via Ollama) | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) | `XGBClassifier` (gradient boosted trees) | Whisper `base` (optional STT) |
| **Inputs** | `StudentProfile`, `RAGContext`, topic string | Query string, raw `.pptx`/`.pdf`/`.txt`/`.md` files | Assessment CSV, `student_id` | LLM response text, retrieved RAG chunks, audio file |
| **Outputs** | Pedagogical text, C examples, feedback hints, milestone roadmap | `RAGContext`, `list[RAGDocument]`, Hit@K / Recall / MRR | `dict[str, Any]` student state, `xgboost_model.pkl` | `GroundingVerificationResult`, accessible formatted dict, React dashboard |
| **Integration Contract** | Implements core service & API; consumes Member 2 & 3 interfaces | Implements `RAGInterface` (`src/eduadapt/interfaces/rag.py`) | Adapted via `LearningTwinAdapter` into `StudentProfile` | Invoked directly by `AdaptiveLearningService`; UI calls `/api/session/generate` |
| **Current Status** | **[IMPLEMENTED] & [TESTED]** | **[IMPLEMENTED] & [TESTED]** | **[IMPLEMENTED] & [DEMO]** (tiny demo dataset) | **[IMPLEMENTED] & [TESTED]** |

---

## 4. Member 1 Complete Implementation: GenAI Core

Member 1 is responsible for the generative core of EduAdapt, managing all interactions with the LLM, prompt templates, personalized generation logic, automated feedback, dynamic roadmap planning, FastAPI exposure, and cross-module integration.

### 4.1 Detailed Module & Class Breakdown

#### 1. Configuration: `src/eduadapt/config.py`
- **Class `Settings(BaseSettings)`**: Loads configuration from `.env` or system environment.
  - Fields: `app_name`, `app_env`, `log_level`, `llm_provider`, `llm_model_name`, `llm_api_base`, `llm_temperature`, `llm_max_tokens`, `llm_timeout`, and external service URLs.
  - Validator: `validate_llm_provider()` strictly enforces that `llm_provider` must be either `"mock"` or `"ollama"`. Any unsupported provider raises a validation `ValueError`.

#### 2. LLM Abstraction: `src/eduadapt/inference/base.py`
- **Class `GenerationResult(BaseModel)`**: Encapsulates the output of any LLM invocation.
  - Fields: `content` (str), `model_name` (str), `metadata` (dict), `prompt_tokens` (Optional[int]), `completion_tokens` (Optional[int]).
- **Class `BaseLLMClient(ABC)`**: Abstract base class requiring implementation of:
  - `generate(prompt, system_instruction, temperature, max_tokens, **kwargs) -> GenerationResult`
- **Class `MockLLMClient(BaseLLMClient)`**: Deterministic mock provider used in continuous integration and unit testing. Returns `"[Mock LLM Output for prompt length N chars]"` without network overhead or GPU requirements.

#### 3. Live Ollama Client: `src/eduadapt/inference/ollama.py`
- **Exception Hierarchy**:
  - `OllamaError`: Base class for inference failures.
  - `OllamaConnectionError`: Raised when port 11434 is unreachable or refused.
  - `OllamaTimeoutError`: Raised when the inference exceeds `eff_timeout` (default 180s).
  - `OllamaResponseError`: Raised on non-200 HTTP status codes, malformed JSON, or Ollama error payloads.
- **Class `OllamaLLMClient(BaseLLMClient)`**:
  - Method `generate(...)`: Performs synchronous HTTP POST to `http://localhost:11434/api/generate` with JSON payload `{ "model": ..., "prompt": ..., "stream": False, "options": { "temperature": ..., "num_predict": ... } }`.
  - Captures `prompt_eval_count` and `eval_count` from Ollama's response JSON as token statistics.

#### 4. Prompt Template Management: `src/eduadapt/prompts/templates.py`
- **Class `PromptTemplate(BaseModel)`**: Container holding `name`, `template` (format string), and `description`. Exposes `render(**kwargs) -> str`.
- **Class `PromptManager`**: Registry managing 4 built-in parameterized templates:
  - `"teaching_explanation"`: Basic concept explanation.
  - `"personalized_teaching"`: Mastery-, history-, misconception-, and format-conditioned prompt.
  - `"feedback_generation"`: Step-by-step diagnostic feedback on C code.
  - `"roadmap_generation"`: Milestone study plan generation.

#### 5. Personalized Content Generator: `src/eduadapt/teaching/generator.py`
- **Class `PersonalizedContentGenerator`**:
  - Method `generate_for_student(topic, student_profile, preferred_response_format, performance_history, additional_context)`:
    - Extracts `mastery_score = student_profile.mastery_levels.get(topic, 0.0)`.
    - Dynamically calibrates cognitive tier:
      - Score $\ge 0.70$: Advanced (focus on nuances, memory layout, edge cases, efficiency).
      - $0.40 \le \text{Score} < 0.70$: Intermediate (reinforce core mechanics and syntax applications).
      - Score $< 0.40$: Beginner (foundational breakdown, simple analogies, guided walkthrough).
    - Retrieves top-3 curriculum chunks from `RAGInterface` if RAG is attached.
    - Assembles and renders the `"personalized_teaching"` prompt.
    - Invokes `llm_client.generate()`.

#### 6. Feedback & Roadmap Modules:
- **`src/eduadapt/feedback/evaluator.py` (`FeedbackGenerator`)**: Formulates pedagogical hints on student code without revealing complete answers.
- **`src/eduadapt/roadmap/planner.py` (`RoadmapGenerator`)**: Produces milestone study progressions tailored to the student's entry mastery.

#### 7. Service Orchestrator: `src/eduadapt/services/adaptive_learning.py`
- **Class `AdaptiveLearningService`**: The central coordinator connecting Members 1, 2, 3, and 4 into a deterministic, unified learning session returning a standardized 10-key contract.

#### 8. HTTP API Adapter: `src/eduadapt/api.py`
- **FastAPI Application**: Acts as a minimal HTTP gateway exposing `AdaptiveLearningService`.
  - Enables full CORS for local development and frontend integrations.
  - Endpoints:
    - `GET /health`: Healthcheck endpoint returning `{"status": "ok", "service": "EduAdapt"}`.
    - `GET /api/student/{student_id}`: Returns live student state from `member3.student_state`.
    - `POST /api/session/generate`: Accepts `{ student_id, topic, top_k }` and executes `run_learning_session()`.

---

## 5. Ollama + Mistral 7B Deep-Dive

### 5.1 Local Inference Rationale
EduAdapt uses **local Mistral 7B inference via Ollama** rather than external cloud APIs (e.g., OpenAI, Anthropic, Google Gemini):
1. **Academic Privacy & Offline Autonomy**: Student performance data, code submissions, and institutional curriculum materials remain entirely on the local workstation.
2. **Zero API Cost / No Rate Limits**: Removes token subscription fees, quota exhaustion risks, and credit card requirements.
3. **Reproducibility**: Guarantees consistent local model weights (`mistral:7b` based on Mistral-7B-Instruct-v0.2) across student evaluations.

### 5.2 Network & Request Architecture
- **Default Endpoint**: `http://localhost:11434/api/generate`
- **HTTP Method**: `POST`
- **Payload Schema**:
```json
{
  "model": "mistral:7b",
  "prompt": "<RENDERED_PROMPT_STRING>",
  "system": "You are an expert tutor for Programming for Problem Solving (PPS) in C.",
  "stream": false,
  "options": {
    "temperature": 0.7,
    "num_predict": 1024
  }
}
```

### 5.3 Response Handling & Token Tracking
Ollama returns a single JSON object containing generation metadata:
- `response`: The full generated text string.
- `prompt_eval_count`: Number of input tokens processed by Mistral's tokenizer.
- `eval_count`: Number of output tokens generated.
- `total_duration`: Nanoseconds spent on request execution.
- `load_duration`: Nanoseconds spent loading model weights into memory.

`OllamaLLMClient` maps these values directly into `GenerationResult`:
```python
GenerationResult(
    content=data.get("response", ""),
    model_name=data.get("model", self.model_name),
    metadata=metadata,
    prompt_tokens=data.get("prompt_eval_count"),
    completion_tokens=data.get("eval_count"),
)
```

### 5.4 Supported Providers
- **`"ollama"`**: Live local LLM inference against `http://localhost:11434`.
- **`"mock"`**: Instantaneous deterministic mock generator used for automated unit testing and rapid dry-runs.
- *Any other provider string (e.g., `"openai"`, `"anthropic"`) is actively rejected by Pydantic validators during application startup.*

---

## 6. Exact Prompt Engineering Strategy

The prompt engineering strategy in EduAdapt is entirely deterministic and template-driven. All templates are maintained in `src/eduadapt/prompts/templates.py`.

### 6.1 Template 1: `teaching_explanation`

#### Purpose
Used as a generic or fallback prompt for explaining a PPS concept when detailed student mastery records are absent.

#### Exact Template Text
```text
You are an expert tutor for Programming for Problem Solving (PPS).
Topic: {topic}
Student Learning Preference: {learning_preference}
Context: {context}

Explain the concept clearly with relevant C programming examples.
```

#### Variable Injection
- `{topic}`: The PPS concept name (e.g., `"Pointers"`).
- `{learning_preference}`: Requested presentation format (e.g., `"visual and code-focused"`).
- `{context}`: Background information (e.g., `"Introductory level"`).

---

### 6.2 Template 2: `personalized_teaching`

#### Purpose
The primary prompt for personalized instruction. Injects multidimensional student modeling signals (mastery score, cognitive tier, performance history, misconceptions) and retrieved curriculum slide chunks.

#### Exact Template Text
```text
You are an expert tutor for Programming for Problem Solving (PPS) in C.
Topic: {topic}
Student Mastery Level: {mastery_level}
Performance History: {performance_history}
Common Misconceptions to Address: {misconceptions}
Preferred Response Format: {response_format}
Additional Context: {context}

Instructions:
- Tailor cognitive depth and scaffolding to the student's mastery level and performance history.
- Explicitly detect and clarify the noted misconceptions without condescension.
- Present practical, syntactically correct C programming examples matching the requested response format.
```

#### Detailed Variable Breakdown

1. `{topic}`: Target C programming topic (e.g., `"Pointers"`, `"For Loops in C"`).
2. `{mastery_level}`: Calibrated string produced by `PersonalizedContentGenerator`:
   - If score $\ge 0.70$: `"Advanced (0.95) - focus on nuances, edge cases, memory layout, and idiomatic efficiency"`
   - If $0.40 \le \text{score} < 0.70$: `"Intermediate (0.55) - reinforce core mechanics and syntax applications"`
   - If score $< 0.40$: `"Beginner (0.25) - provide intuitive foundational breakdown, simple analogies, and guided walkthrough"`
3. `{performance_history}`: Pedagogical diagnostic narrative from the student twin (e.g., `"Pace: fast, Current curriculum topic: Pointers"` or benchmark history like `"Struggled on practice quiz 1 with iteration count"`).
4. `{misconceptions}`: Semicolon-delimited list of detected student misconceptions (e.g., `"Thinking loop update condition runs before the loop body executes; Off-by-one errors with <= versus < operators"`). If none: `"None identified"`.
5. `{response_format}`: Desired structural format (e.g., `"concise explanation with commented C code and step-by-step trace"`).
6. `{context}`: Formatted RAG curriculum excerpts compiled via `RAGContext.format_for_prompt()`:
   ```text
   Curriculum Context:
   [1] (Source: Unit 1 PPS.pptx, Page: 50, Module: Unit 1, Topic: Structured Programming):
   <slide text content...>
   
   [2] (Source: PPS Unit 2.pptx, Page: 156, Module: Unit 2, Topic: Definition):
   <slide text content...>
   ```

---

### 6.3 Template 3: `feedback_generation`

#### Purpose
Evaluates student-submitted C code against a problem description and produces formative diagnostic guidance without revealing the complete solution.

#### Exact Template Text
```text
You are a code evaluator for Programming for Problem Solving (PPS).
Problem Description: {problem_description}
Student Submission:
```c
{student_code}
```

Provide constructive, step-by-step feedback and hints without giving away the full answer.
```

#### Variable Injection
- `{problem_description}`: Problem context or quiz question text.
- `{student_code}`: The raw C code string submitted by the student.

---

### 6.4 Template 4: `roadmap_generation`

#### Purpose
Generates ordered study milestones and practice checkpoints leading to curriculum mastery.

#### Exact Template Text
```text
Generate a structured milestone-based study roadmap for Programming for Problem Solving (PPS).
Target Competency: {target_competency}
Current Student Mastery: {current_mastery}

Provide ordered milestones and practice milestones.
```

#### Variable Injection
- `{target_competency}`: The goal topic (e.g., `"Pointers Mastery in PPS"`).
- `{current_mastery}`: The student's current baseline tier (e.g., `"Beginner"`, `"Intermediate"`, or `"High"`).

---

## 7. Personalization Architecture

### 7.1 Multi-Stage Personalization Pipeline

```text
Student ID: S001
      ↓
Historical Assessment Records (data/assessment_data.csv)
      ↓
Feature Engineering (member3/features.py)
   - accuracy: 1.00
   - learning_pace: 0.047
   - average_time: 20.25s
   - average_attempts: 1.0
      ↓
XGBoost Classifier (models/xgboost_model.pkl)
   - Predicted Mastery: "High"
      ↓
Rule-Based Twin Heuristics (member3/learning_twin.py)
   - Recommended Difficulty: "Advanced"
   - Pace Category: "Fast"
      ↓
LearningTwinAdapter (src/eduadapt/adapters/student_twin_adapter.py)
   - Maps to canonical StudentProfile
      ↓
PersonalizedContentGenerator (src/eduadapt/teaching/generator.py)
   - Evaluates mastery score: 1.00 >= 0.70 -> Advanced Tier
   - Retrieves Top-3 Curriculum Slide Chunks via RAG
   - Populates "personalized_teaching" Template
      ↓
Ollama (mistral:7b)
      ↓
Personalized Pedagogical Output
```

### 7.2 Conceptual Distinctions

To ensure architectural clarity across the team, the following four concepts must never be conflated:

1. **Student State (`member3.student_state`)**: The internal dictionary produced by Member 3 combining raw aggregate statistics (`accuracy`, `learning_pace`, `average_score`) with the XGBoost categorical prediction (`predicted_mastery_level`).
2. **`StudentProfile` (`src/eduadapt/interfaces/student_model.py`)**: The canonical, Pydantic-validated data contract shared across all modules. Contains `student_id`, `current_topic`, `mastery_levels` (dict of floats between 0.0 and 1.0), `preferred_pace`, `learning_style`, and `common_misconceptions`.
3. **Learning Twin (`member3.learning_twin`)**: The computational model representing the student's learning traits, containing rule-based difficulty adjustments (`Easy`, `Medium`, `Advanced`) and pace bins (`Slow`, `Medium`, `Fast`).
4. **Generated Teaching (`src/eduadapt/teaching`)**: The final textual and code output synthesized by Mistral 7B, conditioned on the student profile and grounded in curriculum retrieval.

---

## 8. Member 2 RAG Module: PPS Curriculum Intelligence

Member 2 owns the Curriculum Knowledge Base, converting raw PowerPoint slide decks into clean semantic vectors and providing sub-second retrieval for the generation pipeline.

### 8.1 Ingestion & Processing Pipeline

```text
data/raw/pps/*.pptx
      ↓
Document Loader (document_loader.py)
   - python-pptx extracts shape text, table cells, and notes slide-by-slide
   - Captures slide title as 'topic' and folder/file as 'module'
      ↓
Preprocessing (preprocessing.py)
   - Normalizes Unicode ligatures (fi, fl, quotes, dashes)
   - Detects C code blocks via keywords (#include, printf, int main)
   - Strips repeated institutional header/footer lines across slides
      ↓
Semantic Chunking (chunking.py)
   - Topic-aware chunker with target size 900 characters, 150 overlap
   - Applies 2.0x factor expansion to prevent splitting C code blocks
      ↓
Dense Vector Embedding (embeddings.py)
   - sentence-transformers/all-MiniLM-L6-v2 (384-dimensional embeddings)
   - In-memory LRU query cache (size: 256)
      ↓
Local Vector Store (vector_store.py)
   - Local persistent Qdrant collection: 'pps_curriculum'
   - Storage directory: vector_db/
   - Metric: Cosine Distance
```

### 8.2 Ingested Curriculum Inventory

The PPS curriculum knowledge base is built from 5 real PowerPoint presentations covering the complete PPS syllabus:

| Slide Deck File | PPS Curriculum Scope | Slide Count | Key Topics Covered |
|---|---|---|---|
| `Unit 1 PPS.pptx` | Unit 1: Foundations | 132 slides | Flowcharts, algorithms, pseudo-code, C data types, variables, constants |
| `PPS Unit 2.pptx` | Unit 2: Control & Pointers | 206 slides | Control statements (if, switch), loops (for, while), 1D/2D arrays, pointers |
| `PPS Unit 3.pptx` | Unit 3: Strings & Functions | 105 slides | String manipulation (`strlen`, `strcpy`, `strcat`), user-defined functions, call-by-value, call-by-reference |
| `UNIT 4-PPS.pptx` | Unit 4: Python Essentials | 163 slides | Python syntax, lists, tuples, dictionaries, file handling |
| `pps u5.pptx` | Unit 5: Data Science Tools | 60 slides | NumPy arrays, multidimensional slicing, Pandas DataFrames, `.query()` |
| **TOTALS** | **Units 1 through 5** | **666 slides** | **966 indexed chunks / vectors** |

### 8.3 Chunk & Metadata Schema
Each stored chunk in `vector_db` and `data/processed/chunks.jsonl` contains:
- `chunk_id`: Stable hash identifier formatted as `doc_<id>_c<idx>`.
- `text`: Cleaned text content preserving C syntax.
- `source`: Source filename (e.g., `"PPS Unit 2.pptx"`).
- `page`: Slide number (1-indexed).
- `module`: Curriculum unit (e.g., `"Unit 2"`).
- `topic`: Extracted slide title (e.g., `"POINTERS"`, `"INITIALIZING OF 2D ARRAY"`).
- `has_code`: Boolean flag indicating C/Python code presence.

---

## 9. RAG Retrieval Evaluation & Results

### 9.1 Evaluation Methodology
Retrieval quality is evaluated using `evaluation/evaluate_retrieval.py` against `evaluation/test_queries.json`. The benchmark contains 10 realistic PPS curriculum queries spanning all 5 units, each mapped to expected topics, source slide decks, and unit modules.

> [!IMPORTANT]
> **Retrieval Metrics vs. LLM Accuracy**:  
> Hit@K, Recall@K, and MRR measure whether the vector search finds the correct curriculum slide excerpts. They are **information retrieval metrics**, not LLM accuracy, and do not evaluate the factual correctness of Mistral's final generation.

### 9.2 Exact Observed Benchmark Results

Executing `python evaluation/evaluate_retrieval.py` against the 966-vector local Qdrant collection produces the following results across all 10 queries:

| Metric | Top-1 ($K=1$) | Top-3 ($K=3$) | Top-5 ($K=5$) | Definition |
|---|---|---|---|---|
| **Hit Rate @ K** | **1.00 (100%)** | **1.00 (100%)** | **1.00 (100%)** | Fraction of queries where at least one relevant slide is in the top $K$. |
| **Mean Recall @ K** | **0.72 (72.0%)** | **0.97 (97.0%)** | **0.97 (97.0%)** | Fraction of all expected curriculum items retrieved in the top $K$. |
| **Mean Reciprocal Rank (MRR)** | **1.00** | **1.00** | **1.00** | Average of $\frac{1}{\text{rank}}$ of the first relevant retrieved result. |

### 9.3 Per-Query Retrieval Breakdown

| Query ID | Topic / Query String | Expected Source | Top Retrieved Slide | Top Score | Hit@5 | Recall@5 |
|---|---|---|---|---|---|---|
| `q01` | Basic data types (int, char, float) | `Unit 1 PPS.pptx` | Slide 73 (Examples) | 0.703 | 1.0 | 1.00 |
| `q02` | Guidelines and symbols for flowcharts | `Unit 1 PPS.pptx` | Slide 32 (Guidelines) | 0.740 | 1.0 | 1.00 |
| `q03` | Switch case control statement in C | `PPS Unit 2.pptx` | Slide 61 (SRM) | 0.742 | 1.0 | 0.67 |
| `q04` | Declare and initialize 2D arrays in C | `PPS Unit 2.pptx` | Slide 107 (Output) | 0.702 | 1.0 | 1.00 |
| `q05` | Pointer declaration and concept | `PPS Unit 2.pptx` | Slide 156 (Definition) | 0.806 | 1.0 | 1.00 |
| `q06` | String functions (strlen, strcpy, strcat) | `PPS Unit 3.pptx` | Slide 14 (STRING FUNCTIONS) | 0.695 | 1.0 | 1.00 |
| `q07` | Call by value vs call by reference | `PPS Unit 3.pptx` | Slide 74 (TYPES OF CALLING) | 0.650 | 1.0 | 1.00 |
| `q08` | Python lists and dictionaries | `UNIT 4-PPS.pptx` | Slide 112 (Python Dictionary) | 0.639 | 1.0 | 1.00 |
| `q09` | Single and multidimensional NumPy arrays | `pps u5.pptx` | Slide 2 (Creating NumPy Array) | 0.821 | 1.0 | 1.00 |
| `q10` | Pandas DataFrame `.query()` method | `pps u5.pptx` | Slide 36 (Definition and Usage) | 0.775 | 1.0 | 1.00 |

### 9.4 Retrieval Limitations
- **Generic Slide Titles**: Slides titled `"SRM"`, `"Example"`, or `"Output"` rely heavily on dense vector context rather than keyword matching.
- **Recall Limitation on Query 3**: Query `q03` achieves Recall@5 of 0.67 because switch-case slides span multiple pages, and some chunks fall beyond rank 5.

---

## 10. Member 3: Student Modeling & Learning Twin

Member 3 owns historical assessment analysis, student feature engineering, rule-based learning twin heuristics, and XGBoost-based mastery classification.

### 10.1 Module Architecture
- **`member3/assessment.py`**: Reads `data/assessment_data.csv` and computes total questions, correct answers, overall accuracy, and average quiz score for a given student.
- **`member3/features.py`**: Groups records by `student_id` to engineer 7 statistical features:
  1. `accuracy`: Total correct / total questions.
  2. `recent_accuracy`: Accuracy over the most recent 2 quiz submissions.
  3. `average_score`: Mean percentage score.
  4. `average_attempts`: Mean number of attempts before correct solution.
  5. `average_time`: Mean time taken in seconds.
  6. `previous_mastery`: Baseline historical accuracy.
  7. `learning_pace`: Inverse speed indicator defined as $\frac{1.0}{\text{average\_time} + 1.0}$.
- **`member3/learning_twin.py`**: Applies rule-based thresholds to feature dictionaries:
  - **Difficulty**:
    - $\text{accuracy} < 0.50 \implies \text{Easy}$
    - $0.50 \le \text{accuracy} < 0.75 \implies \text{Medium}$
    - $\text{accuracy} \ge 0.75 \implies \text{Advanced}$
  - **Learning Pace**:
    - $\text{learning\_pace} < 0.02 \implies \text{Slow}$
    - $0.02 \le \text{learning\_pace} < 0.04 \implies \text{Medium}$
    - $\text{learning\_pace} \ge 0.04 \implies \text{Fast}$
- **`member3/student_state.py`**: Unifies feature extraction, rule-based twin heuristics, and the serialized XGBoost model to produce the full student state dictionary.
- **`member3/update_state.py`**: Recomputes feature values and Learning Twin assignments when new quiz records are appended.

---

## 11. XGBoost Mastery Model & Evaluation Reality

### 11.1 Model Configuration
The classification model is defined in `member3/train_xgboost.py`:
- **Model Type**: `xgboost.XGBClassifier`
- **Hyperparameters**: `n_estimators=100`, `max_depth=3`, `learning_rate=0.1`, `eval_metric="mlogloss"`, `random_state=42`.
- **Target Variable**: `mastery_level` (`"Low"`, `"Medium"`, `"High"`), encoded via `sklearn.preprocessing.LabelEncoder`.
- **Serialized Artifact**: `models/xgboost_model.pkl` (contains model instance, label encoder, and feature list).

### 11.2 Evaluation Context & Exact Results

> [!CAUTION]
> **Demo Dataset Limitation**:  
> `data/assessment_data.csv` contains only **24 rows across 6 students** (`S001` through `S006`), all evaluated solely on the topic `"Loops"`. When grouped by `student_id`, this yields exactly **6 feature vectors**.

In `member3/evaluate.py`, a stratified split with `test_size=3` is performed:
- Training set: 3 students (1 High, 1 Medium, 1 Low).
- Test set: 3 students (1 High, 1 Medium, 1 Low).

Executing `python -m member3.evaluate` yields the exact output:
```text
Evaluation Accuracy: 0.333

Classification Report:
              precision    recall  f1-score   support

        High       0.33      1.00      0.50         1
         Low       0.00      0.00      0.00         1
      Medium       0.00      0.00      0.00         1

    accuracy                           0.33         3
   macro avg       0.11      0.33      0.17         3
weighted avg       0.11      0.33      0.17         3
```

**Context & Explanation**:
- The model correctly predicts the `High` mastery sample, but misclassifies `Low` and `Medium` on this tiny 3-sample test split, resulting in $\frac{1}{3} = \mathbf{33.3\%}$ accuracy.
- **This 33.3% figure is an artifact of synthetic demonstration data**, proving the end-to-end integration of the scikit-learn/XGBoost pipeline, but is **NOT a production-ready model**.

---

## 12. Student Twin Adapter & Integration

### 12.1 Purpose of `LearningTwinAdapter`
Member 3's output is an unvalidated Python dictionary (`{"student_id": "S001", "mastery": 1.0, "accuracy": 1.0, ...}`). The core GenAI and verification services require a strongly-typed, Pydantic-validated `StudentProfile` adhering to `StudentModelInterface`.

`LearningTwinAdapter` (`src/eduadapt/adapters/student_twin_adapter.py`) bridges this boundary:
```python
class LearningTwinAdapter(StudentModelInterface):
    def get_profile(self, student_id: str, topic: Optional[str] = None) -> Optional[StudentProfile]:
        raw_state = get_student_state(student_id)
        if raw_state is None:
            return None
        target_topic = topic or self.default_topic
        return StudentProfile(
            student_id=str(raw_state["student_id"]),
            current_topic=target_topic,
            mastery_levels={target_topic: float(raw_state.get("mastery", 0.0))},
            learning_style="balanced",
            preferred_pace=str(raw_state.get("learning_pace", "moderate")).lower(),
            common_misconceptions=[],
        )
```

### 12.2 Handling Unknown Students
When an unrecognized student ID (e.g., `"S999"`) is queried:
1. `get_student_state("S999")` returns `None`.
2. `LearningTwinAdapter.get_profile("S999")` returns `None`.
3. `AdaptiveLearningService` catches the `None` return and creates a safe baseline fallback profile:
   - `found = False`
   - `mastery = 0.0`
   - `recommended_difficulty = "Medium"`
   - `predicted_mastery_level = "Unknown"`
   - Downstream generation proceeds safely at beginner cognitive depth.

---

## 13. GenAI + RAG Integration Workflow

The interaction between `PersonalizedContentGenerator` and `RAGInterface` occurs during `generate_for_student()`:

```text
1. Student Profile Received (S001, mastery=1.00)
2. Topic Determined ("Pointers")
3. RAG Query Formulated (query="Pointers", top_k=3)
4. Vector Search Executed against Qdrant collection 'pps_curriculum'
5. RAGContext Object Created containing 3 RAGDocument instances
6. Curriculum Text Formatted via rag_context.format_for_prompt()
7. Cognitive Depth Calibrated (mastery >= 0.70 -> Advanced)
8. Prompt Populated with Topic, Mastery, History, Misconceptions, and Curriculum Context
9. Mistral 7B Invoked synchronously via Ollama HTTP client
10. GenerationResult Validated and returned with token metrics
```

---

## 14. Response Verification & Safety Layer

Member 4 implements `ResponseVerifier` (`src/eduadapt/verification/response_verifier.py`) to provide automated safety and grounding signals over generated content.

### 14.1 Deterministic Verification Signals
1. **Response Presence**: Verifies non-empty text generation.
2. **Curriculum Availability**: Verifies that retrieved RAG slides were passed.
3. **Grounding Ratio & Lexical Overlap**:
   - Tokenizes the retrieved curriculum slide text and the generated response (stripping common English stop words).
   - Computes $\text{matched\_terms} = \text{curriculum\_tokens} \cap \text{response\_tokens}$.
   - If $\ge 5$ terms match or overlap ratio $\ge 0.15$: Marked `"Verified: grounded in retrieved PPS curriculum terminology"`.
4. **C Code Extraction**: Detects and extracts C code blocks (`extract_c_code`).
5. **Host Safety Invariant**: Strictly flags untrusted code as `ExecutionStatus.NOT_EXECUTED_UNTRUSTED`.
6. **While-Loop Regression Check**: Verifies that the explanation does not claim a while loop "continues until $i > n+1$".
7. **Overall Status**: Returns `"VERIFIED_SAFE"`, `"FLAGGED_REGRESSION"`, or `"FAILED_EMPTY_RESPONSE"`.

---

## 15. Accessibility Subsystem

### 15.1 Structured Content Formatting
`AccessibilityFormatter` (`src/eduadapt/accessibility/formatter.py`) reformats the session output dictionary into clean, modular sections suitable for screen readers:
- `screen_reader_summary`: Concise one-paragraph spoken overview.
- `topic` & `learning_level`: Explicit metadata headers.
- `explanation`: Full conceptual narrative.
- `examples`: Standalone C code block.
- `practice_question`: Quiz question, options, and explanation.
- `sources`: List of curriculum slides with slide numbers for reference.

### 15.2 Optional Speech Modules
- **Speech-to-Text (`speech_input.py`)**:
  - [OPTIONAL]: Uses `openai-whisper` (`whisper.load_model("base")`) to transcribe user voice queries.
  - If `whisper` is not installed, catches `ImportError` and returns an informative notice without crashing.
- **Text-to-Speech (`speech_output.py`)**:
  - [IMPLEMENTED]: On Windows, leverages the built-in PowerShell `System.Speech.Synthesis.SpeechSynthesizer` without requiring external Python packages.
  - [OPTIONAL]: Falls back to `pyttsx3` if available.

---

## 16. Final Adaptive Learning Service Contract

The orchestrator `AdaptiveLearningService.run_learning_session()` produces a standardized dictionary contract consumed by CLI scripts and the FastAPI backend:

```json
{
  "student": {
    "student_id": "S001",
    "found": true,
    "mastery": 1.0,
    "accuracy": 1.0,
    "learning_pace": "Fast",
    "recommended_difficulty": "Advanced",
    "predicted_mastery_level": "High"
  },
  "profile": {
    "current_topic": "Pointers",
    "mastery_levels": { "Pointers": 1.0 },
    "preferred_pace": "fast",
    "learning_style": "balanced",
    "common_misconceptions": []
  },
  "curriculum": {
    "topic": "Pointers",
    "retrieved_count": 3,
    "retrieved_chunks": [
      {
        "doc_id": "doc_Unit_1_PPS_pptx_c50",
        "source": "Unit 1 PPS.pptx",
        "slide_or_page": 50,
        "unit_or_module": "Unit 1",
        "topic": "Structured Programming",
        "relevance_score": 0.6163,
        "preview": "Structured programming concepts..."
      }
    ]
  },
  "teaching": {
    "generated_teaching_content": "<MISTRAL_OR_MOCK_GENERATED_EXPLANATION>",
    "provider": "OllamaLLMClient",
    "model": "mistral:7b",
    "latency": 26.93,
    "token_information": {
      "prompt_tokens": 327,
      "completion_tokens": 614,
      "total_tokens": 941
    }
  },
  "assessment": {
    "topic": "Pointers",
    "question": "What is the output of dereferencing a pointer `*ptr` when `int a = 42; int *ptr = &a;` in C?",
    "options": ["A) Memory address of a", "B) 42", "C) Null pointer error", "D) Garbage value"],
    "correct_option": "B",
    "explanation": "The dereference operator `*` accesses the value stored at the memory location pointed to by `ptr`.",
    "score": 95,
    "accuracy": 1.0,
    "attempts": 1,
    "time_taken_seconds": 25,
    "historical_performance": { "accuracy": 1.0, "average_score": 90.0 }
  },
  "feedback": {
    "problem": "Practice submission for Pointers",
    "feedback": "<CONSTRUCTIVE_DIAGNOSTIC_HINTS>",
    "model": "mistral:7b"
  },
  "learning_state": {
    "initial_state": { "student_id": "S001", "mastery": 1.0, "accuracy": 1.0 },
    "can_update_in_place": true,
    "updated_state": { "student_id": "S001", "mastery": 1.0, "accuracy": 1.0, "learning_pace": "Fast", "recommended_difficulty": "Advanced" },
    "status_message": "Learning Twin state recomputed with assessment submission: mastery=1.0, pace=Fast, difficulty=Advanced."
  },
  "roadmap": {
    "target_competency": "Pointers Mastery in PPS",
    "current_mastery": "High",
    "roadmap_content": "<ORDERED_MILESTONE_PROGRESSION>",
    "model": "mistral:7b"
  },
  "verification": {
    "generation_completed": true,
    "curriculum_context_available": true,
    "retrieved_sources_count": 3,
    "matched_curriculum_terms_count": 14,
    "grounding_ratio": 0.389,
    "grounding_status": "Verified: grounded in retrieved PPS curriculum terminology",
    "code_detected": true,
    "extracted_code_lines": 18,
    "code_execution": "NOT_EXECUTED_UNTRUSTED",
    "safety_status": "Enforced: untrusted LLM code is NOT executed on host machine",
    "regression_check": "Passed",
    "overall_status": "VERIFIED_SAFE"
  },
  "accessibility": {
    "topic": "Pointers",
    "learning_level": "High",
    "preferred_pace": "fast",
    "explanation": "<TEXT>",
    "examples": "<EXTRACTED_C_CODE>",
    "practice_question": { "question": "...", "options": [...], "explanation": "..." },
    "feedback": "...",
    "sources": [{ "source": "Unit 1 PPS.pptx", "slide_or_page": 50, "module": "Unit 1" }],
    "screen_reader_summary": "Lesson on Pointers for High level student S001. Grounding verified with 3 curriculum slides. Includes interactive practice assessment question with feedback.",
    "modality": "screen_reader_and_text_optimized"
  }
}
```

---

## 17. Full Demonstration Walkthrough

### 17.1 Demo Command
The full end-to-end demonstration is executed via:
```bash
python scripts/run_full_demo.py --student-id S001 --topic Pointers --provider ollama --model mistral:7b --top-k 3
```
*(For environments without Ollama running, supply `--provider mock` for instant execution.)*

### 17.2 Real Observed Output Trace

```text
================================================================================
                 EDUADAPT ADAPTIVE LEARNING DEMO
================================================================================

1. INITIAL STUDENT STATE
- Student ID             : S001
- Mastery                : 1.00
- Accuracy               : 1.00
- Learning Pace          : Fast
- Recommended Difficulty : Advanced
- Predicted Mastery      : High

2. PERSONALIZED PROFILE
- Topic                  : Pointers
- Mastery Level          : 1.00
- Preferred Pace         : fast
- Learning Style         : balanced

3. CURRICULUM RETRIEVAL
Top 3 retrieved PPS sources for query 'Pointers':
  [1] PPTX: Unit 1 PPS.pptx
      Slide/Page: 50 | Unit: Unit 1 | Topic: Structured Programming (score: 0.6163)
  [2] PPTX: PPS Unit 2.pptx
      Slide/Page: 156 | Unit: Unit 2 | Topic: Definition (score: 0.5989)
  [3] PPTX: PPS Unit 2.pptx
      Slide/Page: 172 | Unit: Unit 2 | Topic: Limitations of Pointer Arithmetic (score: 0.5867)

4. PERSONALIZED TEACHING
- Model / Provider       : mistral:7b (OllamaLLMClient)
- Completion Tokens      : 614

--- Generated Teaching Content ---
In C programming, pointers are variables that hold the memory address of another variable...
```c
int a = 42;
int *ptr = &a;
printf("Address of a: %p\n", (void *)ptr);
printf("Value of a: %d\n", *ptr);
```
--- End Teaching Content ---

5. RESPONSE VERIFICATION
- Curriculum Context     : Available (3 chunks)
- Grounding Check        : Verified: grounded in retrieved PPS curriculum terminology (14 terms matched, ratio: 0.389)
- Generation Completed   : Yes
- C Code Detected        : Yes
- Code Safety / Sandbox  : Enforced: untrusted LLM code is NOT executed on host machine
- Untrusted Code Status  : NOT_EXECUTED_UNTRUSTED
- Regression Check       : Passed
- Overall Status         : VERIFIED_SAFE

6. PRACTICE / ASSESSMENT
- Assessment Topic       : Pointers
- Question               : What is the output of dereferencing a pointer `*ptr` when `int a = 42; int *ptr = &a;` in C?
  A) Memory address of a
  B) 42
  C) Null pointer error
  D) Garbage value
- Evaluation Score       : 95 / 100
- Accuracy               : 1.00
- Attempts               : 1
- Time Taken             : 25s
- Correct Answer         : Option B (The dereference operator `*` accesses the value stored at the memory location pointed to by `ptr`.)

7. FEEDBACK
Constructive Feedback: Your pointer initialization syntax is clean. Notice how assigning `*p = 100` modifies the original variable `val` directly in memory.

8. LEARNING TWIN STATUS
- Status                 : Learning Twin state recomputed with assessment submission: mastery=1.0, pace=Fast, difficulty=Advanced.
- Updated Mastery        : 1.00
- Updated Accuracy       : 1.00
- Updated Pace           : Fast
- Recommended Difficulty : Advanced

9. ROADMAP
- Target Competency      : Pointers Mastery in PPS
- Baseline Mastery       : High
- Roadmap Milestones     : Stage 1: Memory Layout & Addresses; Stage 2: Pointer Arithmetic; Stage 3: Pointers to Pointers & Dynamic Allocation.

10. ACCESSIBILITY
- Formatted Modality     : screen_reader_and_text_optimized
- Screen Reader Summary  : Lesson on Pointers for High level student S001. Grounding verified with 3 curriculum slides. Includes interactive practice assessment question with feedback.
- Optional Speech Input  : Not requested (standard text input used)
- Optional Speech Output : Not requested
================================================================================
EduAdapt Adaptive Learning Session Demonstration Completed.
================================================================================
```

---

## 18. Exact Demonstration Results: Data Classification

| Value / Metric | Observed Value | Classification | Source / Rationale |
|---|---|---|---|
| Initial Mastery | `1.00` | **DEMO DATA** | Calculated from 4 perfect quiz rows for `S001` in `data/assessment_data.csv`. |
| Initial Accuracy | `1.00` | **DEMO DATA** | Calculated from `assessment_data.csv` (`correct=1` on all 4 items). |
| Learning Pace | `"Fast"` | **DEMO DATA** | Calculated via heuristic $\frac{1.0}{20.25 + 1.0} = 0.047 \ge 0.04$. |
| Recommended Difficulty | `"Advanced"` | **DEMO DATA** | Heuristic based on accuracy $\ge 0.75$. |
| Predicted Mastery Level | `"High"` | **DEMO DATA / MODEL** | Output of `xgboost_model.pkl` on `S001`'s features. |
| Retrieved Slide Chunks | 3 slides | **REAL OBSERVED OUTPUT** | Real vector search against Qdrant (`Unit 1` p.50, `Unit 2` p.156, `Unit 2` p.172). |
| Grounding Terms Matched | 14 terms | **REAL OBSERVED OUTPUT** | Intersection of slide vocabulary with Mistral generation. |
| Code Execution Status | `NOT_EXECUTED_UNTRUSTED`| **STATIC SAFETY POLICY** | Enforced by `ResponseVerifier` and `CExecutor`. |
| Overall Verification | `VERIFIED_SAFE` | **REAL OBSERVED OUTPUT** | Result of deterministic checks (presence, overlap, regression). |
| Assessment Score | 95 / 100 | **STATIC CONFIGURATION** | Default representative submission in `STATIC_PPS_ASSESSMENT_BANK`. |
| Test Suite Passes | 103 passed, 1 warning | **REAL OBSERVED OUTPUT** | Output of `pytest tests/` in 24.76s. |

---

## 19. Security, Safety, and Execution Sandboxing Model

### 19.1 Host Protection Policy
EduAdapt enforces a strict security policy regarding C code:
- **LLM-Generated Code Is Untrusted**: Large language models can hallucinate dangerous system commands (`system("rm -rf ...")`), invalid memory allocations, infinite loops, or malicious shell exploits.
- **Enforced Isolation**: LLM-generated code is **NEVER compiled or executed on the host machine**. It is extracted, syntax-highlighted, saved for human review, and flagged as `ExecutionStatus.NOT_EXECUTED_UNTRUSTED`.

### 19.2 Trusted Reference Execution Engine
- `src/eduadapt/evaluation/c_executor.py` maintains a `CExecutor` class that **only executes vetted benchmark reference programs** (authored by course faculty in `data/benchmark/pps_benchmark_20.json`).
- **Compilation Flags**: Uses GCC with `-std=c99 -Wall`.
- **Resource Limits**: Strict subprocess timeout (default 3.0s, compilation 10.0s) prevents CPU exhaustion from infinite loops.
- **Process Isolation**: Code is compiled and run inside temporary directories (`tempfile.TemporaryDirectory()`), ensuring disk cleanup upon completion.

---

## 20. 20-Question Mistral 7B Benchmark Results

The automated evaluation framework (`scripts/run_pps_evaluation.py`) was executed across 20 curated PPS questions covering 7 curriculum areas. The full output is preserved in `data/evaluation_results_mistral7b.json`.

### 20.1 Summary Performance Metrics

| Benchmark Metric | Observed Value | Interpretation |
|---|---|---|
| Total Questions Evaluated | 20 | Curated PPS questions covering Variables, Operators, Conditionals, Loops, Arrays, Functions. |
| Successful Inferences | 20 / 20 (100%) | Ollama maintained continuous HTTP availability with zero crashes or connection drops. |
| Mean Latency per Question | **26.93 seconds** | Average generation time per question on local consumer hardware. |
| Total Prompt Tokens Processed | 6,652 tokens | Total tokens evaluated across all 20 prompt templates. |
| Total Completion Tokens Generated | 12,581 tokens | Total response tokens synthesized by Mistral 7B. |
| Mean Concept Coverage Indicator | **84.9% (0.849)** | Automated keyword coverage indicator (*not model accuracy*). |
| Compiler Detected | `C:\MinGW\bin\gcc.exe` | Verified MinGW GCC installation on the host machine. |
| Trusted Reference Runs | 20 / 20 (100%) Passed | All faculty reference solutions compiled and exited cleanly with exit code 0. |
| While-Loop Termination Regressions | **0 detected** | Zero instances of the erroneous "continues until $i > n+1$" pattern. |
| Pedagogical Manual Review Status | `is_reviewed = false` | Automated indicators complete; expert human review rubric pending execution. |

---

## 21. Pytest Test Suite Audit

The test suite validates module isolation, edge cases, regression guards, and end-to-end integration:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\kanishk\OneDrive\Desktop\EduAdapt
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.13.0, langsmith-0.10.16, asyncio-1.4.0
collected 103 items

tests\test_adaptive_learning_service.py ......                           [  5%]
tests\test_evaluation.py ............                                    [ 17%]
tests\test_loading_and_preprocessing.py ..............................   [ 46%]
tests\test_ollama.py ......                                              [ 52%]
tests\test_retrieval.py ......................................           [ 89%]
tests\test_smoke.py .......                                              [ 96%]
tests\test_student_twin_adapter.py ....                                  [100%]

======================= 103 passed, 1 warning in 24.76s =======================
```

### Test Breakdown by Subsystem
1. **`test_adaptive_learning_service.py` (6 tests)**: Validates `run_learning_session` output structure, S001 student state, RAG integration, custom quiz submissions, fallback handling for unknown students, and accessibility formatting.
2. **`test_evaluation.py` (12 tests)**: Validates C compiler discovery, trusted reference compilation, untrusted code safety marking (`NOT_EXECUTED_UNTRUSTED`), and while-loop regression detection.
3. **`test_loading_and_preprocessing.py` (30 tests)**: Tests document loaders (`.pptx`, `.pdf`, `.txt`, `.md`), ligature cleaning, and C-code preservation.
4. **`test_ollama.py` (6 tests)**: Validates Ollama client initialization, parameter mapping, timeout handling, and exception raising.
5. **`test_retrieval.py` (38 tests)**: Tests chunking, embedding generation, Qdrant store upserts, and vector retrieval.
6. **`test_smoke.py` (7 tests)**: Validates core GenAI pipeline components, prompt template rendering, and `MockLLMClient`.
7. **`test_student_twin_adapter.py` (4 tests)**: Tests profile adaptation from Member 3, default topic assignment, and unknown student handling.

---

## 22. Git History, Branches, and Commits

### 22.1 Branch Topology
- **Current Active Branch**: `feature/member1-genai-review2` (ahead of origin by 7 commits).
- **`main` Branch**: Contains base project setup.
- **Remote Tracking Branches**:
  - `origin/main` (commit `75c0138`: Merge PR #4)
  - `origin/member2-rag` (commit `1194569`: Add files via upload)
  - `origin/member3-learning-twin` (commit `422cd93`: Add Member 3 learning twin and XGBoost)
  - `origin/member4-speech-accessibility-verification` (commit `84d9356`: Add Member 4 accessibility and verification)

### 22.2 Key Commits on Current Branch
- `1d7cc67`: `feat(demo): complete adaptive learning demonstration` (Unified end-to-end service and CLI demo).
- `a7d3365`: `feat(demo): complete adaptive learning demonstration` (Pre-demo formatting updates).
- `0cae7d4`: `feat(integration): connect learning twin rag and genai` (Wired Member 2 RAG and Member 3 Twin into GenAI).
- `980695b`: `feat(student): add learning twin adapter` (Implemented `LearningTwinAdapter`).
- `27b5fbd`: `fix(student): make learning twin root-safe` (Resolved cross-directory relative path imports).
- `2bd0c76`: `feat(student): integrate member3 learning twin` (Integrated Member 3 feature engineering).
- `9bb8a76`: `feat(rag): add PPS PPTX ingestion and retrieval validation` (Ingested 5 PPTX decks into Qdrant).
- `b9e9a79`: `feat(rag): integrate PPS curriculum retrieval` (Added Qdrant retrieval client).
- `5a56a14`: `feat(genai): add member 1 GenAI baseline` (Initial Ollama client and prompt templates).

---

## 23. Frontend Implementation & Vercel Readiness

### 23.1 Frontend Architecture & Technology
The frontend is implemented in the `frontend/` directory using modern web standards:
- **Framework**: **React 19** (`^19.2.8`) with `react-dom`.
- **Bundler / Dev Server**: **Vite 6/8** (`^8.3.0`) with `@vitejs/plugin-react`.
- **Linter**: **Oxlint** (`^1.81.0`).
- **Styling**: Academic minimalist CSS using custom CSS variables, semantic borders, and zero external CSS bloat.
- **Design Philosophy**: High-contrast, accessibility-first (WCAG 2.1 AA), typography-focused layout without animated gradients or distraction.

### 23.2 Component Architecture & Page Hierarchy
The application renders via a two-column responsive grid in `frontend/src/pages/Dashboard.jsx`:
- **Left Column: Student Modeling & Controls**:
  - `StudentProfile.jsx`: Displays Student ID, predicted mastery level, accuracy, pace, and difficulty badges.
  - `LearningControls.jsx`: Topic selection dropdown (Pointers, Loops, Arrays, Functions, Variables), Top-K slide retrieval count slider, and "Generate Learning Session" trigger button.
- **Right Column: Session Results**:
  - `TeachingContent.jsx`: Displays the generated pedagogical narrative with syntax-highlighted, copyable C code blocks.
  - `CurriculumContext.jsx`: Lists retrieved PPS lecture slides with slide numbers and relevance scores.
  - `VerificationPanel.jsx`: Displays safety badges, grounding overlap ratios, matched curriculum terms, and untrusted execution safety status.
  - `AssessmentPanel.jsx`: Formative quiz question viewer with multiple-choice options and solution explanation.
  - `FeedbackPanel.jsx`: Formative code feedback and diagnostic hints.
  - `LearningState.jsx`: Visualizes initial vs. updated Learning Twin state parameters.
  - `Roadmap.jsx`: Ordered milestone stages toward topic mastery.
  - `AccessibilityPanel.jsx`: Plain screen-reader summary and full accessible lesson transcript.

### 23.3 API Layer (`frontend/src/api/learningApi.js`)
Handles asynchronous HTTP communication with the backend:
- `fetchStudentProfile(studentId)`: `GET ${VITE_API_BASE_URL}/api/student/${studentId}`
- `generateLearningSession(studentId, topic, topK)`: `POST ${VITE_API_BASE_URL}/api/session/generate`

### 23.4 Vercel Deployment Readiness
The frontend is fully configured and ready for 1-click Vercel deployment:
1. **Root Directory**: `frontend`.
2. **Framework Preset**: `Vite`.
3. **Build Command**: `npm run build` (outputs to `frontend/dist/`).
4. **Environment Variables**: Set `VITE_API_BASE_URL` to the public URL of the EduAdapt backend.
5. **Pre-built Distribution**: The production build assets (`index.html`, assets, SVG icons) are already compiled and verified in `frontend/dist/`.

---

## 24. Comprehensive Dependencies Table

| Technology / Library | Version Specified | Purpose | Module Where Used |
|---|---|---|---|
| **Python** | 3.11.0 (Team Reference) | Core programming language runtime | Entire backend codebase |
| **pydantic** | $\ge 2.5.0$ | Data modeling, validation, and contract schemas | `src/eduadapt/interfaces/*`, `src/eduadapt/inference/base.py` |
| **pydantic-settings**| $\ge 2.1.0$ | Environment variable loading and validation | `src/eduadapt/config.py` |
| **python-dotenv** | $\ge 1.0.0$ | Reads `.env` configuration file | `src/eduadapt/config.py` |
| **requests** | $\ge 2.31.0$ | Synchronous HTTP calls to local Ollama API | `src/eduadapt/inference/ollama.py` |
| **fastapi** | $\ge 0.100.0$ | High-performance asynchronous REST API framework | `src/eduadapt/api.py` |
| **uvicorn** | $\ge 0.22.0$ | ASGI web server for FastAPI | `src/eduadapt/api.py` |
| **ollama** | $\ge 0.4.0$ | Official Ollama Python library | Listed in `requirements.txt` |
| **sentence-transformers** | $\ge 3.0$ | Dense text embeddings (`all-MiniLM-L6-v2`) | `src/eduadapt/rag/embeddings.py` |
| **qdrant-client** | $\ge 1.10$ | Embedded local vector database client | `src/eduadapt/rag/vector_store.py` |
| **python-pptx** | $\ge 1.0.0$ | Ingestion of PowerPoint curriculum slides | `src/eduadapt/rag/document_loader.py` |
| **pypdf** | $\ge 4.0$ | Parsing of PDF documents | `src/eduadapt/rag/document_loader.py` |
| **scikit-learn** | Installed in environment | `train_test_split`, `LabelEncoder`, metrics | `member3/train_xgboost.py`, `member3/evaluate.py` |
| **xgboost** | Installed in environment | Gradient-boosted decision trees for mastery | `member3/train_xgboost.py`, `member3/evaluate.py` |
| **joblib** | Installed in environment | Model serialization and deserialization | `member3/student_state.py`, `member3/train_xgboost.py` |
| **pandas** | Installed in environment | Tabular data manipulation and CSV loading | `member3/*`, `src/eduadapt/services/adaptive_learning.py` |
| **pytest** | $\ge 7.4.0$ | Automated test framework | `tests/*` |
| **MinGW GCC** | System binary (`gcc.exe`) | Compiling trusted C benchmark reference code | `src/eduadapt/evaluation/c_executor.py` |
| **React** | `^19.2.8` | Declarative user interface library | `frontend/src/*` |
| **Vite** | `^8.3.0` | Next-generation frontend bundler and dev server | `frontend/*` |
| **openai-whisper** | Optional | Speech-to-text audio transcription | `src/eduadapt/accessibility/speech_input.py` |
| **pyttsx3** | Optional | Cross-platform text-to-speech fallback | `src/eduadapt/accessibility/speech_output.py` |

---

## 25. Repository Datasets & Artifacts Inventory

| Name | File Location | Purpose | Format | Record Count / Size | Status |
|---|---|---|---|---|---|
| **PPS Curriculum Slides** | `data/raw/pps/*.pptx` | Primary course materials (Units 1-5) | PPTX | 5 files, 666 slides | **[IMPLEMENTED]** |
| **Processed Chunks** | `data/processed/chunks.jsonl` | Cleaned curriculum text chunks | JSONL | 966 records | **[IMPLEMENTED]** |
| **Local Vector DB** | `vector_db/` | Embedded Qdrant vector index | SQLite/Binary | 966 points (384-dim) | **[IMPLEMENTED]** |
| **Assessment Data** | `data/assessment_data.csv` | Student quiz records for Learning Twin | CSV | 24 rows (6 students) | **[DEMO DATA]** |
| **XGBoost Artifact** | `models/xgboost_model.pkl` | Serialized mastery classifier | Pickle/Joblib | Model + Encoder | **[DEMO MODEL]** |
| **Benchmark Problems** | `data/benchmark/pps_benchmark_20.json` | Curated PPS benchmark questions | JSON | 20 problems | **[IMPLEMENTED]** |
| **Manual Review Rubric** | `data/benchmark/manual_review_rubric.md` | Human pedagogical grading rubric | Markdown | 5 dimensions | **[IMPLEMENTED]** |
| **Retrieval Test Queries** | `evaluation/test_queries.json` | Evaluation queries for RAG | JSON | 10 queries | **[IMPLEMENTED]** |
| **Mistral Benchmark Output**| `data/evaluation_results_mistral7b.json`| Benchmark outputs & indicators | JSON | 20 results (101 KB) | **[TESTED]** |
| **Scenario Inference Output**| `data/real_model_responses.json` | 4 pedagogical scenario outputs | JSON | 4 results (13 KB) | **[TESTED]** |
| **Frontend Static Build** | `frontend/dist/` | Production compiled web assets | HTML/JS/CSS | Vercel-ready distribution | **[IMPLEMENTED]** |

---

## 26. File-by-File Repository Map

| Path | Purpose | Owner | Inputs | Outputs | Dependencies |
|---|---|---|---|---|---|
| `src/eduadapt/config.py` | Application configuration | Member 1 | Environment / `.env` | `Settings` instance | `pydantic-settings` |
| `src/eduadapt/api.py` | FastAPI HTTP REST API adapter | Member 1 | HTTP Requests | JSON responses | `fastapi`, `uvicorn` |
| `src/eduadapt/main.py` | Service factory and wiring | Member 1 | `Settings` | Service dictionary | `eduadapt.*` |
| `src/eduadapt/inference/base.py` | LLM client interface & mock | Member 1 | Prompt string | `GenerationResult` | `pydantic` |
| `src/eduadapt/inference/ollama.py` | Ollama HTTP inference client | Member 1 | Prompt & options | `GenerationResult` | `requests` |
| `src/eduadapt/prompts/templates.py`| Prompt template manager | Member 1 | Template parameters | Rendered prompt | `pydantic` |
| `src/eduadapt/teaching/generator.py`| Personalized content generator | Member 1 | `StudentProfile`, topic | `GenerationResult` | `inference`, `prompts`, `rag` |
| `src/eduadapt/feedback/evaluator.py`| C code feedback evaluator | Member 1 | Problem & student code | `GenerationResult` | `inference`, `prompts` |
| `src/eduadapt/roadmap/planner.py` | Milestone study roadmap planner| Member 1 | Topic & baseline level | `GenerationResult` | `inference`, `prompts` |
| `src/eduadapt/services/adaptive_learning.py`| Complete session orchestrator| Member 1 | `student_id`, topic | 10-key session dict | All modules |
| `src/eduadapt/adapters/student_twin_adapter.py`| Adapts Member 3 to StudentProfile| Member 1/3 | `student_id`, topic | `StudentProfile` | `member3.student_state` |
| `src/eduadapt/rag/document_loader.py`| Parses raw slides and documents | Member 2 | File path | `list[dict]` pages | `python-pptx`, `pypdf` |
| `src/eduadapt/rag/preprocessing.py`| Cleans text & preserves C code | Member 2 | Raw pages | Cleaned pages | regex |
| `src/eduadapt/rag/chunking.py` | Splits slides into chunks | Member 2 | Cleaned pages | `list[dict]` chunks | regex |
| `src/eduadapt/rag/embeddings.py` | Dense vector embedder | Member 2 | Text strings | `list[list[float]]` | `sentence-transformers` |
| `src/eduadapt/rag/vector_store.py`| Qdrant client wrapper | Member 2 | Chunks & vectors | Persisted vectors | `qdrant-client` |
| `src/eduadapt/rag/retriever.py` | Semantic similarity search | Member 2 | Query string, top-k | Retrieved chunks | `qdrant-client` |
| `src/eduadapt/rag/rag_interface.py`| PPS curriculum RAG adapter | Member 2 | Query string, top-k | `RAGContext` | `rag.*` |
| `member3/assessment.py` | Student quiz performance stats | Member 3 | CSV path, `student_id` | Statistics dict | `pandas` |
| `member3/features.py` | Feature extraction pipeline | Member 3 | DataFrame | Feature DataFrame | `pandas` |
| `member3/learning_twin.py` | Rule-based difficulty/pace | Member 3 | Feature dict | Twin dict | None |
| `member3/student_state.py` | Live student state generator | Member 3 | `student_id` | Full state dict | `joblib`, `features`, `learning_twin` |
| `member3/train_xgboost.py` | Model training script | Member 3 | `assessment_data.csv` | `xgboost_model.pkl` | `xgboost`, `sklearn`, `joblib` |
| `member3/evaluate.py` | Model evaluation script | Member 3 | Serialized model & data | Evaluation metrics | `sklearn`, `joblib` |
| `src/eduadapt/verification/response_verifier.py`| Response grounding & safety | Member 4 | Response & RAG chunks | `GroundingVerificationResult` | `c_executor`, `regression` |
| `src/eduadapt/accessibility/formatter.py`| Screen-reader formatter | Member 4 | Session dict | Accessible dict | None |
| `src/eduadapt/accessibility/speech_input.py`| Audio transcription hook | Member 4 | Audio file path | Text string | `whisper` (optional) |
| `src/eduadapt/accessibility/speech_output.py`| Audio speech synthesis hook | Member 4 | Text string | Audio WAV / speech | PowerShell / `pyttsx3` |
| `src/eduadapt/evaluation/c_executor.py`| C compiler discovery & execution| Member 4 | C source string | `CodeExecutionResult` | `subprocess`, `tempfile` |
| `src/eduadapt/evaluation/regression.py`| While-loop regression detector| Member 4 | Response text | Regression check dict| regex |
| `frontend/src/pages/Dashboard.jsx` | Academic React Dashboard | Member 4 | User interaction | UI Views | `react`, `learningApi` |
| `frontend/src/api/learningApi.js` | Frontend HTTP API client | Member 4 | User parameters | Backend JSON | `fetch` |

---

## 27. Zero-to-Hero Local Reproduction Guide

This section provides exact instructions for a teammate setting up the project on Windows with Python 3.11, Ollama, and Node.js.

### Step 1: Clone the Repository & Checkout Branch
```powershell
git clone https://github.com/kanishkupadhyay1/EduAdapt.git
cd EduAdapt
git checkout feature/member1-genai-review2
```

### Step 2: Configure Environment
Copy the environment template:
```powershell
Copy-Item .env.example .env
```

### Step 3: Install Python Dependencies
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install scikit-learn xgboost joblib pandas fastapi uvicorn
```

### Step 4: Install & Start Ollama
1. Download Ollama for Windows from [https://ollama.com/download](https://ollama.com/download) and install.
2. In a separate PowerShell terminal, pull the required model:
   ```powershell
   ollama pull mistral:7b
   ```
3. Verify that the Ollama service is responsive:
   ```powershell
   curl http://localhost:11434/api/tags
   ```

### Step 5: Verify PPS Curriculum Ingestion (RAG)
The repository includes pre-built vectors in `vector_db/`. To re-ingest and verify fresh indexing from the PPTX files:
```powershell
$env:PYTHONPATH="src"
python scripts/rag/ingest.py --rebuild
```

### Step 6: Run the Pytest Test Suite
```powershell
python -m pytest tests/ -v
```
*Expected result: 103 passed, 1 warning in ~25 seconds.*

### Step 7: Run the FastAPI Backend
Start the HTTP API server:
```powershell
$env:PYTHONPATH="src;."
python -m uvicorn eduadapt.api:app --host 0.0.0.0 --port 8000 --reload
```
*Verify in browser at `http://localhost:8000/health` or `http://localhost:8000/docs`.*

### Step 8: Run the React Web Dashboard
In another terminal:
```powershell
cd frontend
npm install
npm run dev
```
*Open `http://localhost:5173` in your browser to interact with the full dashboard.*

### Step 9: Run CLI Demonstrations
```powershell
$env:PYTHONPATH="src;."
# Using live local Mistral 7B:
python scripts/run_full_demo.py --student-id S001 --topic Pointers --provider ollama --model mistral:7b --top-k 3

# Or using fast mock provider (no GPU/Ollama required):
python scripts/run_full_demo.py --student-id S001 --topic Pointers --provider mock
```

---

## 28. End-to-End Traced Walkthrough: Student S001 on Pointers

To understand how data flows across module boundaries during a session, follow this step-by-step trace of `run_learning_session(student_id="S001", topic="Pointers")`:

1. **Request Received**: `AdaptiveLearningService` (or `POST /api/session/generate`) receives `student_id="S001"` and `topic="Pointers"`.
2. **Student State Extraction**:
   - `LearningTwinAdapter` invokes `member3.student_state.get_student_state("S001")`.
   - `member3.features.create_features` aggregates 4 quiz rows for `S001`: `accuracy=1.00`, `learning_pace=0.047`, `average_score=90.0`, `average_time=20.25`.
   - `member3.learning_twin.create_learning_twin` evaluates thresholds: `accuracy >= 0.75 -> "Advanced"`, `pace >= 0.04 -> "Fast"`.
   - `models/xgboost_model.pkl` predicts `predicted_mastery_level="High"`.
   - Output adapted to canonical `StudentProfile(student_id="S001", current_topic="Pointers", mastery_levels={"Pointers": 1.0}, preferred_pace="fast")`.
3. **Curriculum Retrieval**:
   - `PPSCurriculumRAG.retrieve("Pointers", top_k=3)` queries local Qdrant vectors.
   - Retrieves Slide 50 of `Unit 1 PPS.pptx` (score: 0.6163), Slide 156 of `PPS Unit 2.pptx` (score: 0.5989), and Slide 172 of `PPS Unit 2.pptx` (score: 0.5867).
4. **Prompt Rendering**:
   - `PersonalizedContentGenerator` detects `mastery_score = 1.0 >= 0.70`, selecting the Advanced cognitive tier.
   - RAG slide text is formatted into the `{context}` parameter.
   - The `"personalized_teaching"` template is rendered into a complete instruction prompt.
5. **LLM Generation**:
   - Dispatched to Ollama (`mistral:7b`) via HTTP POST.
   - Content returned with syntax-highlighted C code blocks.
6. **Safety & Verification**:
   - `ResponseVerifier` checks response non-emptiness (passed).
   - Counts curriculum term overlaps: 14 matching tokens (passed).
   - Extracts C code: 18 lines extracted.
   - **Enforces host protection**: Marks code as `ExecutionStatus.NOT_EXECUTED_UNTRUSTED`.
   - Runs regex check for while-loop termination errors (passed).
   - Assigns `overall_status = "VERIFIED_SAFE"`.
7. **Post-Learning Quiz & Assessment**:
   - Fetches pointer question from `STATIC_PPS_ASSESSMENT_BANK`: `"What is the output of dereferencing a pointer *ptr..."`.
   - Evaluates submission: Score 95, accuracy 1.0, attempts 1, time 25s.
8. **Feedback & Roadmap**:
   - `FeedbackGenerator` creates formative hints for pointer manipulation.
   - `RoadmapGenerator` synthesizes 3 ordered study milestones.
9. **State Update Simulation**:
   - Appends quiz result to `data/assessment_data.csv` in-memory.
   - Re-runs feature extraction and rule-based classification, confirming updated state: `mastery=1.0`, `pace="Fast"`, `difficulty="Advanced"`.
10. **Accessibility Formatting & UI Delivery**:
    - `AccessibilityFormatter` compiles structured sections and screen-reader summary.
    - Complete 10-key dictionary returned to caller or React Dashboard for visualization.

---

## 29. Implementation Status Matrix

### 29.1 Completed: `[IMPLEMENTED] & [TESTED]`
- [x] Local Ollama LLM inference client with retry and error hierarchy (`OllamaLLMClient`).
- [x] Deterministic mock LLM client for rapid testing (`MockLLMClient`).
- [x] Parameterized prompt template registry (`PromptManager`, 4 templates).
- [x] Student-aware personalized explanation generator (`PersonalizedContentGenerator`).
- [x] Diagnostic code feedback generator (`FeedbackGenerator`).
- [x] Learning roadmap planner (`RoadmapGenerator`).
- [x] Multi-format curriculum loader supporting `.pptx`, `.pdf`, `.txt`, `.md` (`DocumentLoader`).
- [x] Ligature-normalizing and C-code-preserving text cleaner (`preprocessing.py`).
- [x] Topic-aware and code-preserving chunker (`chunking.py`).
- [x] Dense vector embedder wrapper using `sentence-transformers/all-MiniLM-L6-v2` (`Embedder`).
- [x] Local persistent Qdrant vector storage wrapper (`VectorStore`).
- [x] RAG retrieval evaluation suite with Hit@K, Recall@K, and MRR metrics (`evaluate_retrieval.py`).
- [x] Ingestion and indexing of all 5 SRM PPS PPTX slide decks (666 slides, 966 vectors).
- [x] Response grounding and lexical overlap verifier (`ResponseVerifier`).
- [x] Host security enforcement marking untrusted LLM code as `NOT_EXECUTED_UNTRUSTED`.
- [x] Trusted C benchmark compilation and execution harness with GCC (`CExecutor`).
- [x] Targeted while-loop termination error regression detector (`check_while_loop_explanation`).
- [x] Accessibility content formatter for screen readers (`AccessibilityFormatter`).
- [x] Unified end-to-end service orchestrator (`AdaptiveLearningService`).
- [x] FastAPI HTTP REST API adapter (`src/eduadapt/api.py`).
- [x] React 19 + Vite academic web dashboard (`frontend/`).
- [x] End-to-end CLI demonstration scripts (`run_full_demo.py`, `run_integrated_demo.py`).
- [x] 103-test automated test suite passing in Pytest.

### 29.2 Partially Complete: `[DEMO / LIMITATION]`
- [!] **Student Learning Twin Dataset**: `data/assessment_data.csv` contains only 24 records for 6 students, limited strictly to the topic `"Loops"`.
- [!] **XGBoost Mastery Classifier**: Trained and evaluated on 6 aggregated samples with a 3-sample test split, yielding an evaluation accuracy of **33.3%**.
- [!] **Static Assessment Bank**: Formative quiz bank currently contains 4 curated questions (`Pointers`, `Loops`, `Arrays`, `Functions`); requires dynamic expansion.
- [!] **Pedagogical Manual Review**: 20 benchmark questions evaluated automatically (84.9% concept coverage); human expert rubric grading remains pending (`is_reviewed = false`).

### 29.3 Planned: `[PLANNED / NOT IMPLEMENTED]`
- [ ] **Longitudinal Student Cohort Tracking**: Database persistence (PostgreSQL / SQLite) tracking student progress across multiple academic terms.
- [ ] **Fine-Tuning Experiments**: QLoRA parameter-efficient fine-tuning of Mistral 7B on PPS C programming pedagogy.
- [ ] **Containerized Docker Deployment**: Unified multi-stage Docker container packaging backend, frontend, and Qdrant.

---

## 30. Technical Limitations & Constraints

1. **Small Learning Twin Dataset**: The student modeling component is trained on a synthetic demonstration dataset of 24 rows across 6 students. The 33.3% XGBoost test accuracy reflects small sample size rather than algorithmic failure. Real classroom data must be collected before deploying the classifier in production.
2. **Local Inference Latency**: Mistral 7B running on local CPU/consumer GPU averages ~26.9 seconds per generation. While acceptable for asynchronous study sessions, real-time interactive user experiences benefit from GPU acceleration or quantized inference.
3. **Automated Indicators vs. Pedagogical Correctness**: The 84.9% concept coverage ratio measures keyword presence, not educational validity. An explanation can contain technical keywords while possessing subtle pedagogical flaws. Authorized faculty must complete the manual review rubric.
4. **Untrusted Code Execution Isolation**: Because LLM-generated code cannot safely be executed directly on the host machine, student code verification is limited to static analysis, regex checks, and LLM critique, rather than full compiler-backed unit test suites.
5. **Static Quiz Bank**: The formative quiz question repository is currently small (4 topics); expanding this to hundreds of categorized items is required for semester-long deployment.

---

## 31. Alignment with Review-2 PBL Requirements

EduAdapt aligns directly with the Review-2 Project-Based Learning (PBL) criteria through its hybrid architecture:

| PBL Review Requirement | Technical Implementation in EduAdapt | Academic Justification |
|---|---|---|
| **Machine Learning (ML)** | Supervised gradient boosting via `xgboost.XGBClassifier` and feature engineering (`member3.features`) | Used for tabular student mastery classification based on historical performance indicators (accuracy, attempts, time). |
| **Deep Learning (DL)** | Local large language model `mistral:7b` (7-billion parameter transformer architecture) | Generates natural language pedagogical explanations, conceptual analogies, and code feedback adapted to student profiles. |
| **Natural Language Processing (NLP)** | Ligature normalization, regex code extraction, stop-word removal, and vocabulary intersection | Preprocesses raw curriculum slides and computes deterministic lexical grounding ratios between curriculum and generated text. |
| **Transformer Models** | Bi-encoder dense embeddings (`sentence-transformers/all-MiniLM-L6-v2`) and Mistral 7B | MiniLM creates 384-dimensional semantic embeddings for curriculum retrieval; Mistral generates contextual pedagogical instruction. |
| **Generative AI (GenAI)** | Parameterized prompt templates and deterministic generation pipelines in `eduadapt.teaching` | Synthesizes customized learning materials conditioned on student mastery, misconceptions, and retrieved curriculum slides. |
| **Prompt Engineering** | Structured multi-variable prompt templates (`PromptManager`, `personalized_teaching`) | Demonstrates systematic calibration of cognitive depth across Beginner, Intermediate, and Advanced engineering students. |
| **Architectural Rigor** | **Single central LLM within deterministic workflow; NO AGENTIC LOOPS** | Eliminates non-deterministic hallucination loops, reduces token overhead, and guarantees host system safety. |

---

## 32. Prompt Engineering Scenarios: Beginner, Intermediate, Advanced

### Scenario A: Beginner Learner (Mastery 0.25)
- **Profile**: Student `std_beginner_loops`, current topic `"For Loops"`, mastery score `0.25`, pace `"slow"`.
- **Misconceptions**: `"Thinking loop update condition runs before the loop body executes; Off-by-one errors with <= versus < operators"`.
- **Calibrated Injected Level**: `"Beginner (0.25) - provide intuitive foundational breakdown, simple analogies, and guided walkthrough"`.
- **Generated Pedagogical Behavior**: Mistral breaks down the execution cycle into 4 explicit, numbered steps (`Init -> Condition -> Body -> Update`), provides an execution trace table for `i = 0` to `i = 2`, and warns against off-by-one errors.

### Scenario B: Intermediate Learner (Mastery 0.55)
- **Profile**: Student `std_var_int`, current topic `"Variables and data types"`, mastery score `0.55`, pace `"moderate"`.
- **Misconceptions**: `"Believing ISO C guarantees ASCII encoding on all platforms"`.
- **Calibrated Injected Level**: `"Intermediate (0.55) - reinforce core mechanics and syntax applications"`.
- **Generated Pedagogical Behavior**: Mistral focuses on character arithmetic, demonstrates character-to-integer conversion (`digit - '0'`), and explicitly cites ISO C99/C11 clause 5.2.1 regarding contiguous decimal digit values while clarifying that ASCII is implementation-defined.

### Scenario C: Advanced Learner (Mastery 0.95)
- **Profile**: Student `std_advanced_loops`, current topic `"Nested Loops"`, mastery score `0.95`, pace `"fast"`.
- **Misconceptions**: None.
- **Calibrated Injected Level**: `"Advanced (0.95) - focus on nuances, edge cases, memory layout, and idiomatic efficiency"`.
- **Generated Pedagogical Behavior**: Mistral skips elementary syntax, focuses on 2D array traversal, demonstrates row-major memory order, explains CPU cache line locality, and provides an asymptotic time complexity analysis ($\mathcal{O}(N \times M)$).

---

## 33. Team Integration Contract & Interface Boundaries

To maintain software engineering integrity and prevent breaking changes across the team, all members must adhere to the following contracts:

### Rule 1: Do Not Modify Canonical Interfaces
- The files in `src/eduadapt/interfaces/` (`rag.py`, `student_model.py`, `accessibility.py`) represent the **team contract**.
- **No member may modify these files independently without unanimous agreement.**

### Rule 2: Member 2 (RAG) Integration Boundary
- Must interact with the rest of the application exclusively through `PPSCurriculumRAG` (`src/eduadapt/rag/rag_interface.py`), which implements `RAGInterface`.
- Method signature: `retrieve(query: str, top_k: int = 5) -> RAGContext`.
- Ensure each `RAGDocument` in `RAGContext.documents` includes valid `source`, `page`, `module`, and `topic` metadata.

### Rule 3: Member 3 (Student Model) Integration Boundary
- Member 3 should focus on expanding `data/assessment_data.csv` and refining feature algorithms in `member3/`.
- All interaction with GenAI is managed by `LearningTwinAdapter` (`src/eduadapt/adapters/student_twin_adapter.py`). Member 3 code should not directly call Ollama or import GenAI modules.

### Rule 4: Member 4 (Verification / Accessibility / UI) Integration Boundary
- Must maintain `ResponseVerifier.verify_response(response_text, retrieved_chunks, topic)` as a pure static method returning `GroundingVerificationResult`.
- Must preserve the host safety invariant: **never execute untrusted LLM code via `subprocess` or `os.system`**.
- Frontend components in `frontend/src/components/` must consume the canonical session dictionary contract returned by `POST /api/session/generate`.

### Rule 5: Member 1 (GenAI & Orchestration) Responsibility
- Member 1 maintains `AdaptiveLearningService` and `src/eduadapt/api.py`, coordinating inputs and outputs across all modules without altering internal member implementations.

---

## 34. Realistic Future Work

1. **Classroom Assessment Data Collection**: Replace the 24-row demo dataset with longitudinal quiz and lab submissions from real first-year PPS engineering cohorts to train a statistically robust XGBoost mastery classifier.
2. **Dynamic Assessment Generation**: Integrate LLM-assisted or question-bank-driven quiz generation covering all PPS units rather than 4 static topics.
3. **Dockerized Deployment**: Package the application into a Docker container with local Ollama or connect it to an institutional vLLM inference server for production scalability.
4. **Completion of Faculty Manual Reviews**: Have PPS course instructors complete the 5-dimension rubric in `data/benchmark/manual_review_rubric.md` for all 20 benchmark responses to establish formal pedagogical validation.
