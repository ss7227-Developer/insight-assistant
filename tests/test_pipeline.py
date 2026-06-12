"""
test_pipeline.py
Unit tests for the data ingestion pipeline.
No AWS credentials required — tests run fully offline.
"""

import os
import tempfile

import pytest

from pipelines.document_loader import load_documents
from pipelines.text_normalizer import normalize
from pipelines.chunker import chunk_documents


# ── Fixtures ────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_txt_dir():
    """Create a temp directory with sample .txt and .csv files."""
    with tempfile.TemporaryDirectory() as tmp:
        txt_path = os.path.join(tmp, "report.txt")
        with open(txt_path, "w") as f:
            f.write("This is a sample financial report.\n\nRevenue grew by 20% YoY.")

        csv_path = os.path.join(tmp, "data.csv")
        with open(csv_path, "w") as f:
            f.write("product,revenue,growth\n")
            f.write("widget_A,1000000,0.20\n")
            f.write("widget_B,500000,0.05\n")

        yield tmp


# ── document_loader tests ────────────────────────────────────────────────────────

def test_load_txt_documents(sample_txt_dir):
    docs = load_documents(sample_txt_dir, domain="test")
    txt_docs = [d for d in docs if d.metadata["file_type"] == "txt"]
    assert len(txt_docs) == 1
    assert "financial report" in txt_docs[0].page_content


def test_load_csv_documents(sample_txt_dir):
    docs = load_documents(sample_txt_dir, domain="test")
    csv_docs = [d for d in docs if d.metadata["file_type"] == "csv"]
    # 2 data rows → 2 Documents
    assert len(csv_docs) == 2
    assert "product: widget_A" in csv_docs[0].page_content


def test_document_metadata(sample_txt_dir):
    docs = load_documents(sample_txt_dir, domain="test_domain")
    for doc in docs:
        assert doc.metadata["domain"] == "test_domain"
        assert "source" in doc.metadata
        assert "ingested_at" in doc.metadata


# ── text_normalizer tests ────────────────────────────────────────────────────────

def test_normalize_removes_duplicates(sample_txt_dir):
    docs = load_documents(sample_txt_dir, domain="test")
    # Double the docs to create duplicates
    doubled = docs + docs
    result = normalize(doubled)
    assert len(result) == len(docs)


def test_normalize_cleans_whitespace():
    from langchain_core.documents import Document

    dirty = Document(page_content="  Hello   World  \n\n\n\n  Goodbye  ", metadata={})
    result = normalize([dirty])
    assert len(result) == 1
    assert "  " not in result[0].page_content  # no double spaces
    # Should have at most 2 consecutive newlines
    assert "\n\n\n" not in result[0].page_content


# ── chunker tests ────────────────────────────────────────────────────────────────

def test_chunk_documents_output_count(sample_txt_dir):
    docs = load_documents(sample_txt_dir, domain="test")
    docs = normalize(docs)
    chunks = chunk_documents(docs, chunk_size=100, chunk_overlap=20)
    assert len(chunks) >= len(docs)  # at least one chunk per doc


def test_chunk_metadata_inherited(sample_txt_dir):
    docs = load_documents(sample_txt_dir, domain="test")
    chunks = chunk_documents(docs, chunk_size=200, chunk_overlap=20)
    for chunk in chunks:
        assert "domain" in chunk.metadata
        assert "chunk_id" in chunk.metadata
        assert "source" in chunk.metadata


def test_chunk_size_respected(sample_txt_dir):
    docs = load_documents(sample_txt_dir, domain="test")
    txt_docs = [d for d in docs if d.metadata["file_type"] == "txt"]
    chunks = chunk_documents(txt_docs, chunk_size=50, chunk_overlap=5)
    for chunk in chunks:
        # Allow slight overflow due to splitter behaviour, but not 2x
        assert len(chunk.page_content) <= 100
