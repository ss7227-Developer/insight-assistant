"""
query_engine.py
Builds the RAG chain and runs queries using Groq + FAISS retrieval.
The LLM is prompted to return a structured JSON response with:
  answer, key_insights, confidence (high|medium|low)
"""

import json
import re
from dataclasses import dataclass

import groq as groq_sdk
from langchain_core.documents import Document

import config
from core.vector_store import load_index

_SYSTEM_PROMPT_BASE = (
    "You are an AI assistant that extracts structured insights from domain-specific documents. "
    "Answer ONLY based on the provided context. Do NOT fabricate information. "
    "Respond with valid JSON in this exact format:\n"
    '{\n'
    '  "answer": "<concise answer to the question>",\n'
    '  "key_insights": ["<insight 1>", "<insight 2>", "<insight 3>"],\n'
    '  "confidence": "<high|medium|low>"\n'
    '}\n\n'
    "Context:\n"
)


@dataclass
class _Chain:
    """Lightweight container holding a loaded FAISS vector store."""
    vector_store: object
    domain: str


def create_chain(domain: str) -> _Chain:
    """
    Load the FAISS index for the given domain and return a chain object.
    Signature kept identical to the original so callers are unchanged.
    """
    vector_store = load_index(domain)
    return _Chain(vector_store=vector_store, domain=domain)


def query(chain: _Chain, question: str, k: int = config.RETRIEVER_K) -> dict:
    """
    Run a question through the RAG pipeline.

    Returns:
        {
            "answer": str,
            "key_insights": list[str],
            "confidence": str,
            "source_docs": list[Document],
            "raw_response": str,
        }
    """
    # 1. Retrieve relevant chunks
    retriever = chain.vector_store.as_retriever(search_kwargs={"k": k})
    source_docs: list[Document] = retriever.invoke(question)

    # 2. Build context string
    context = "\n\n".join(doc.page_content for doc in source_docs)

    # 3. Call Groq
    client = groq_sdk.Groq(api_key=config.GROQ_API_KEY)
    system_msg = _SYSTEM_PROMPT_BASE + context
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": question},
        ],
        temperature=0.1,
        max_tokens=600,
    )
    raw = response.choices[0].message.content or ""

    parsed = _parse_response(raw)
    parsed["source_docs"] = source_docs
    parsed["raw_response"] = raw
    return parsed


def _parse_response(raw: str) -> dict:
    """Extract JSON from LLM output, falling back gracefully."""
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            return {
                "answer": data.get("answer", raw),
                "key_insights": data.get("key_insights", []),
                "confidence": data.get("confidence", "medium"),
            }
        except json.JSONDecodeError:
            pass

    return {"answer": raw, "key_insights": [], "confidence": "low"}
