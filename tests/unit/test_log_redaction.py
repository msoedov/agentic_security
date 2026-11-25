"""Credentials never reach the log output.

Users hand the scanner HTTP specs and dataset URLs that carry keys, and
httpx errors repeat the full URL. logutils masks secret-looking values in
every record before the rich handler prints it.
"""

import logging

import httpx
import pytest

from agentic_security import logutils
from agentic_security.logutils import MASK, RedactSecrets, redact

KEY = "sk-test-FAKEKEY-0123456789abcdef"


@pytest.mark.parametrize(
    "text,secret",
    [
        (f"GET https://api.example.com/v1?api_key={KEY}&q=1", KEY),
        ("GET https://example.com/data.csv?token=abc123def456", "abc123def456"),
        ("https://example.com/?client_secret=s3cr3tvalue", "s3cr3tvalue"),
        ("Authorization: Bearer abcdefgh12345678", "abcdefgh12345678"),
        ('{"x-api-key": "0123456789abcdef"}', "0123456789abcdef"),
        (f"loaded key {KEY} from env", KEY),
        ("anthropic sk-ant-api03-AAAAAAAAAAAAAAAA", "sk-ant-api03-AAAAAAAAAAAAAAAA"),
        ("hf token hf_ABCDEFGHIJKLMNOPQRST", "hf_ABCDEFGHIJKLMNOPQRST"),
        ("aws AKIAABCDEFGHIJKLMNOP", "AKIAABCDEFGHIJKLMNOP"),
    ],
)
def test_redact_masks_secrets(text, secret):
    cleaned = redact(text)
    assert secret not in cleaned
    assert MASK in cleaned


@pytest.mark.parametrize(
    "text",
    [
        "Loading CSV from URL: https://example.com/prompts.csv?page=2",
        "Authorization: Bearer XXXXX",  # the shipped placeholder spec
        "Scanning module AgenticBackend on port 8718",
        "The model said: I cannot help with that.",
    ],
)
def test_ordinary_lines_pass_unchanged(text):
    assert redact(text) == text


def _record(msg, *args, exc_info=None):
    return logging.LogRecord("t", logging.INFO, __file__, 1, msg, args, exc_info)


def test_filter_rewrites_formatted_message():
    record = _record("fetching %s", f"https://example.com/?apikey={KEY}")
    assert RedactSecrets().filter(record) is True
    assert KEY not in record.getMessage()


def test_filter_masks_exception_text():
    try:
        raise httpx.ConnectError(f"failed https://example.com/?api_key={KEY}")
    except httpx.ConnectError:
        import sys

        record = _record("request failed", exc_info=sys.exc_info())
    RedactSecrets().filter(record)
    assert KEY not in (record.exc_text or "")


def test_rich_handler_carries_the_filter():
    root = logging.getLogger(logutils.LOGGER_NAME)
    assert any(isinstance(f, RedactSecrets) for h in root.handlers for f in h.filters)


def test_http_client_loggers_stay_quiet():
    for name in ("httpx", "httpcore"):
        assert logging.getLogger(name).getEffectiveLevel() >= logging.WARNING
