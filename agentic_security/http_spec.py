import base64
from enum import Enum
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel

from agentic_security.config import settings_var


class Modality(Enum):
    TEXT = 0
    IMAGE = 1
    AUDIO = 2
    FILES = 3
    MIXED = 4


def encode_image_base64_by_url(url: str = "https://github.com/fluidicon.png") -> str:
    """Encode image data to base64 from a URL"""
    response = httpx.get(url)
    encoded_content = base64.b64encode(response.content).decode("utf-8")
    return "data:image/jpeg;base64," + encoded_content


def encode_audio_base64_by_url(url: str) -> str:
    """Encode audio data to base64 from a URL"""
    response = httpx.get(url)
    encoded_content = base64.b64encode(response.content).decode("utf-8")
    return "data:audio/mpeg;base64," + encoded_content


class InvalidHTTPSpecError(Exception):
    pass


class LLMSpec(BaseModel):
    method: str
    url: str
    headers: dict
    body: str
    has_files: bool = False
    has_image: bool = False
    has_audio: bool = False

    @classmethod
    def from_string(cls, http_spec: str):
        try:
            return parse_http_spec(http_spec)
        except Exception as e:
            raise InvalidHTTPSpecError(f"Failed to parse HTTP spec: {e}") from e

    def timeout(self):
        return (
            settings_var("network.timeout_connect", 30),
            settings_var("network.timeout_response", 90),
        )

    async def _probe_with_files(self, files):
        transport = httpx.AsyncHTTPTransport(retries=settings_var("network.retry", 3))
        async with httpx.AsyncClient(transport=transport) as client:
            response = await client.request(
                method=self.method,
                url=self.url,
                headers=self.headers,
                files=files,
                timeout=self.timeout(),
            )

        return response

    def validate(self, prompt, encoded_image, encoded_audio, files) -> None:
        if self.has_files and not files:
            raise ValueError("Files are required for this request.")

        if self.has_image and not encoded_image:
            raise ValueError("An image is required for this request.")

        if self.has_audio and not encoded_audio:
            raise ValueError("Audio is required for this request.")

    async def probe(
        self, prompt: str, encoded_image: str = "", encoded_audio: str = "", files={}
    ) -> httpx.Response:
        """Sends an HTTP request using the `httpx` library.

        Replaces a placeholder in the request body with a provided prompt and returns the response.

        Args:
            prompt (str): The prompt to be included in the request body.

        Returns:
            httpx.Response: The response object containing the result of the HTTP request.
        """

        self.validate(prompt, encoded_image, encoded_audio, files)

        if files:
            return await self._probe_with_files(files)
        content = self.body.replace("<<PROMPT>>", escape_special_chars_for_json(prompt))
        content = content.replace("<<BASE64_IMAGE>>", encoded_image)
        content = content.replace("<<BASE64_AUDIO>>", encoded_audio)

        transport = httpx.AsyncHTTPTransport(retries=settings_var("network.retry", 3))
        async with httpx.AsyncClient(transport=transport) as client:
            response = await client.request(
                method=self.method,
                url=self.url,
                headers=self.headers,
                content=content,
                timeout=self.timeout(),
            )

        return response

    async def verify(self) -> httpx.Response:
        match self:
            case LLMSpec(has_image=True):
                return await self.probe("test", encode_image_base64_by_url())
            case LLMSpec(has_audio=True):
                return await self.probe(
                    "test",
                    # TODO: fix url for mp3
                    encoded_audio=encode_audio_base64_by_url(
                        "https://www.example.com/audio.mp3"
                    ),
                )
            case LLMSpec(has_files=True):
                return await self._probe_with_files({})
            case _:
                return await self.probe("test prompt")

    fn = probe

    @property
    def modality(self) -> Modality:
        if self.has_image:
            return Modality.IMAGE
        if self.has_audio:
            return Modality.AUDIO
        return Modality.TEXT


def parse_http_spec(http_spec: str) -> LLMSpec:
    """Parses an HTTP specification string into a LLMSpec object.

    Args:
        http_spec (str): A string representing an HTTP specification.

    Returns:
        LLMSpec: An object representing the parsed HTTP specification, with attributes for the method, URL, headers, and body.
    """
    from agentic_security.core.app import get_secrets

    secrets = get_secrets()

    # Split the spec by lines
    lines = http_spec.strip().split("\n")

    # Extract the method and URL from the first line
    method, url = lines[0].split(" ")[0:2]

    # Check url validity
    valid_url = urlparse(url)
    # if missing the correct formatting ://, urlparse.netloc will be empty
    if valid_url.scheme not in ("http", "https") or not valid_url.netloc:
        raise InvalidHTTPSpecError(
            f"Invalid URL: {url}. Ensure it starts with 'http://' or 'https://'"
        )

    # Initialize headers and body
    headers = {}
    body = ""

    # Iterate over the remaining lines
    reading_headers = True
    for line in lines[1:]:
        if line.strip() == "":
            reading_headers = False
            continue

        if reading_headers:
            if ":" not in line:
                raise InvalidHTTPSpecError(f"Invalid header line: '{line}'")
            key, value = line.split(":", maxsplit=1)
            key = key.strip()
            value = value.strip()
            if not key:
                raise InvalidHTTPSpecError("Header name cannot be empty.")
            headers[key] = value
        else:
            body += line
    has_files = "multipart/form-data" in headers.get("Content-Type", "")
    has_image = "<<BASE64_IMAGE>>" in body
    has_audio = "<<BASE64_AUDIO>>" in body

    for key, value in secrets.items():
        if not value:
            continue
        key = key.strip("$")
        body = body.replace(f"${key}", value)

    return LLMSpec(
        method=method,
        url=url,
        headers=headers,
        body=body,
        has_files=has_files,
        has_image=has_image,
        has_audio=has_audio,
    )


def escape_special_chars_for_json(prompt: str) -> str:
    """Escapes special characters in a string for safe inclusion in a JSON
    template.

    Args:
        prompt (str): The input string to be escaped.

    Returns:
        str: The escaped string.
    """
    # Escape backslashes first to avoid double escaping
    escaped_prompt = prompt.replace("\\", "\\\\")

    # Escape other special characters
    escaped_prompt = escaped_prompt.replace('"', '\\"')
    escaped_prompt = escaped_prompt.replace("\n", "\\n")
    escaped_prompt = escaped_prompt.replace("\r", "\\r")
    escaped_prompt = escaped_prompt.replace("\t", "\\t")

    return escaped_prompt
