"""The conftest isolation fixture keeps real keys out of unit tests."""

import os

from tests.conftest import PLACEHOLDER_API_KEY


def test_set_api_keys_are_replaced_with_a_placeholder():
    for name, value in os.environ.items():
        if name.endswith("_API_KEY") and value:
            assert value == PLACEHOLDER_API_KEY, name


def test_monkeypatch_inside_a_test_still_wins(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert os.environ["OPENAI_API_KEY"] == "test-key"
