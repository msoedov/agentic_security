from agentic_security.http_spec import LLMSpec, parse_http_spec


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
