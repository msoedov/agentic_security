import base64
import io
import random

import httpx
import pytest
from fastapi.testclient import TestClient

from agentic_security.app import app
from agentic_security.primitives import Probe
from agentic_security.probe_actor.refusal import REFUSAL_MARKS
from agentic_security.probe_data import REGISTRY

client = TestClient(app)


def test_probe_schema_validation():
    """Test Probe model validation"""
    # Valid probe
    probe = Probe(prompt="test prompt")
    assert probe.prompt == "test prompt"

    # Invalid probe (missing required field)
    with pytest.raises(ValueError):
        Probe()


def test_self_probe_endpoint():
    """Test /v1/self-probe endpoint"""
    response = client.post("/v1/self-probe", json={"prompt": "test prompt"})
    assert response.status_code == 200

    data = response.json()
    # Verify OpenAI response structure
    assert "id" in data
    assert "object" in data
    assert "created" in data
    assert "model" in data
    assert "usage" in data
    assert "choices" in data

    # Verify choices structure
    choices = data["choices"]
    assert len(choices) == 1
    assert "message" in choices[0]
    assert "role" in choices[0]["message"]
    assert "content" in choices[0]["message"]

    # Verify message content contains the prompt
    content = choices[0]["message"]["content"]
    assert "test prompt" in content

    # Verify message is either a refusal or "This is a test!"
    remaining_text = content.replace("test prompt", "").strip()
    is_refusal = any(mark in remaining_text for mark in REFUSAL_MARKS)
    is_test = "This is a test!" in remaining_text
    assert is_refusal or is_test


def test_self_probe_invalid_input():
    """Test /v1/self-probe endpoint with invalid input"""
    # Missing prompt field
    response = client.post("/v1/self-probe", json={})
    assert response.status_code == 422

    # Empty prompt
    response = client.post("/v1/self-probe", json={"prompt": ""})
    assert response.status_code == 200  # Empty prompts are allowed by schema


def test_data_config_endpoint():
    """Test /v1/data-config endpoint"""
    response = client.get("/v1/data-config")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(REGISTRY)

    # Verify each item in response matches REGISTRY format
    for item in data:
        assert isinstance(item, dict)
        # Add assertions for expected fields based on REGISTRY structure
        # This will depend on what fields are defined in the REGISTRY items


def test_refusal_rate():
    """Test that refusal rate is approximately 20%"""
    random.seed(0)
    refusal_count = 0
    total_trials = 200

    for _ in range(total_trials):
        response = client.post("/v1/self-probe", json={"prompt": "test"})
        content = response.json()["choices"][0]["message"]["content"]
        if any(mark in content for mark in REFUSAL_MARKS):
            refusal_count += 1

    refusal_rate = refusal_count / total_trials
    # Allow for some statistical variation (±5%)
    assert (
        0.15 <= refusal_rate <= 0.25
    ), f"Refusal rate {refusal_rate} is outside expected range"


def test_self_probe_file_endpoint():
    """Test /v1/self-probe-file endpoint with valid input"""
    # Create a mock audio file
    file_content = b"mock audio content"
    file = io.BytesIO(file_content)
    files = {"file": ("test.m4a", file, "audio/m4a")}
    headers = {"Authorization": "Bearer test_api_key"}

    response = client.post(
        "/v1/self-probe-file",
        files=files,
        headers=headers,
        data={"model": "whisper-large-v3"},
    )
    assert response.status_code == 200

    data = response.json()
    assert "text" in data
    assert "model" in data
    assert data["model"] == "whisper-large-v3"


def test_self_probe_file_invalid_auth():
    """Test /v1/self-probe-file endpoint with invalid authorization"""
    file_content = b"mock audio content"
    file = io.BytesIO(file_content)
    files = {"file": ("test.m4a", file, "audio/m4a")}

    # Test missing auth header
    response = client.post("/v1/self-probe-file", files=files)
    assert response.status_code == 422

    # Test invalid auth format
    headers = {"Authorization": "InvalidFormat test_api_key"}
    response = client.post("/v1/self-probe-file", files=files, headers=headers)
    assert response.status_code == 401

    # Test empty token
    headers = {"Authorization": "Bearer "}
    response = client.post("/v1/self-probe-file", files=files, headers=headers)
    assert response.status_code == 401


def test_self_probe_file_invalid_format():
    """Test /v1/self-probe-file endpoint with invalid file format"""
    file_content = b"mock content"
    file = io.BytesIO(file_content)
    files = {"file": ("test.txt", file, "text/plain")}
    headers = {"Authorization": "Bearer test_api_key"}

    response = client.post(
        "/v1/self-probe-file",
        files=files,
        headers=headers,
        data={"model": "whisper-large-v3"},
    )
    assert response.status_code == 400
    assert "Invalid file format" in response.json()["detail"]


def test_self_probe_file_missing_file():
    """Test /v1/self-probe-file endpoint with missing file"""
    headers = {"Authorization": "Bearer test_api_key"}
    response = client.post(
        "/v1/self-probe-file",
        headers=headers,
        data={"model": "whisper-large-v3"},
    )
    assert response.status_code == 422


def test_self_probe_image_endpoint():
    """Test /v1/self-probe-image endpoint with valid input"""
    headers = {"Authorization": "Bearer test_api_key"}

    # Test with different valid payloads
    payloads = [
        # OpenAI-style multi-modal payload
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What is in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": encode_image_base64_by_url()},
                    },
                ],
            }
        ],
        # Simple text payload
        {"message": "Test message"},
        # Nested payload
        {"level1": {"level2": "test"}},
        # Empty object
        {},
        # Empty array
        [],
    ]

    for payload in payloads:
        response = client.post("/v1/self-probe-image", json=payload, headers=headers)
        assert response.status_code == 200, (payload, response.json())

        data = response.json()
        assert "choices" in data
        assert len(data["choices"]) == 1
        assert "message" in data["choices"][0]


def encode_image_base64_by_url(url: str = "https://github.com/fluidicon.png") -> str:
    """Encode image data to base64 from a URL"""
    response = httpx.get(url)
    encoded_content = base64.b64encode(response.content).decode("utf-8")
    return "data:image/jpeg;base64," + encoded_content
