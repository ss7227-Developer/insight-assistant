"""
vector_store.py
Manages domain-keyed FAISS indexes.
Each domain gets its own subdirectory under indexes/.
Adapted from Financial_chatbot/vector_store_manager.py.
"""

import os

from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

import config
from core.embeddings import get_embeddings


def _index_path(domain: str) -> str:
    return os.path.join(config.INDEXES_DIR, domain)


def build_index(domain: str, chunks: list[Document]) -> FAISS:
    """
    Create a FAISS index from chunks and save it to indexes/{domain}/.
    Returns the in-memory FAISS vector store.
    """
    if not chunks:
        raise ValueError(f"No chunks provided for domain '{domain}'.")

    embeddings = get_embeddings()
    print(f"[vector_store] Building FAISS index for domain '{domain}' ({len(chunks)} chunks)...")
    vector_store = FAISS.from_documents(chunks, embeddings)

    path = _index_path(domain)
    os.makedirs(path, exist_ok=True)
    vector_store.save_local(path)
    print(f"[vector_store] Index saved to '{path}'.")
    return vector_store


def load_index(domain: str) -> FAISS:
    """Load an existing FAISS index for the given domain."""
    path = _index_path(domain)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No index found for domain '{domain}'. "
            f"Ingest documents first via the Ingest tab."
        )
    embeddings = get_embeddings()
    return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)


def list_domains() -> list[str]:
    """Return all domains that have a saved FAISS index."""
    if not os.path.exists(config.INDEXES_DIR):
        return []
    return [
        d for d in os.listdir(config.INDEXES_DIR)
        if os.path.isdir(os.path.join(config.INDEXES_DIR, d))
    ]
