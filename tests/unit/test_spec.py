import pytest

from agentic_security.http_spec import (
    InvalidHTTPSpecError,
    LLMSpec,
    parse_http_spec,
)


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
