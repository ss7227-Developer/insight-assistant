"""
test_query_engine.py
Unit tests for query_engine._parse_response.
No AWS calls — the LangChain chain and Bedrock client are mocked.
"""

import json
import pytest

from core.query_engine import _parse_response


# ── _parse_response ──────────────────────────────────────────────────────────────

def test_parse_valid_json():
    raw = json.dumps({
        "answer": "Revenue increased by 20%.",
        "key_insights": ["Revenue up 20%", "Expenses stable"],
        "confidence": "high",
    })
    result = _parse_response(raw)
    assert result["answer"] == "Revenue increased by 20%."
    assert result["key_insights"] == ["Revenue up 20%", "Expenses stable"]
    assert result["confidence"] == "high"


def test_parse_json_embedded_in_text():
    raw = (
        'Here is the answer:\n'
        '{"answer": "Q3 was strong.", "key_insights": ["Strong Q3"], "confidence": "medium"}\n'
        'End of response.'
    )
    result = _parse_response(raw)
    assert result["answer"] == "Q3 was strong."
    assert result["confidence"] == "medium"


def test_parse_fallback_on_invalid_json():
    raw = "I cannot find relevant information in the provided context."
    result = _parse_response(raw)
    assert result["answer"] == raw
    assert result["key_insights"] == []
    assert result["confidence"] == "low"


def test_parse_missing_fields_uses_defaults():
    raw = '{"answer": "Partial answer."}'
    result = _parse_response(raw)
    assert result["answer"] == "Partial answer."
    assert result["key_insights"] == []
    assert result["confidence"] == "medium"


def test_parse_empty_string():
    result = _parse_response("")
    assert result["answer"] == ""
    assert result["confidence"] == "low"
