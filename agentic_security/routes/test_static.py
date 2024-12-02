from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from ..models.schemas import Settings
from .static import get_static_file, router

client = TestClient(router)


def test_root_route():
    """Test the root route returns index.html"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_main_js_route():
    """Test the main.js route"""
    response = client.get("/main.js")
    assert response.status_code == 200
    assert "application/javascript" in response.headers["content-type"]
    assert "Cache-Control" in response.headers


def test_favicon_route():
    """Test the favicon route"""
    response = client.get("/favicon.ico")
    assert response.status_code == 200
    assert "image/x-icon" in response.headers["content-type"]
    assert "Cache-Control" in response.headers


def test_telemetry_js_route_enabled():
    """Test telemetry.js route when telemetry is enabled"""
    Settings.DISABLE_TELEMETRY = False
    response = client.get("/telemetry.js")
    assert response.status_code == 200
    assert "application/javascript" in response.headers["content-type"]


def test_telemetry_js_route_disabled():
    """Test telemetry.js route when telemetry is disabled"""
    Settings.DISABLE_TELEMETRY = True
    response = client.get("/telemetry.js")
    assert response.status_code == 200
    assert "application/javascript" in response.headers["content-type"]


def test_get_static_file_not_found():
    """Test get_static_file with non-existent file"""
    with pytest.raises(HTTPException) as exc_info:
        get_static_file(Path("nonexistent.file"))
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "File not found"
