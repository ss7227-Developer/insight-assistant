"""
chunker.py
Splits normalized LangChain Documents into overlapping chunks
using RecursiveCharacterTextSplitter.
Each chunk inherits source metadata and gets a chunk_id.
"""

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

import config


def chunk_documents(
    docs: list[Document],
    chunk_size: int = config.CHUNK_SIZE,
    chunk_overlap: int = config.CHUNK_OVERLAP,
) -> list[Document]:
    """
    Split documents into overlapping chunks.
    Returns a flat list of Document chunks with metadata:
      source, domain, file_type, page_num, ingested_at, chunk_id
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    all_chunks: list[Document] = []
    for doc in docs:
        raw_chunks = splitter.create_documents(
            [doc.page_content],
            metadatas=[doc.metadata],
        )
        for i, chunk in enumerate(raw_chunks):
            chunk.metadata["chunk_id"] = f"{doc.metadata.get('source', 'doc')}_{i}"
            all_chunks.append(chunk)

    return all_chunks
