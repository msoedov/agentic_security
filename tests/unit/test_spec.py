import json

import pytest

from agentic_security.core import app as app_module
from agentic_security.http_spec import (
    InvalidHTTPSpecError,
    LLMSpec,
    escape_special_chars_for_json,
    parse_http_spec,
)
from agentic_security.routes._specs import LLM_SPECS


class TestParseHttpSpec:
    # Should correctly parse a simple HTTP spec with headers and body
    def test_parse_simple_http_spec(self):
        http_spec = (
            'GET http://example.com\nContent-Type: application/json\n\n{"key": "value"}'
        )
        expected_spec = LLMSpec(
            method="GET",
            url="http://example.com",
            headers={"Content-Type": "application/json"},
            body='{"key": "value"}',
        )
        assert parse_http_spec(http_spec) == expected_spec

    # Should correctly parse a HTTP spec with headers containing special characters
    def test_parse_http_spec_with_special_characters(self):
        http_spec = 'POST http://example.com\nX-Auth-Token: abcdefg1234567890!@#$%^&*\n\n{"key": "value"}'
        expected_spec = LLMSpec(
            method="POST",
            url="http://example.com",
            headers={"X-Auth-Token": "abcdefg1234567890!@#$%^&*"},
            body='{"key": "value"}',
        )
        assert parse_http_spec(http_spec) == expected_spec

    # Should correctly parse a spec with no headers and no body
    def test_parse_http_spec_with_no_headers_and_no_body(self):
        # Arrange
        http_spec = "GET http://example.com"

        # Act
        result = parse_http_spec(http_spec)

        # Assert
        assert result.method == "GET"
        assert result.url == "http://example.com"
        assert result.headers == {}
        assert result.body == ""

    def test_parse_http_spec_with_headers_no_body(self):
        # Arrange
        http_spec = "GET http://example.com\nContent-Type: application/json\n\n"

        # Act
        result = parse_http_spec(http_spec)

        # Assert
        assert result.method == "GET"
        assert result.url == "http://example.com"
        assert result.headers == {"Content-Type": "application/json"}
        assert result.body == ""

    def test_parse_http_spec_rejects_malformed_header(self):
        http_spec = "GET http://example.com\nHeaderWithoutColon\n\n"

        with pytest.raises(InvalidHTTPSpecError, match="Invalid header line"):
            parse_http_spec(http_spec)

    def test_parse_http_spec_trims_header_whitespace(self):
        http_spec = "GET http://example.com\nAuthorization:Bearer token\n\n"

        result = parse_http_spec(http_spec)

        assert result.headers == {"Authorization": "Bearer token"}


class TestLLMSpec:
    def test_validate_raises_error_for_missing_files(self):
        spec = LLMSpec(
            method="POST", url="http://example.com", headers={}, body="", has_files=True
        )
        with pytest.raises(ValueError, match="Files are required for this request."):
            spec.validate(prompt="", encoded_image="", encoded_audio="", files={})

    def test_validate_raises_error_for_missing_image(self):
        spec = LLMSpec(
            method="POST", url="http://example.com", headers={}, body="", has_image=True
        )
        with pytest.raises(ValueError, match="An image is required for this request."):
            spec.validate(prompt="", encoded_image="", encoded_audio="", files={})


class TestEscapeSpecialCharsForJson:
    @pytest.mark.parametrize(
        "prompt",
        [
            'say "hi"',
            "back\\slash",
            "line1\nline2\r\n\ttabbed",
            "backspace\x08 formfeed\x0c",
            "ansi \x1b[31mred\x1b[0m",
            "nul\x00byte and unit separator\x1f",
            "unicode café 日本語 \U0001f600",
        ],
    )
    def test_escaped_prompt_round_trips_through_json(self, prompt):
        body = '{"prompt": "%s"}' % escape_special_chars_for_json(prompt)
        assert json.loads(body)["prompt"] == prompt

    def test_keeps_non_ascii_text_unescaped(self):
        assert escape_special_chars_for_json("café") == "café"


class TestParseHttpSpecSecretExpansion:
    @pytest.fixture(autouse=True)
    def isolated_secrets(self, monkeypatch):
        monkeypatch.setattr(app_module, "_secrets", {})

    def test_expands_openai_preset_url_headers_and_body(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-FAKEOPENAI999")
        app_module.set_secrets(
            {"OPENAI_API_KEY": "$OPENAI_API_KEY", "API_KEY": "user:p@ss=1;2"}
        )
        entry = next(item for item in LLM_SPECS if item["name"] == "Open AI")
        preset = LLMSpec.from_string(entry["spec"])
        assert preset.headers["Authorization"] == "Bearer sk-test-FAKEOPENAI999"
        assert "<<PROMPT>>" in preset.body

        spec = parse_http_spec(
            "POST https://api.example.com/v1?key=$API_KEY\n"
            "$API_KEY: $API_KEY\n\n"
            '{"token": "$API_KEY", "prompt": "<<PROMPT>>"}'
        )
        assert spec.url == "https://api.example.com/v1?key=user:p@ss=1;2"
        assert spec.headers == {"$API_KEY": "user:p@ss=1;2"}
        assert spec.body == '{"token": "user:p@ss=1;2", "prompt": "<<PROMPT>>"}'

    def test_longest_key_boundary_and_single_pass_substitution(self):
        app_module.set_secrets(
            {"API_KEY": "sk-test-V1", "API_KEY_V2": r"tok_$API_KEY\1"}
        )
        spec = parse_http_spec(
            "POST https://api.example.com/v1/chat\n"
            "X-V1: $API_KEY\nX-V2: $API_KEY_V2\nX-Unset: $API_KEY_UNSET\n\n{}"
        )
        assert spec.headers == {
            "X-V1": "sk-test-V1",
            "X-V2": r"tok_$API_KEY\1",
            "X-Unset": "$API_KEY_UNSET",
        }

    def test_skips_non_string_secrets_and_redacts_invalid_url_errors(self, monkeypatch):
        monkeypatch.setattr(
            app_module,
            "_secrets",
            {
                "MISSING": None,
                "EMPTY": "",
                "PORT": 8080,
                "$": "x",
                "KEY": "sk-test-FAKEOK",
            },
        )
        spec = parse_http_spec(
            "POST https://api.example.com/v1/chat\n"
            "X-Missing: $MISSING\nX-Port: $PORT\nAuthorization: Bearer $KEY\n\n"
            '{"missing": "$MISSING", "empty": "$EMPTY"}'
        )
        assert spec.headers == {
            "X-Missing": "$MISSING",
            "X-Port": "$PORT",
            "Authorization": "Bearer sk-test-FAKEOK",
        }
        assert spec.body == '{"missing": "$MISSING", "empty": "$EMPTY"}'

        with pytest.raises(InvalidHTTPSpecError) as exc_info:
            parse_http_spec("POST ftp://api.example.com/v1?key=$KEY\n\n{}")
        assert "sk-test-FAKEOK" not in str(exc_info.value)
