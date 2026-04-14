"""
query_engine.py
Builds the LangChain RAG chain and runs queries.
The LLM is prompted to return a structured JSON response with:
  answer, key_insights, confidence (high|medium|low)
Adapted from Financial_chatbot/query_assistant.py.
"""

import json
import re

import boto3
from langchain_community.llms import Bedrock
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.docstore.document import Document

import config
from core.vector_store import load_index

_SYSTEM_PROMPT = (
    "You are an AI assistant that extracts structured insights from domain-specific documents. "
    "Answer ONLY based on the provided context. Do NOT fabricate information. "
    "Respond with valid JSON in this exact format:\n"
    '{{\n'
    '  "answer": "<concise answer to the question>",\n'
    '  "key_insights": ["<insight 1>", "<insight 2>", "<insight 3>"],\n'
    '  "confidence": "<high|medium|low>"\n'
    '}}\n\n'
    "Context:\n{context}"
)


def create_chain(domain: str):
    """
    Load the FAISS index for the given domain and return a LangChain retrieval chain.
    The chain expects input dict: {input: str} and returns {answer: str, context: list[Document]}.
    """
    vector_store = load_index(domain)

    session = boto3.Session(
        region_name=config.AWS_REGION,
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
    )
    bedrock_client = session.client(service_name="bedrock-runtime")

    llm = Bedrock(
        client=bedrock_client,
        model_id=config.LLM_MODEL_ID,
        model_kwargs={"temperature": 0.1, "maxTokenCount": 600},
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", _SYSTEM_PROMPT),
        ("human", "{input}"),
    ])

    document_chain = create_stuff_documents_chain(llm, prompt)
    retriever = vector_store.as_retriever(search_kwargs={"k": config.RETRIEVER_K})
    return create_retrieval_chain(retriever, document_chain)


def query(chain, question: str, k: int = config.RETRIEVER_K) -> dict:
    """
    Run a question through the RAG chain.

    Returns:
        {
            "answer": str,
            "key_insights": list[str],
            "confidence": str,
            "source_docs": list[Document],
            "raw_response": str,
        }
    """
    result = chain.invoke({"input": question})
    raw = result.get("answer", "")
    source_docs: list[Document] = result.get("context", [])

    parsed = _parse_response(raw)
    parsed["source_docs"] = source_docs
    parsed["raw_response"] = raw
    return parsed


def _parse_response(raw: str) -> dict:
    """Extract JSON from LLM output, falling back gracefully."""
    # Try to find a JSON block
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

    # Fallback: return raw text as the answer
    return {"answer": raw, "key_insights": [], "confidence": "low"}
