"""
app.py
FastAPI backend for the AI-Powered Domain-Specific Insights Assistant.

Endpoints (no authentication required):
  GET  /api/health
  GET  /api/domains
  POST /api/ingest
  POST /api/query

Session isolation:
  Every browser session generates a UUID on page load and sends it as
  X-Session-ID on every request.  Uploaded domains are stored as
  "{session_id}__{domain}" so they are invisible to any other session.
  The "demo" domain has no prefix and is visible to everyone.
  Session indexes older than 24 hours are purged on startup.
"""

import os
import shutil
import tempfile
import time
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pipelines.document_loader import load_documents
from pipelines.text_normalizer import normalize
from pipelines.chunker import chunk_documents
from core.vector_store import build_index, load_index, list_domains
from core.query_engine import create_chain, query
from core.explainability import build_citations

# ── Constants ─────────────────────────────────────────────────────────────────────

_PUBLIC_DOMAINS = {"demo"}
_SESSION_INDEX_MAX_AGE = 24 * 3600  # seconds


# ── Domain helpers ────────────────────────────────────────────────────────────────

def _storage_key(session_id: str, domain: str) -> str:
    return f"{session_id}__{domain}"


def _session_domains(session_id: str) -> list[str]:
    """Domains visible in this session: public ones + session-specific ones."""
    all_stored = set(list_domains())
    result = [pd for pd in _PUBLIC_DOMAINS if pd in all_stored]
    prefix = f"{session_id}__"
    for d in all_stored:
        if d.startswith(prefix):
            result.append(d[len(prefix):])
    return sorted(result)


def _resolve_key(session_id: str, domain: str) -> str:
    if domain in _PUBLIC_DOMAINS:
        return domain
    return _storage_key(session_id, domain)


# ── Startup tasks ─────────────────────────────────────────────────────────────────

def _ingest_demo() -> None:
    demo_dir = os.path.join("data", "sample_docs")
    if not os.path.isdir(demo_dir):
        print("[startup] data/sample_docs/ not found — skipping demo ingestion.")
        return
    if "demo" in list_domains():
        print("[startup] 'demo' domain already indexed — skipping.")
        return
    print("[startup] Ingesting data/sample_docs/ into 'demo' domain...")
    try:
        docs = load_documents(demo_dir, domain="demo")
        docs = normalize(docs)
        chunks = chunk_documents(docs)
        build_index("demo", chunks)
        print(f"[startup] Demo domain ready ({len(chunks)} chunks).")
    except Exception as exc:
        print(f"[startup] Demo ingestion failed: {exc}")


def _cleanup_old_sessions() -> None:
    """Delete session-specific indexes older than 24 hours."""
    indexes_dir = "indexes"
    if not os.path.exists(indexes_dir):
        return
    cutoff = time.time() - _SESSION_INDEX_MAX_AGE
    removed = 0
    for name in os.listdir(indexes_dir):
        if "__" not in name:
            continue  # public domain — leave it
        path = os.path.join(indexes_dir, name)
        if os.path.isdir(path) and os.path.getmtime(path) < cutoff:
            shutil.rmtree(path, ignore_errors=True)
            removed += 1
    if removed:
        print(f"[startup] Cleaned up {removed} expired session index(es).")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _cleanup_old_sessions()
    _ingest_demo()
    yield


# ── App ───────────────────────────────────────────────────────────────────────────

app = FastAPI(title="Insights Assistant API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ───────────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    domain: str


class CitationOut(BaseModel):
    source: str
    domain: str
    page_num: int | None
    excerpt: str


class QueryResponse(BaseModel):
    answer: str
    key_insights: List[str]
    confidence: str
    citations: List[CitationOut]


# ── Routes ────────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/domains")
def domains(x_session_id: str = Header(default="anonymous")):
    return {"domains": _session_domains(x_session_id)}


@app.post("/api/ingest")
async def ingest(
    domain: str = Form(...),
    files: List[UploadFile] = File(...),
    x_session_id: str = Header(default="anonymous"),
):
    domain = domain.strip().lower()
    if not domain:
        raise HTTPException(status_code=422, detail="domain must not be empty")
    if domain in _PUBLIC_DOMAINS:
        raise HTTPException(status_code=400, detail=f"'{domain}' is a reserved domain name")
    if not files:
        raise HTTPException(status_code=422, detail="at least one file required")

    storage_key = _storage_key(x_session_id, domain)

    with tempfile.TemporaryDirectory() as tmp_dir:
        for uf in files:
            dest = os.path.join(tmp_dir, uf.filename)
            content = await uf.read()
            with open(dest, "wb") as f:
                f.write(content)

        docs = load_documents(tmp_dir, domain=domain)
        if not docs:
            raise HTTPException(status_code=422, detail="no extractable content in uploaded files")

        docs = normalize(docs)
        chunks = chunk_documents(docs)

        try:
            build_index(storage_key, chunks)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"indexing failed: {exc}")

    return {"domain": domain, "files_ingested": len(files), "chunks_indexed": len(chunks)}


@app.post("/api/query", response_model=QueryResponse)
def query_endpoint(
    req: QueryRequest,
    x_session_id: str = Header(default="anonymous"),
):
    storage_key = _resolve_key(x_session_id, req.domain)
    if storage_key not in list_domains():
        raise HTTPException(status_code=404, detail=f"domain '{req.domain}' not found")

    try:
        chain = create_chain(storage_key)
        result = query(chain, req.question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    citations = [
        CitationOut(
            source=c["source"],
            domain=c.get("domain", ""),
            page_num=c.get("page_num"),
            excerpt=c["excerpt"],
        )
        for c in build_citations(result["source_docs"])
    ]

    return QueryResponse(
        answer=result["answer"],
        key_insights=result["key_insights"],
        confidence=result["confidence"],
        citations=citations,
    )
