import httpx
from pydantic import BaseModel


class InvalidHTTPSpecError(Exception): ...


class LLMSpec(BaseModel):
    method: str
    url: str
    headers: dict
    body: str
    has_files: bool = False
    has_image: bool = False

    @classmethod
    def from_string(cls, http_spec: str):
        try:
            return parse_http_spec(http_spec)
        except Exception as e:
            raise InvalidHTTPSpecError(f"Failed to parse HTTP spec: {e}") from e

    async def _probe_with_files(self, files):
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=self.method,
                url=self.url,
                headers=self.headers,
                files=files,
                timeout=(30, 90),
            )

        return response

    def validate(self, prompt, encoded_image, files) -> None:
        if self.has_files and not files:
            raise ValueError("Files are required for this request.")

        if self.has_image:
            if not encoded_image:
                raise ValueError("An image is required for this request.")

    async def probe(
        self, prompt: str, encoded_image: str = "", files={}
    ) -> httpx.Response:
        """Sends an HTTP request using the `httpx` library.

        Replaces a placeholder in the request body with a provided prompt and returns the response.

        Args:
            prompt (str): The prompt to be included in the request body.

        Returns:
            httpx.Response: The response object containing the result of the HTTP request.
        """

        self.validate(prompt, encoded_image, files)

        if files:
            return await self._probe_with_files(files)
        content = self.body.replace("<<PROMPT>>", escape_special_chars_for_json(prompt))
        content = content.replace("<<BASE64_IMAGE>>", encoded_image)
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=self.method,
                url=self.url,
                headers=self.headers,
                content=content,
                timeout=(30, 90),
            )

        return response

    fn = probe


def parse_http_spec(http_spec: str) -> LLMSpec:
    """Parses an HTTP specification string into a LLMSpec object.

    Args:
        http_spec (str): A string representing an HTTP specification.

    Returns:
        LLMSpec: An object representing the parsed HTTP specification, with attributes for the method, URL, headers, and body.
    """

    # Split the spec by lines
    lines = http_spec.strip().split("\n")

    # Extract the method and URL from the first line
    method, url = lines[0].split(" ")[0:2]

    # Initialize headers and body
    headers = {}
    body = ""

    # Iterate over the remaining lines
    reading_headers = True
    for line in lines[1:]:
        if line == "":
            reading_headers = False
            continue

        if reading_headers:
            key, value = line.split(": ")
            headers[key] = value
        else:
            body += line
    has_files = "multipart/form-data" in headers.get("Content-Type", "")
    has_image = "<<BASE64_IMAGE>>" in body
    return LLMSpec(
        method=method,
        url=url,
        headers=headers,
        body=body,
        has_files=has_files,
        has_image=has_image,
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
