"""
text_normalizer.py
Cleans and deduplicates LangChain Documents before chunking.
- Strips excess whitespace and normalizes unicode
- Removes duplicate documents by SHA-256 content hash
- Preserves all metadata
"""

import hashlib
import re
import unicodedata

from langchain_core.documents import Document


def normalize(docs: list[Document]) -> list[Document]:
    """
    Clean and deduplicate documents.
    Returns a new list with cleaned content and no exact duplicates.
    """
    seen_hashes: set[str] = set()
    cleaned: list[Document] = []

    for doc in docs:
        text = _clean_text(doc.page_content)
        if not text:
            continue

        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if content_hash in seen_hashes:
            continue

        seen_hashes.add(content_hash)
        cleaned.append(Document(page_content=text, metadata=doc.metadata))

    return cleaned


def _clean_text(text: str) -> str:
    # Normalize unicode (NFC form)
    text = unicodedata.normalize("NFC", text)

    # Replace smart quotes and dashes with ASCII equivalents
    replacements = {
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-",
        "\u00a0": " ",  # non-breaking space
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)

    # Collapse multiple blank lines to at most two
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse horizontal whitespace runs (spaces/tabs) to a single space
    text = re.sub(r"[ \t]+", " ", text)

    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)

    return text.strip()
