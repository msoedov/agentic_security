"""Unit tests for security module."""

import pytest
from agentic_security.core.security import (
    SecurityValidator,
    SecretManager,
    RateLimiter,
    sanitize_log_output,
)


class TestSecurityValidator:

    def test_validate_url_valid(self):
        assert SecurityValidator.validate_url("https://example.com/path")
        assert SecurityValidator.validate_url("http://api.example.com")

    def test_validate_url_invalid_scheme(self):
        assert not SecurityValidator.validate_url("ftp://example.com")
        assert not SecurityValidator.validate_url("file:///etc/passwd")

    def test_validate_url_localhost(self):
        assert not SecurityValidator.validate_url("http://localhost/api")
        assert not SecurityValidator.validate_url("http://127.0.0.1/api")
        assert not SecurityValidator.validate_url("http://0.0.0.0/api")

    def test_validate_url_private_ip(self):
        assert not SecurityValidator.validate_url("http://10.0.0.1")
        assert not SecurityValidator.validate_url("http://192.168.1.1")
        assert not SecurityValidator.validate_url("http://169.254.1.1")

    def test_validate_url_allowed_hosts(self):
        allowed = ["api.example.com"]
        assert SecurityValidator.validate_url("https://api.example.com", allowed)
        assert not SecurityValidator.validate_url("https://evil.com", allowed)

    def test_validate_url_too_long(self):
        long_url = "https://example.com/" + "a" * 3000
        assert not SecurityValidator.validate_url(long_url)

    def test_sanitize_filename(self):
        assert SecurityValidator.sanitize_filename("test.csv") == "test.csv"
        assert SecurityValidator.sanitize_filename("../../../etc/passwd") == "passwd"
        assert SecurityValidator.sanitize_filename("test/file.txt") == "file.txt"
        assert (
            SecurityValidator.sanitize_filename("file with spaces.txt")
            == "file with spaces.txt"
        )

    def test_sanitize_filename_invalid(self):
        with pytest.raises(ValueError):
            SecurityValidator.sanitize_filename(".")
        with pytest.raises(ValueError):
            SecurityValidator.sanitize_filename("..")
        with pytest.raises(ValueError):
            SecurityValidator.sanitize_filename("")

    def test_validate_file_size(self):
        assert SecurityValidator.validate_file_size(1024)
        assert SecurityValidator.validate_file_size(1024 * 1024)
        assert not SecurityValidator.validate_file_size(0)
        assert not SecurityValidator.validate_file_size(-1)
        assert not SecurityValidator.validate_file_size(20 * 1024 * 1024)

    def test_validate_csv_content(self):
        assert SecurityValidator.validate_csv_content("col1,col2\nval1,val2")
        assert not SecurityValidator.validate_csv_content("")
        assert not SecurityValidator.validate_csv_content("x" * (11 * 1024 * 1024))


class TestSecretManager:

    def test_hash_and_verify_secret(self):
        secret = "my-secret-key"
        hashed = SecretManager.hash_secret(secret)

        assert SecretManager.verify_secret(secret, hashed)
        assert not SecretManager.verify_secret("wrong-secret", hashed)

    def test_hash_secret_with_salt(self):
        secret = "my-secret"
        hashed1 = SecretManager.hash_secret(secret, "salt1")
        hashed2 = SecretManager.hash_secret(secret, "salt2")

        assert hashed1 != hashed2

    def test_verify_secret_invalid_format(self):
        assert not SecretManager.verify_secret("secret", "invalid-hash")


class TestRateLimiter:

    def test_rate_limiter_allows_requests(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)

        assert limiter.is_allowed("user1")
        assert limiter.is_allowed("user1")
        assert limiter.is_allowed("user1")

    def test_rate_limiter_blocks_excess(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        assert limiter.is_allowed("user1")
        assert limiter.is_allowed("user1")
        assert not limiter.is_allowed("user1")

    def test_rate_limiter_separate_keys(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        assert limiter.is_allowed("user1")
        assert limiter.is_allowed("user1")
        assert limiter.is_allowed("user2")
        assert limiter.is_allowed("user2")

    def test_rate_limiter_reset(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        assert limiter.is_allowed("user1")
        assert not limiter.is_allowed("user1")

        limiter.reset("user1")
        assert limiter.is_allowed("user1")


class TestSanitizeLogOutput:

    def test_sanitize_api_key(self):
        data = 'api_key="sk-1234567890"'
        result = sanitize_log_output(data)
        assert "sk-1234567890" not in result
        assert "***" in result

    def test_sanitize_token(self):
        data = "token: abc123xyz"
        result = sanitize_log_output(data)
        assert "abc123xyz" not in result

    def test_sanitize_password(self):
        data = {"password": "secret123"}
        result = sanitize_log_output(data)
        assert "secret123" not in result

    def test_sanitize_bearer_token(self):
        data = "Authorization: Bearer eyJhbGc..."
        result = sanitize_log_output(data)
        assert "eyJhbGc" not in result
        assert "Bearer ***" in result

    def test_preserves_non_sensitive(self):
        data = "user_id=123 name=John"
        result = sanitize_log_output(data)
        assert "user_id=123" in result
        assert "name=John" in result
