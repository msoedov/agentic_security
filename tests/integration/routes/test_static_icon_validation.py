"""Tests for the /icons/{icon_name} allowlist and path-containment guard (CWE-22)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agentic_security.routes.static import ICON_NAME_RE, router

_app = FastAPI()
_app.include_router(router)
_client = TestClient(_app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# ICON_NAME_RE unit tests — no HTTP round-trip needed
# ---------------------------------------------------------------------------


class TestIconNameRegex:
    """ICON_NAME_RE rejects all names that could cause path traversal or SSRF."""

    @pytest.mark.parametrize(
        "name",
        [
            "openai.png",
            "claude-3.png",
            "gpt_4.png",
            "Anthropic.png",
            "my.icon.png",
            "test-icon-123.png",
            "A.png",
        ],
    )
    def test_valid_names_match(self, name: str):
        assert ICON_NAME_RE.fullmatch(name), f"Expected {name!r} to be accepted"

    @pytest.mark.parametrize(
        "name",
        [
            "../etc/passwd",  # classic path traversal
            "../../secret.png",  # multi-level traversal
            "foo%2Fbar.png",  # percent-encoded slash
            "foo/bar.png",  # literal slash
            "icon.PNG",  # uppercase extension (not in the dataset)
            "icon.jpg",  # wrong extension
            "icon.gif",  # wrong extension
            ".png",  # empty stem
            "",  # empty string
            "icon.png.sh",  # double extension — shell script suffix
            "\x00icon.png",  # null byte
            "icon.png\n",  # trailing newline (defeats $-anchored match)
        ],
    )
    def test_invalid_names_rejected(self, name: str):
        assert not ICON_NAME_RE.fullmatch(name), f"Expected {name!r} to be rejected"


# ---------------------------------------------------------------------------
# Integration tests — HTTP-level validation via TestClient
# ---------------------------------------------------------------------------


class TestServeIconValidation:
    """serve_icon returns 400 for names that fail the allowlist check."""

    @pytest.mark.parametrize(
        "bad_name",
        [
            "no-extension",
            "icon.jpg",
            "icon.PNG",
            ".png",
            "icon.png.sh",
        ],
    )
    def test_invalid_name_returns_400(self, bad_name: str):
        """Names that fail ICON_NAME_RE get a 400 before any FS/network I/O."""
        response = _client.get(f"/icons/{bad_name}")
        assert (
            response.status_code == 400
        ), f"Expected 400 for {bad_name!r}, got {response.status_code}"
        assert response.json().get("detail") == "Invalid icon name"

    def test_valid_name_does_not_return_400(self, tmp_path, mocker):
        """A well-formed name passes validation; 404 is acceptable when the
        upstream fetch also fails, but 400 must not be returned."""
        mocker.patch("agentic_security.routes.static.ICONS_DIR", tmp_path)

        # Stub the external HTTP call so the test is hermetic
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 404
        mocker.patch(
            "agentic_security.routes.static.requests.get", return_value=mock_resp
        )

        response = _client.get("/icons/openai.png")
        assert (
            response.status_code != 400
        ), "A valid icon name should not be rejected by the allowlist check"

    def test_valid_name_served_from_cache(self, tmp_path, mocker):
        """When the icon file already exists locally it is served directly."""
        mocker.patch("agentic_security.routes.static.ICONS_DIR", tmp_path)
        icon_file = tmp_path / "openai.png"
        icon_file.write_bytes(b"\x89PNG\r\n\x1a\n")  # minimal PNG magic bytes

        response = _client.get("/icons/openai.png")
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("image/png")
