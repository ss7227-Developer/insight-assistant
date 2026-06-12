"""
explainability.py
Provides source attribution and relevance scoring for RAG outputs.
- build_citations: extracts human-readable source references from retrieved docs
- score_relevance: cosine similarity between query and each retrieved doc
"""

import numpy as np
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings


def build_citations(source_docs: list[Document]) -> list[dict]:
    """
    Build a list of citation dicts from the retrieved source documents.

    Each citation contains:
        source:   filename the chunk came from
        domain:   document domain
        page_num: page number (if applicable, else None)
        excerpt:  first 200 characters of the chunk
    """
    citations = []
    seen = set()

    for doc in source_docs:
        meta = doc.metadata
        key = (meta.get("source"), meta.get("chunk_id"))
        if key in seen:
            continue
        seen.add(key)

        citations.append({
            "source": meta.get("source", "unknown"),
            "domain": meta.get("domain", ""),
            "page_num": meta.get("page_num"),
            "excerpt": doc.page_content[:200].replace("\n", " "),
        })

    return citations


def score_relevance(
    query: str,
    docs: list[Document],
    embeddings: Embeddings,
) -> list[float]:
    """
    Compute cosine similarity between the query embedding and each document embedding.
    Returns a list of floats in [0, 1], one per document.
    """
    if not docs:
        return []

    texts = [doc.page_content for doc in docs]
    all_texts = [query] + texts

    try:
        all_embeddings = embeddings.embed_documents(all_texts)
    except Exception as e:
        print(f"[explainability] Relevance scoring failed: {e}")
        return [0.0] * len(docs)

    query_vec = np.array(all_embeddings[0])
    scores = []
    for doc_vec in all_embeddings[1:]:
        doc_vec = np.array(doc_vec)
        cosine = _cosine_similarity(query_vec, doc_vec)
        scores.append(round(float(cosine), 4))

    return scores


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
