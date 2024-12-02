from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from .report import router

client = TestClient(router)


@pytest.fixture
def mock_csv_exists():
    with patch.object(Path, "exists") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def mock_csv_not_exists():
    with patch.object(Path, "exists") as mock:
        mock.return_value = False
        yield mock


def test_failures_csv_exists(mock_csv_exists):
    """Test /failures endpoint when CSV file exists"""
    with patch("agentic_security.routes.report.FileResponse") as mock_response:
        mock_response.return_value = "mocked_response"
        response = client.get("/failures")
        assert response.status_code == 200
        mock_response.assert_called_once_with("failures.csv")


def test_failures_csv_not_exists(mock_csv_not_exists):
    """Test /failures endpoint when CSV file doesn't exist"""
    response = client.get("/failures")
    assert response.status_code == 200
    assert response.json() == {"error": "No failures found"}


@pytest.mark.skip
def test_get_plot():
    """Test /plot.jpeg endpoint"""
    # Mock data matching expected plot_security_report format
    table_data = [
        {
            "module": "SQL Injection",
            "tokens": 1000,
            "failureRate": 75.5,
        },
        {
            "module": "XSS Attack",
            "tokens": 800,
            "failureRate": 45.2,
        },
        {
            "module": "CSRF Attack",
            "tokens": 600,
            "failureRate": 30.8,
        },
    ]

    # Mock plot_security_report function

    response = client.post("/plot.jpeg", json={"table": table_data})

    # Verify response
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
