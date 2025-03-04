import pytest
import base64
import httpx
import asyncio
from agentic_security.http_spec import (
    LLMSpec,
    parse_http_spec,
    escape_special_chars_for_json,
    encode_image_base64_by_url,
    encode_audio_base64_by_url,
    InvalidHTTPSpecError,
    Modality
)

################################################################################
# Tests for agentic_security/http_spec.py
################################################################################

def test_escape_special_chars_for_json():
    """Test escaping special characters in a prompt for JSON safety."""
    prompt = 'Line1\nLine2\t"Quote"\\Backslash'
    escaped = escape_special_chars_for_json(prompt)
    assert '\\n' in escaped
    assert '\\t' in escaped
    assert '\\"' in escaped
    assert '\\\\' in escaped

def test_parse_http_spec_text():
    """Test parsing a text HTTP spec without image/audio/files requirements."""
    spec = "POST http://example.com/api\nContent-Type: application/json\n\nThis is a prompt: <<PROMPT>>"
    llm_spec = parse_http_spec(spec)
    assert llm_spec.method == "POST"
    assert llm_spec.url == "http://example.com/api"
    assert llm_spec.headers["Content-Type"] == "application/json"
    assert "<<PROMPT>>" in llm_spec.body
    assert not llm_spec.has_files
    assert not llm_spec.has_image
    assert not llm_spec.has_audio

def test_parse_http_spec_files():
    """Test parsing a HTTP spec with multipart/form-data header indicating files."""
    spec = "PUT http://example.com/upload\nContent-Type: multipart/form-data\n\nFile upload test"
    llm_spec = parse_http_spec(spec)
    assert llm_spec.has_files

def test_parse_http_spec_image_audio():
    """Test parsing a HTTP spec that requires image and audio via placeholders."""
    spec = "GET http://example.com/api\nContent-Type: application/json\n\nImage: <<BASE64_IMAGE>> and Audio: <<BASE64_AUDIO>>"
    llm_spec = parse_http_spec(spec)
    assert llm_spec.has_image
    assert llm_spec.has_audio

def test_encode_image_base64_by_url(monkeypatch):
    """Test that image encoding returns the correct base64 string with prefix."""
    dummy_content = b'test_image'
    class DummyResponse:
        def __init__(self, content):
            self.content = content

    def dummy_get(url):
        return DummyResponse(dummy_content)

    monkeypatch.setattr(httpx, "get", dummy_get)
    result = encode_image_base64_by_url("http://dummyurl.com/image.jpg")
    expected = "data:image/jpeg;base64," + base64.b64encode(dummy_content).decode("utf-8")
    assert result == expected

def test_encode_audio_base64_by_url(monkeypatch):
    """Test that audio encoding returns the correct base64 string with prefix."""
    dummy_content = b'test_audio'
    class DummyResponse:
        def __init__(self, content):
            self.content = content

    def dummy_get(url):
        return DummyResponse(dummy_content)

    monkeypatch.setattr(httpx, "get", dummy_get)
    result = encode_audio_base64_by_url("http://dummyurl.com/audio.mp3")
    expected = "data:audio/mpeg;base64," + base64.b64encode(dummy_content).decode("utf-8")
    assert result == expected

@pytest.mark.asyncio
async def test_probe_text(monkeypatch):
    """Test the probe function for text modality by replacing <<PROMPT>>."""
    spec = "POST http://example.com/api\nContent-Type: application/json\n\n{\"prompt\": \"<<PROMPT>>\"}"
    llm_spec = parse_http_spec(spec)

    async def dummy_request(self, method, url, headers, content, timeout):
        return httpx.Response(200, text="ok")

    monkeypatch.setattr(httpx.AsyncClient, "request", dummy_request)
    response = await llm_spec.probe("Hello")
    assert response.status_code == 200
    assert "ok" in response.text

@pytest.mark.asyncio
async def test_probe_with_files(monkeypatch):
    """Test that probe correctly branches to _probe_with_files when files are provided."""
    spec = "POST http://example.com/api\nContent-Type: multipart/form-data\n\nFile data"
    llm_spec = parse_http_spec(spec)
    files = {"file": ("dummy.txt", b"data")}

    async def dummy_request(self, method, url, headers, files, timeout):
        return httpx.Response(200, text="file upload ok")

    monkeypatch.setattr(httpx.AsyncClient, "request", dummy_request)
    response = await llm_spec.probe("Unused", files=files)
    assert response.status_code == 200
    assert "file upload ok" in response.text

@pytest.mark.asyncio
async def test_verify_image(monkeypatch):
    """Test verify method branch for image modality by monkeypatching image encoder."""
    spec = "POST http://example.com/api\nContent-Type: application/json\n\n{\"image\": \"<<BASE64_IMAGE>>\"}"
    llm_spec = parse_http_spec(spec)

    # Replace the image encoder to return a dummy string
    monkeypatch.setattr("agentic_security.http_spec.encode_image_base64_by_url", lambda url="": "dummy_image")

    async def dummy_request(self, method, url, headers, content, timeout):
        # Check that the dummy image is injected in the content
        assert "dummy_image" in content
        return httpx.Response(200, text="image ok")

    monkeypatch.setattr(httpx.AsyncClient, "request", dummy_request)
    response = await llm_spec.verify()
    assert response.status_code == 200
    assert "image ok" in response.text

@pytest.mark.asyncio
async def test_verify_audio(monkeypatch):
    """Test verify method branch for audio modality by monkeypatching audio encoder."""
    spec = "POST http://example.com/api\nContent-Type: application/json\n\n{\"audio\": \"<<BASE64_AUDIO>>\"}"
    llm_spec = parse_http_spec(spec)

    monkeypatch.setattr("agentic_security.http_spec.encode_audio_base64_by_url", lambda url: "dummy_audio")

    async def dummy_request(self, method, url, headers, content, timeout):
        # Ensure that the dummy audio string is present in the request content
        assert "dummy_audio" in content
        return httpx.Response(200, text="audio ok")

    monkeypatch.setattr(httpx.AsyncClient, "request", dummy_request)
    response = await llm_spec.verify()
    assert response.status_code == 200
    assert "audio ok" in response.text

@pytest.mark.asyncio
async def test_verify_files(monkeypatch):
    """Test verify method branch for files modality where _probe_with_files is invoked."""
    spec = "POST http://example.com/api\nContent-Type: multipart/form-data\n\nFile data"
    llm_spec = parse_http_spec(spec)

    async def dummy_request(self, method, url, headers, files, timeout):
        return httpx.Response(200, text="files ok")

    monkeypatch.setattr(httpx.AsyncClient, "request", dummy_request)
    response = await llm_spec.verify()
    assert response.status_code == 200
    assert "files ok" in response.text

def test_llm_spec_modality_property():
    """Test that the modality property reflects the correct modality."""
    spec_text = "POST http://example.com/api\nContent-Type: application/json\n\nPrompt: <<PROMPT>>"
    llm_spec_text = parse_http_spec(spec_text)
    assert llm_spec_text.modality == Modality.TEXT

    spec_image = "POST http://example.com/api\nContent-Type: application/json\n\nImage: <<BASE64_IMAGE>>"
    llm_spec_image = parse_http_spec(spec_image)
    assert llm_spec_image.modality == Modality.IMAGE

    spec_audio = "POST http://example.com/api\nContent-Type: application/json\n\nAudio: <<BASE64_AUDIO>>"
    llm_spec_audio = parse_http_spec(spec_audio)
    assert llm_spec_audio.modality == Modality.AUDIO

def test_from_string_invalid():
    """Test that LLMSpec.from_string raises an error for an invalid spec."""
    invalid_spec = "INVALID_SPEC"
    with pytest.raises(InvalidHTTPSpecError):
        LLMSpec.from_string(invalid_spec)
@pytest.mark.asyncio
async def test_validate_missing_files():
    """Test that LLMSpec.validate raises a ValueError when files are required but missing."""
    spec = "POST http://example.com/api\nContent-Type: multipart/form-data\n\nFile upload test"
    llm_spec = parse_http_spec(spec)
    with pytest.raises(ValueError, match="Files are required"):
        llm_spec.validate("test prompt", "", "", {})

@pytest.mark.asyncio
async def test_validate_missing_image():
    """Test that LLMSpec.validate raises a ValueError when an image is required but missing."""
    spec = "POST http://example.com/api\nContent-Type: application/json\n\nImage: <<BASE64_IMAGE>>"
    llm_spec = parse_http_spec(spec)
    with pytest.raises(ValueError, match="An image is required"):
        llm_spec.validate("test prompt", "", "dummy_audio", {})

@pytest.mark.asyncio
async def test_validate_missing_audio():
    """Test that LLMSpec.validate raises a ValueError when audio is required but missing."""
    spec = "POST http://example.com/api\nContent-Type: application/json\n\nAudio: <<BASE64_AUDIO>>"
    llm_spec = parse_http_spec(spec)
    with pytest.raises(ValueError, match="Audio is required"):
        llm_spec.validate("test prompt", "dummy_image", "", {})

def test_fn_alias(monkeypatch):
    """Test that LLMSpec.fn is a functional alias for LLMSpec.probe."""
    spec = "POST http://example.com/api\nContent-Type: application/json\n\n{\"prompt\": \"<<PROMPT>>\"}"
    llm_spec = parse_http_spec(spec)

    # Instead of overriding the instance method, verify the alias at the class level.
    assert LLMSpec.fn is LLMSpec.probe

def test_escape_special_chars_no_special():
    """Test that the escape function returns the original string if no special characters are present."""
    prompt = "Simple text without specials"
    escaped = escape_special_chars_for_json(prompt)
    assert escaped == "Simple text without specials"
@pytest.mark.asyncio
async def test_probe_text_with_special_chars(monkeypatch):
    """Test probe for text modality with special characters in prompt ensuring escaped content."""
    spec = "POST http://example.com/api\nContent-Type: application/json\n\n{\"prompt\": \"<<PROMPT>>\"}"
    llm_spec = parse_http_spec(spec)
    captured = {}

    async def dummy_request(self, method, url, headers, content, timeout):
        captured['content'] = content
        return httpx.Response(200, text="ok")

    monkeypatch.setattr(httpx.AsyncClient, "request", dummy_request)
    test_prompt = 'Hello\nWorld\t"Test"'
    response = await llm_spec.probe(test_prompt)
    expected_escaped = escape_special_chars_for_json(test_prompt)
    assert expected_escaped in captured['content']
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_verify_both_image_audio(monkeypatch):
    """Test verify method when both image and audio placeholders are present.
    Expect a ValueError because only the image branch is triggered by pattern matching and the missing audio causes validation to fail."""
    spec = ("POST http://example.com/api\nContent-Type: application/json\n\n"
            "{\"audio\": \"<<BASE64_AUDIO>>\", \"image\":\"<<BASE64_IMAGE>>\"}")
    llm_spec = parse_http_spec(spec)
    # Monkey patch the image encoder to return a dummy value
    monkeypatch.setattr("agentic_security.http_spec.encode_image_base64_by_url", lambda url="": "dummy_image")
    with pytest.raises(ValueError, match="Audio is required"):
        await llm_spec.verify()

def test_parse_http_spec_invalid_header_format():
    """Test that parse_http_spec raises an error when a header line doesn't have the expected 'key: value' format."""
    invalid_spec = "GET http://example.com/api\nInvalidHeaderWithoutColon\n\nBody with <<PROMPT>>"
    with pytest.raises(ValueError):
            parse_http_spec(invalid_spec)

def test_from_string_valid():
    """Test that LLMSpec.from_string returns a valid LLMSpec object when given a proper spec string."""
    spec = "GET http://example.com/api\nContent-Type: application/json\n\n{ \"prompt\": \"<<PROMPT>>\" }"
    llm_spec = LLMSpec.from_string(spec)
    assert llm_spec.method == "GET"
    assert llm_spec.url == "http://example.com/api"

@pytest.mark.asyncio
async def test_parse_http_spec_multiline_body():
    """Test parsing an HTTP spec with a multiline body to ensure body concatenation works."""
    spec = (
        "PATCH http://example.com/api\n"
        "Content-Type: application/json\n"
        "\n"
        "Line one of body\n"
        "Line two of body\n"
        "Line three"
    )
    llm_spec = parse_http_spec(spec)
    # As implemented, the parser concatenates lines without newline delimiters
    expected_body = "Line one of bodyLine two of bodyLine three"
    assert llm_spec.body == expected_body

@pytest.mark.asyncio
async def test_encode_image_default_argument(monkeypatch):
    """Test that encode_image_base64_by_url works with its default URL argument."""
    dummy_content = b'default_image'
    class DummyResponse:
        def __init__(self, content):
            self.content = content

    def dummy_get(url):
        # check that the default URL (which includes 'fluidicon.png') is used
        assert "fluidicon.png" in url
        return DummyResponse(dummy_content)

    monkeypatch.setattr(httpx, "get", dummy_get)
    result = encode_image_base64_by_url()
    expected = "data:image/jpeg;base64," + base64.b64encode(dummy_content).decode("utf-8")
    assert result == expected

@pytest.mark.asyncio
async def test_probe_without_prompt_placeholder(monkeypatch):
    """Test the probe function when the request body does not include the <<PROMPT>> placeholder."""
    spec = "POST http://example.com/api\nContent-Type: application/json\n\n{\"message\": \"No placeholder here\"}"
    llm_spec = parse_http_spec(spec)

    captured = {}

    async def dummy_request(self, method, url, headers, content, timeout):
        captured['content'] = content
        return httpx.Response(200, text="ok without placeholder")

    monkeypatch.setattr(httpx.AsyncClient, "request", dummy_request)
    response = await llm_spec.probe("Ignored prompt")
    assert "No placeholder here" in captured['content']
    assert response.status_code == 200

def test_validate_success():
    """Test that LLMSpec.validate does not raise an error when all required data is provided."""
    # Test case for files: files are provided as required
    spec_files = "POST http://example.com/api\nContent-Type: multipart/form-data\n\nFile upload"
    llm_spec_files = parse_http_spec(spec_files)
    llm_spec_files.validate("some prompt", "dummy_image", "dummy_audio", {"file": ("dummy.txt", b"data")})

    # Test case for image: image is provided as required
    spec_image = "POST http://example.com/api\nContent-Type: application/json\n\nImage: <<BASE64_IMAGE>>"
    llm_spec_image = parse_http_spec(spec_image)
    llm_spec_image.validate("some prompt", "dummy_image", "dummy_audio", {})

    # Test case for audio: audio is provided as required
    spec_audio = "POST http://example.com/api\nContent-Type: application/json\n\nAudio: <<BASE64_AUDIO>>"
    llm_spec_audio = parse_http_spec(spec_audio)
    llm_spec_audio.validate("some prompt", "dummy_image", "dummy_audio", {})

@pytest.mark.asyncio
async def test_probe_invalid_url(monkeypatch):
    """Test that probe raises an exception when the HTTP client fails due to an invalid URL."""
    spec = "GET http://nonexistent_url/api\nContent-Type: application/json\n\n{\"prompt\": \"<<PROMPT>>\"}"
    llm_spec = parse_http_spec(spec)

    async def dummy_request(self, method, url, headers, content, timeout):
        raise httpx.RequestError("Invalid URL")

    monkeypatch.setattr(httpx.AsyncClient, "request", dummy_request)
    with pytest.raises(httpx.RequestError):
        await llm_spec.probe("Test")