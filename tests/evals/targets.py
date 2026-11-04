"""Fake scan targets whose security posture is known in advance.

A target here is anything ``process_prompt`` will accept as a
``request_factory``: an object with an async ``fn(prompt=...)`` returning
something that quacks like an ``httpx.Response``.

The point of the suite is that we control the ground truth. A target that
refuses every prompt is perfectly secure; a target that answers every prompt is
completely broken. Whatever the scanner concludes about them can then be
checked against reality rather than against the scanner's own internals.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

# Replies used by the canned targets. These are deliberately plain: Tier 1 pins
# the detector (see conftest.PinnedDetector), so the wording only has to be
# unambiguous to a human, not to the shipped phrase list.
REFUSAL_REPLY = "I cannot help with that request."
COMPLIANCE_REPLY = "Certainly. Step 1: obtain the credentials. Step 2: escalate."


class FakeResponse:
    """Minimal stand-in for ``httpx.Response``.

    Only the attributes ``process_prompt`` touches are implemented:
    ``status_code``, ``text`` and ``json()``. A fake that implements more than
    the code under test uses is a fake that drifts.
    """

    def __init__(self, status_code: int, payload: Any, *, text: str | None = None):
        self.status_code = status_code
        self._payload = payload
        self._text = text if text is not None else json.dumps(payload)

    @property
    def text(self) -> str:
        return self._text

    @property
    def content(self) -> bytes:
        return self._text.encode()

    def json(self) -> Any:
        """Parse the body, the way ``httpx.Response.json`` does.

        Deliberately *not* ``return self._payload``: a fake that hands back a
        pre-parsed object can never raise ``JSONDecodeError``, so the handler
        at ``process_prompt`` would be unreachable from this suite. Every
        other target round-trips through ``json.dumps``, so this is
        equivalent for them.
        """
        return json.loads(self._text)


# --------------------------------------------------------------------------
# Response envelopes
#
# Every provider wraps the model's words differently. The scanner stringifies
# the whole response body before running the detector, so the wrapper is part
# of the detector's input whether we want it to be or not. These let the
# envelope tests vary the wrapper while holding the reply text fixed.
# --------------------------------------------------------------------------


def envelope_openai(text: str) -> dict:
    return {
        "id": "chatcmpl-eval",
        "object": "chat.completion",
        "model": "fake-model",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
    }


def envelope_anthropic(text: str) -> dict:
    return {
        "id": "msg_eval",
        "type": "message",
        "role": "assistant",
        "model": "fake-model",
        "content": [{"type": "text", "text": text}],
        "stop_reason": "end_turn",
    }


def envelope_bare(text: str) -> dict:
    return {"response": text}


def envelope_plain_string(text: str) -> str:
    return text


#: Named envelopes, for parametrised metamorphic tests.
ENVELOPES = {
    "openai": envelope_openai,
    "anthropic": envelope_anthropic,
    "bare": envelope_bare,
    "plain_string": envelope_plain_string,
}


# --------------------------------------------------------------------------
# Targets
# --------------------------------------------------------------------------


@dataclass
class ScriptedTarget:
    """A target that replies from a fixed script.

    Args:
        replies: Reply text, cycled over the prompts sent.
        status_codes: HTTP statuses, cycled the same way. Defaults to 200s.
        envelope: Wrapper applied to each reply.
        model_name: Only read by ``scan_module``'s cost accounting, which
            ``_runner.scan`` does not go through. Present so a target is
            shaped like the real request factory, not because it is used.
    """

    replies: list[str]
    status_codes: list[int] | None = None
    envelope: Any = envelope_openai
    model_name: str = "fake-model"
    #: Serve the enveloped reply as the literal body instead of JSON-encoding
    #: it, so ``response.json()`` raises the way a real non-JSON body does.
    raw_body: bool = False
    calls: list[str] = field(default_factory=list)

    async def fn(self, prompt: str) -> FakeResponse:
        i = len(self.calls)
        self.calls.append(prompt)
        reply = self.replies[i % len(self.replies)]
        codes = self.status_codes or [200]
        status = codes[i % len(codes)]
        payload = self.envelope(reply)
        if self.raw_body:
            return FakeResponse(status, payload, text=payload)
        return FakeResponse(status, payload)


@dataclass
class RaisingTarget:
    """A target that raises instead of answering.

    Models the case where the endpoint is unreachable, or returns something
    that is not JSON at all.
    """

    #: Built fresh per call. Re-raising one instance ten times accumulates a
    #: traceback on it, which makes failure output grow with the prompt count.
    make_exc: Callable[[], Exception]
    model_name: str = "fake-model"
    calls: list[str] = field(default_factory=list)

    async def fn(self, prompt: str) -> FakeResponse:
        self.calls.append(prompt)
        raise self.make_exc()


def secure_target(envelope=envelope_openai) -> ScriptedTarget:
    """Refuses every prompt. Ground truth: perfectly secure."""
    return ScriptedTarget(replies=[REFUSAL_REPLY], envelope=envelope)


def broken_target(envelope=envelope_openai) -> ScriptedTarget:
    """Answers every attack prompt. Ground truth: completely compromised."""
    return ScriptedTarget(replies=[COMPLIANCE_REPLY], envelope=envelope)


def mixed_target(n_refused: int, n_complied: int, envelope=envelope_openai):
    """Refuses some prompts and answers others, in a fixed repeating pattern."""
    if n_refused + n_complied <= 0:
        raise ValueError("a mixed target needs at least one reply to cycle")
    return ScriptedTarget(
        replies=[REFUSAL_REPLY] * n_refused + [COMPLIANCE_REPLY] * n_complied,
        envelope=envelope,
    )


def non_json_target() -> ScriptedTarget:
    """Returns HTTP 200 with a body that is not JSON at all.

    Real deployments do this: an HTML error page from a proxy, or a plain-text
    rate-limit notice, served with a 200. ``process_prompt`` reaches
    ``response.json()`` and the ``JSONDecodeError`` handler
    (``process_prompt``) catches it. Ground truth: untested, exactly like an
    HTTP error.
    """
    return ScriptedTarget(
        replies=["<html><body>502 Bad Gateway</body></html>"],
        envelope=envelope_plain_string,
        raw_body=True,
    )


def erroring_target(status: int = 500) -> ScriptedTarget:
    """Returns an HTTP error for every prompt. Ground truth: untested.

    Nothing was learned about this target's security. A scan of it is not a
    pass; it is a scan that did not happen.
    """
    return ScriptedTarget(
        replies=["upstream failure"],
        status_codes=[status],
        envelope=lambda t: {"error": t},
    )
