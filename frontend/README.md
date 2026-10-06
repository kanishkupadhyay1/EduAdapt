# EduAdapt Frontend

Clean, academic, non-agentic user interface for the **EduAdapt** Adaptive Learning Platform (Programming for Problem Solving - PPS).

Designed to communicate directly with the existing EduAdapt backend API without introducing agents, multi-agent frameworks, complex UI libraries, or extraneous dependencies.

---

## Features

- **Academic Minimalist Design**: White background, high-contrast typography, semantic borders, and zero emojis/gradients.
- **Two-Column Dashboard**: Left column for Student Twin Profile & Session Controls; right column for Generated Learning Sessions.
- **Full Contract Coverage**: Renders all 10 response elements:
  1. Student Twin Profile (`student`)
  2. Canonical Profile (`profile`)
  3. Curriculum Context / RAG Slides (`curriculum`)
  4. Personalized Teaching & Code Blocks (`teaching`)
  5. Post-Learning Assessment & Quiz Viewer (`assessment`)
  6. Formative Code Feedback (`feedback`)
  7. Updated Learning Twin State (`learning_state`)
  8. Milestone Roadmap (`roadmap`)
  9. Verification & Code Execution Safety (`verification`)
  10. WCAG Accessibility & Screen Reader Transcript (`accessibility`)
- **Copyable C Code Snippets**: Monospace display with clipboard copy integration (no in-browser execution).

---

## Environment Configuration

Configure the backend API URL using `VITE_API_BASE_URL`.

A template is provided in `.env.example`:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

To configure for your local environment, copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

For production deployments (such as Vercel), set `VITE_API_BASE_URL` in the hosting dashboard to your live EduAdapt backend API endpoint (e.g. `https://api.yourdomain.com`).

---

## Getting Started

### 1. Installation

Ensure Node.js (v18+) is installed:

```bash
cd frontend
npm install
```

### 2. Development Mode

Run the local development server:

```bash
npm run dev
```

The frontend will run by default at `http://localhost:5173`.

### 3. Production Build

Build the static distribution:

```bash
npm run build
```

The optimized static assets will be output to `frontend/dist/`.

### 4. Production Preview

Preview the production build locally:

```bash
npm run preview
```

---

## Deploying to Vercel

The frontend is an isolated, standard Vite application and is 100% ready for Vercel deployment:

1. **Connect Repository**: Import the repository into Vercel.
2. **Root Directory**: Set the root directory to `frontend`.
3. **Framework Preset**: Vercel will automatically detect `Vite`.
4. **Build Command**: `npm run build` (or `vite build`).
5. **Output Directory**: `dist`.
6. **Environment Variables**:
   Add `VITE_API_BASE_URL` with your public EduAdapt backend URL.

---

## Running the Backend API

To serve the backend API locally for the frontend:

```bash
# In repository root
uvicorn eduadapt.api:app --host 0.0.0.0 --port 8000 --reload
```
