# EduAdapt: Generative AI Module

This repository contains the **Generative AI Module** for the **Programming for Problem Solving (PPS)** Adaptive Learning Platform.

---

## 📌 Project Scope & Architectural Boundaries

- **Single Generative AI Architecture**: This module employs direct prompt-engineered and model-driven generative workflows. It is **not** an agentic system and does **not** use autonomous multi-agent loops or frameworks.
- **Course Scope**: Exclusively scoped to the **Programming for Problem Solving (PPS)** C programming curriculum.
- **Module Ownership**:
  - **Owned by this Module**:
    - LLM Inference abstraction & client interfaces
    - Prompt template management
    - Personalized pedagogical content generation (concept explanations)
    - Code feedback & hint generation
    - Curriculum roadmap generation
    - Fine-tuning experiment scaffolding & evaluation
  - **Owned by Other Team Members**:
    - **RAG System**: Retrieval pipeline, embeddings, vector store
    - **Student Modeling**: Knowledge tracing, mastery estimation, profile persistence
    - **Accessibility**: Modality conversion, audio narration, assistive technology adapters

---

## 📂 Project Directory Structure

```text
EduAdapt/
├── .env.example                     # Environment variable template
├── .gitignore                        # Git exclusion rules
├── README.md                         # Project documentation
├── requirements.txt                  # Minimal essential dependencies
├── data/
│   └── mock/                         # Mock fixtures for testing & contract validation
│       ├── sample_problem.json       # Sample PPS problem fixture
│       ├── sample_rag_context.json   # Mock RAG retrieval payload
│       └── sample_student.json       # Mock student profile payload
├── src/
│   └── eduadapt/                     # Core Python package
│       ├── __init__.py
│       ├── config.py                 # Pydantic Settings & environment config
│       ├── main.py                   # Module entry point & component wiring
│       ├── inference/                # LLM client abstractions & mock clients
│       │   ├── __init__.py
│       │   └── base.py
│       ├── prompts/                  # Prompt templates & formatting
│       │   ├── __init__.py
│       │   └── templates.py
│       ├── teaching/                 # Personalized explanation generation
│       │   ├── __init__.py
│       │   └── generator.py
│       ├── feedback/                 # Code feedback & hint generation
│       │   ├── __init__.py
│       │   └── evaluator.py
│       ├── roadmap/                  # Learning roadmap generation
│       │   ├── __init__.py
│       │   └── planner.py
│       ├── training/                 # Fine-tuning & evaluation scaffolding
│       │   ├── __init__.py
│       │   └── pipeline.py
│       └── interfaces/               # Team member contract interfaces
│           ├── __init__.py
│           ├── rag.py                # External RAG contract
│           ├── student_model.py      # External Student Modeling contract
│           └── accessibility.py      # External Accessibility contract
└── tests/
    ├── __init__.py
    └── test_smoke.py                 # Unit and smoke test suite
```

---

## ⚙️ Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Adjust environment variables in `.env` as needed:
   - `LLM_PROVIDER`: Default `mock` (no API key or downloads required for setup).
   - `LLM_MODEL_NAME`: Name of the target model (default: `mock-pps-model`).
   - `APP_ENV`: `development`, `testing`, or `production`.

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Smoke Tests
```bash
python -m pytest tests/ -v
```

### 3. Run the Application Entry Point
```bash
python -m eduadapt.main
```
*(Make sure `src/` is in `PYTHONPATH`, e.g., via `set PYTHONPATH=src` or `export PYTHONPATH=src`)*
