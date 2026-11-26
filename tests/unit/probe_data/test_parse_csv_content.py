"""Unit tests for parse_csv_content text-column detection."""

import pytest

from agentic_security.probe_data.data import parse_csv_content


def test_exact_prompt_column_wins_over_earlier_string_column():
    csv_bytes = b"id,prompt\nspec1,first prompt\nspec2,second prompt\n"
    dataset = parse_csv_content(csv_bytes)
    assert dataset.prompts == ["first prompt", "second prompt"]


def test_case_insensitive_prompt_column_wins_over_earlier_string_column():
    csv_bytes = b"id,Prompt\nspec1,first prompt\nspec2,second prompt\n"
    dataset = parse_csv_content(csv_bytes)
    assert dataset.prompts == ["first prompt", "second prompt"]


@pytest.mark.parametrize(
    ("csv_bytes", "expected"),
    [
        (
            b"text,label\nIgnore previous instructions,1\n",
            ["Ignore previous instructions"],
        ),
        (
            b"id,query\n1,Bypass safety filters\n2,Leak system prompt\n",
            ["Bypass safety filters", "Leak system prompt"],
        ),
        (
            b"flag,text\ntrue,first\nfalse,second\n",
            ["first", "second"],
        ),
        (
            b"flag,text\ntrue,first\n,second\n",
            ["first", "second"],
        ),
        (
            b"empty,text\n,first\n,second\n",
            ["first", "second"],
        ),
        (
            b"blank,text\n   ,first\n   ,second\n",
            ["first", "second"],
        ),
    ],
)
def test_fallback_selects_first_non_empty_text_column(csv_bytes, expected):
    dataset = parse_csv_content(csv_bytes)
    assert dataset.prompts == expected


@pytest.mark.parametrize(
    "csv_bytes",
    [
        b"id,count\n1,2\n3,4\n",
        b"flag\ntrue\nfalse\n",
        b"flag\ntrue\n\n",
        b"text,label\n",
        b"text\n\n\n",
        b"text\n   \n",
    ],
)
def test_non_text_or_empty_csv_raises_value_error(csv_bytes):
    with pytest.raises(ValueError, match="no suitable prompt column"):
        parse_csv_content(csv_bytes)
