---
title: DocInsight
emoji: 🔍
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# AI-Powered Domain-Specific Insights Assistant

A production-quality **Retrieval-Augmented Generation (RAG)** system that extracts structured insights from large domain-specific document corpora. Powered by HuggingFace sentence-transformers (local embeddings), FAISS vector search, LangChain, and Groq LLaMA-3.

---

## Architecture

```
Next.js Frontend (Vercel)
        │  REST (JSON + multipart)
        ▼
FastAPI Backend (HuggingFace Spaces / Docker)
        │
        ├── POST /api/ingest   ──► pipelines/ (load → normalize → chunk) ──► FAISS index
        │
        └── POST /api/query    ──► core/query_engine.py (Groq LLaMA-3) ──► Structured JSON
                                         │
                                         └── core/explainability.py (citations)
```

---

## Features

| Feature                           | Detail                                            |
| --------------------------------- | ------------------------------------------------- |
| **Multi-format ingestion**        | PDF, DOCX, CSV/XLSX, JSON, TXT/MD                 |
| **Multi-domain indexing**         | Separate FAISS index per domain                   |
| **Structured insight extraction** | Returns `answer`, `key_insights[]`, `confidence`  |
| **Source attribution**            | Cites source file, page number, and excerpt       |
| **Demo domain**                   | Auto-ingested from `data/sample_docs/` on startup |
| **Next.js frontend**              | Chat + Upload tabs, dark sidebar, Tailwind CSS    |

---

## Local Development

### 1. Backend

```bash
# Clone and enter the repo
git clone https://github.com/ss7227-Developer/insight-assistant.git
cd insight-assistant

# Install Python dependencies
pip install -r requirements.txt

# Set up credentials
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Run the FastAPI server
uvicorn app:app --reload --port 7860
```

The server auto-ingests `data/sample_docs/` into the **demo** domain on first startup.
Visit `http://localhost:7860/docs` for the interactive API docs.

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure backend URL
cp .env.example .env.local
# .env.local already points to http://localhost:7860 — no changes needed for local dev

# Start the dev server
npm run dev
```

Open `http://localhost:3000`.

---

## HuggingFace Spaces Deployment (Backend)

HuggingFace Spaces supports Docker-based deployments that expose port 7860.

1. Create a new Space at [huggingface.co/spaces](https://huggingface.co/spaces):
   - **SDK:** Docker
   - **Hardware:** CPU Basic (free tier works; upgrade for faster embedding)

2. Add your secret in the Space settings:
   - `GROQ_API_KEY` → your Groq API key

3. Push the repo to the Space:

```bash
# Add the Space as a remote (replace <username> and <space-name>)
git remote add space https://huggingface.co/spaces/<username>/<space-name>
git push space master
```

HuggingFace will build the Dockerfile and start the server. The first build downloads the `all-MiniLM-L6-v2` model (~90 MB) — subsequent starts use the cached layer.

4. Your backend URL will be:
   `https://<username>-<space-name>.hf.space`

---

## Vercel Deployment (Frontend)

1. Push the entire repo to GitHub (the `frontend/` folder is inside the repo).

2. Import the repo in [vercel.com/new](https://vercel.com/new):
   - **Framework Preset:** Next.js
   - **Root Directory:** `frontend`

3. Add an environment variable in the Vercel dashboard:
   - `NEXT_PUBLIC_BACKEND_URL` → `https://<username>-<space-name>.hf.space`

4. Deploy. Vercel detects `next.config.js` and builds automatically.

---

## Connecting Frontend to Backend

The only configuration needed is `NEXT_PUBLIC_BACKEND_URL`:

| Environment | Value                                             |
| ----------- | ------------------------------------------------- |
| Local dev   | `http://localhost:7860` (default in `.env.local`) |
| Production  | `https://<username>-<space-name>.hf.space`        |

Set this in `frontend/.env.local` for local dev, or as a Vercel environment variable for production.

---

## Project Structure

```
Insight_Assistant/
├── app.py                          # FastAPI backend (4 endpoints)
├── config.py                       # Centralized config
├── requirements.txt
├── .env.example
├── Dockerfile                      # For HuggingFace Spaces
├── data/sample_docs/               # Demo documents (auto-ingested on startup)
│   ├── transformer_architectures.txt
│   ├── rag_systems.txt
│   └── llm_evaluation.txt
├── pipelines/
│   ├── document_loader.py
│   ├── text_normalizer.py
│   └── chunker.py
├── core/
│   ├── embeddings.py               # HuggingFace all-MiniLM-L6-v2 (local)
│   ├── vector_store.py             # FAISS index management
│   ├── query_engine.py             # Groq LLaMA-3 RAG chain
│   └── explainability.py          # Citations + relevance scoring
├── evaluation/
│   ├── metrics.py
│   ├── benchmark_runner.py
│   └── ground_truth/sample_qa.json
├── tests/
└── frontend/                       # Next.js 14 App Router
    ├── app/
    │   ├── page.tsx
    │   ├── layout.tsx
    │   └── globals.css
    ├── components/
    │   ├── ChatView.tsx
    │   ├── UploadView.tsx
    │   ├── MessageBubble.tsx
    │   └── DomainSelector.tsx
    ├── lib/api.ts
    ├── next.config.js
    ├── tailwind.config.ts
    └── package.json
```

---

## API Reference

| Method | Endpoint       | Description                                          |
| ------ | -------------- | ---------------------------------------------------- |
| GET    | `/api/health`  | Liveness check                                       |
| GET    | `/api/domains` | List indexed domains                                 |
| POST   | `/api/ingest`  | Multipart: `domain` (string) + `files` (one or more) |
| POST   | `/api/query`   | JSON `{ question, domain }` → structured answer      |

Full interactive docs at `http://localhost:7860/docs` when running locally.

---

## Configuration

Edit `config.py` to change:

| Setting         | Default | Description                   |
| --------------- | ------- | ----------------------------- |
| `GROQ_API_KEY`  | env var | Your Groq API key             |
| `CHUNK_SIZE`    | `800`   | Characters per chunk          |
| `CHUNK_OVERLAP` | `150`   | Overlap between chunks        |
| `RETRIEVER_K`   | `5`     | Documents retrieved per query |

---

## Run Tests

```bash
pytest tests/ -v
```
