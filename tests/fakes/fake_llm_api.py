"""A localhost stand-in for the OpenAI and Anthropic HTTP APIs.

Lets tests drive the real ``openai`` and ``anthropic`` SDKs with no network
and no credentials. Point ``base_url`` at ``server.url`` (OpenAI clients add
``/v1`` themselves when you pass ``server.url + "/v1"``).

Every request is recorded as ``{"method", "path", "headers", "body"}``, with
header NAMES only, never values, so nothing credential-shaped is ever kept,
even when a client sends a real key.

Routes:
  POST /v1/chat/completions   OpenAI-compatible chat (non-streaming)
  POST /v1/messages           Anthropic Messages (non-streaming)
  POST /v1/messages/count_tokens
Anything else answers 404 in the matching provider's error shape.
"""

import json
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


@dataclass
class FakeLLMServer:
    """Running fake. ``reply`` is what every completion returns."""

    reply: str = "FAKE-REPLY"
    requests: list[dict[str, Any]] = field(default_factory=list)
    _httpd: ThreadingHTTPServer | None = None
    _thread: threading.Thread | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock)

    @property
    def url(self) -> str:
        assert self._httpd is not None, "server not started"
        host, port = self._httpd.server_address[:2]
        return f"http://{host}:{port}"

    def start(self) -> FakeLLMServer:
        server = self

        class Handler(_Handler):
            fake = server

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None

    def record(self, entry: dict[str, Any]) -> None:
        with self._lock:
            self.requests.append(entry)

    def bodies(self, path_suffix: str = "") -> list[Any]:
        with self._lock:
            return [r["body"] for r in self.requests if r["path"].endswith(path_suffix)]


class _Handler(BaseHTTPRequestHandler):
    fake: FakeLLMServer
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # keep test output quiet
        pass

    def _send(self, code: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self) -> Any:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            return json.loads(raw or b"null")
        except ValueError:
            return raw.decode("utf-8", "replace")

    def _record(self, body: Any) -> None:
        self.fake.record(
            {
                "method": self.command,
                "path": self.path.split("?", 1)[0],
                "headers": sorted(k.lower() for k in self.headers.keys()),
                "body": body,
            }
        )

    def do_GET(self):
        self._record(None)
        self._send(404, {"error": {"type": "not_found_error", "message": "fake"}})

    do_DELETE = do_GET

    def do_POST(self):
        body = self._read_body()
        self._record(body)
        path = self.path.split("?", 1)[0]
        model = body.get("model", "fake-model") if isinstance(body, dict) else "fake"

        if path.endswith("/chat/completions"):
            return self._send(200, _openai_chat(model, self.fake.reply))
        if path.endswith("/messages/count_tokens"):
            return self._send(200, {"input_tokens": 1})
        if path.endswith("/messages"):
            return self._send(200, _anthropic_message(model, self.fake.reply))
        self._send(404, {"error": {"type": "not_found_error", "message": "fake"}})


def _openai_chat(model: str, text: str) -> dict[str, Any]:
    return {
        "id": "chatcmpl-fake",
        "object": "chat.completion",
        "created": 0,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


def _anthropic_message(model: str, text: str) -> dict[str, Any]:
    return {
        "id": "msg_fake",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": [{"type": "text", "text": text}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 1, "output_tokens": 1},
    }
