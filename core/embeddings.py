"""
embeddings.py
Returns a HuggingFace sentence-transformers embeddings client.
Runs entirely locally — no API key required.
"""

from langchain_huggingface import HuggingFaceEmbeddings


def get_embeddings() -> HuggingFaceEmbeddings:
    """Return a local HuggingFace embeddings client."""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
