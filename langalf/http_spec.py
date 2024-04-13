import httpx
from pydantic import BaseModel


class LLMSpec(BaseModel):
    method: str
    url: str
    headers: dict
    body: str

    @classmethod
    def from_string(cls, http_spec: str):
        return parse_http_spec(http_spec)

    async def probe(self, prompt):
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=self.method,
                url=self.url,
                headers=self.headers,
                content=self.body.replace(
                    "<<PROMPT>>", escape_special_chars_for_json(prompt)
                ),
                timeout=(30, 90),
            )

        return response

    fn = probe


def parse_http_spec(http_spec: str) -> LLMSpec:
    # Splitting the spec by lines
    lines = http_spec.strip().split("\n")

    # Extracting the method and URL from the first line
    first_line_parts = lines[0].split(" ")
    method = first_line_parts[0]
    url = first_line_parts[1]  # Remove scheme for consistency

    # Parsing headers and body
    headers = {}
    body = ""
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

    return LLMSpec(method=method, url=url, headers=headers, body=body)


def escape_special_chars_for_json(prompt):
    """Escapes special characters in a string for safe inclusion in a JSON
    template.

    Args:
    prompt (str): The input string to be escaped.

    Returns:
    str: The escaped string.
    """
    # Replace backslash first to avoid double escaping backslashes
    escaped_prompt = prompt.replace("\\", "\\\\")  # Escape backslashes

    # Escape other special characters
    escaped_prompt = escaped_prompt.replace('"', '\\"')  # Escape double quotes
    escaped_prompt = escaped_prompt.replace("\n", "\\n")  # Escape new lines
    escaped_prompt = escaped_prompt.replace("\r", "\\r")  # Escape carriage returns
    escaped_prompt = escaped_prompt.replace("\t", "\\t")  # Escape tabs
    # Add more replacements here if needed

    return escaped_prompt
