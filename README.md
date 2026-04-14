# AI-Powered Domain-Specific Insights Assistant

A production-quality **Retrieval-Augmented Generation (RAG)** system that extracts structured insights from large domain-specific document corpora. Built with Amazon Bedrock embeddings, FAISS vector search, and LangChain.

---

## Features

| Feature | Detail |
|---|---|
| **Multi-format ingestion** | PDF, DOCX, CSV/XLSX, JSON, TXT/MD |
| **Multi-domain indexing** | Separate FAISS index per domain, switchable at runtime |
| **Structured insight extraction** | LLM returns `answer`, `key_insights[]`, `confidence` |
| **Source attribution** | Every answer cites source file, page number, and excerpt |
| **Relevance scoring** | Cosine similarity between query and retrieved chunks |
| **Evaluation framework** | Precision@k, Recall@k, MRR, NDCG@k against ground-truth QA |
| **Streamlit UI** | Chat, Ingest, and Evaluate tabs in a single app |

---

## Architecture

```
User Query
    │
    ▼
Streamlit UI (app.py)
    │
    ├── Ingest tab ──► pipelines/ (load → normalize → chunk) ──► core/vector_store.py ──► FAISS index
    │
    ├── Chat tab   ──► core/query_engine.py ──► FAISS retriever ──► Bedrock LLM ──► Structured JSON
    │                      │
    │                      └──► core/explainability.py (citations + relevance scores)
    │
    └── Eval tab   ──► evaluation/benchmark_runner.py ──► metrics.py (P@k, R@k, MRR, NDCG)
```

---

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/ss7227-Developer/insight-assistant.git
cd insight-assistant
pip install -r requirements.txt
```

### 2. Configure AWS credentials

```bash
cp .env.example .env
# Edit .env with your AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
```

Ensure your AWS account has **Amazon Bedrock** enabled for:
- `amazon.titan-embed-text-v1` (embeddings)
- `amazon.titan-text-express-v1` (generation)

### 3. Run the app

```bash
streamlit run app.py
```

---

## Usage

### Ingest Documents
1. Open the **Ingest Documents** tab
2. Enter a domain name (e.g., `finance`, `legal`, `hr`)
3. Upload one or more files
4. Click **Ingest & Index** — documents are chunked and indexed into FAISS

### Chat with Documents
1. Open the **Chat with Documents** tab
2. Select a domain and click **Load domain**
3. Type your question — the assistant returns a structured answer with source citations

### Evaluate Retrieval
1. Edit `evaluation/ground_truth/sample_qa.json` with your questions and relevant chunk IDs
2. Open the **Evaluate Retrieval** tab
3. Select domain, set k, click **Run Benchmark**
4. View Precision@k, Recall@k, MRR, and NDCG metrics

---

## Project Structure

```
Insight_Assistant/
├── app.py                          # Streamlit frontend (3 tabs)
├── config.py                       # Centralized config (models, paths, params)
├── requirements.txt
├── .env.example
├── data/sample_docs/               # Demo documents (committed)
├── pipelines/
│   ├── document_loader.py          # Multi-format document loading
│   ├── text_normalizer.py          # Cleaning + deduplication
│   └── chunker.py                  # RecursiveCharacterTextSplitter
├── core/
│   ├── embeddings.py               # Bedrock embeddings client
│   ├── vector_store.py             # FAISS index management (per domain)
│   ├── query_engine.py             # RAG chain + structured JSON output
│   └── explainability.py          # Citations + cosine relevance scoring
├── evaluation/
│   ├── metrics.py                  # precision@k, recall@k, MRR, NDCG
│   ├── benchmark_runner.py         # Evaluation orchestration + reporting
│   └── ground_truth/
│       └── sample_qa.json          # Ground-truth QA pairs template
└── tests/
    ├── test_pipeline.py
    ├── test_evaluation.py
    └── test_query_engine.py
```

---

## Evaluation Metrics

| Metric | Formula | What it measures |
|---|---|---|
| **Precision@k** | `|retrieved[:k] ∩ relevant| / k` | Fraction of top-k results that are relevant |
| **Recall@k** | `|retrieved[:k] ∩ relevant| / |relevant|` | Fraction of all relevant docs found in top-k |
| **MRR** | `1 / rank(first relevant)` | How early the first relevant doc appears |
| **NDCG@k** | Discounted cumulative gain | Quality of the ranking, accounting for position |

---

## Run Tests

```bash
pytest tests/ -v
```

Tests are fully offline — no AWS credentials required.

---

## Configuration

Edit `config.py` to change:

| Setting | Default | Description |
|---|---|---|
| `EMBEDDING_MODEL_ID` | `amazon.titan-embed-text-v1` | Bedrock embedding model |
| `LLM_MODEL_ID` | `amazon.titan-text-express-v1` | Bedrock generation model |
| `CHUNK_SIZE` | `800` | Characters per chunk |
| `CHUNK_OVERLAP` | `150` | Overlap between consecutive chunks |
| `RETRIEVER_K` | `5` | Documents retrieved per query |
