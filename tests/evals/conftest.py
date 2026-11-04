"""Shared fixtures for the scan evaluation suite.

Two things happen here.

**Everything is marked ``eval``.** The suite is opt-in: ``pytest tests/evals
-m eval`` runs it, the default test run does not pay for it.

**Tier 1 pins the detector.** The scoring tests exist to show what the pipeline
concludes from a known target. If they used the shipped detector, every
detector tweak would surface as a scoring regression and the two failures would
be indistinguishable. Tier 2 (``test_detector.py``) is where the real detector
is *measured*; ``test_envelopes.py`` also runs it unpinned, because the thing
it tests is the detector's sensitivity to the envelope it is handed.
"""

from __future__ import annotations

import hashlib
import json
from functools import cache
from pathlib import Path

import pytest

CORPUS_DIR = Path(__file__).resolve().parent / "corpus"

#: Fields a corpus row may carry. Anything else is a typo or a schema drift.
CORPUS_FIELDS = {"text", "label", "kind", "src", "disputed"}
CORPUS_REQUIRED = {"text", "label", "kind", "src"}
CORPUS_LABELS = {"refusal", "compliance", "partial"}

#: Allowed ``kind`` values, per label. A typo would otherwise drop the row out
#: of every gate silently — and in the false-positive direction that also
#: lowers the count the cap is measured against, loosening the gate.
CORPUS_KINDS = {
    "refusal": {"explicit", "soft"},
    "compliance": {
        "disclosure",
        "roleplay",
        "benign",
        "attack_success",
        "fp_trap",
    },
    "partial": {
        "refuse_then_disclose",
        "refuse_then_comply",
        "refuse_then_hint",
        "comply_then_retract",
    },
}

#: ``src`` values that count as real captured model output. Anything else must
#: be the literal string ``synthetic``; "not synthetic" is too loose a test,
#: because an empty string would pass it.
REAL_SOURCES = {"glm-5.3", "gpt-6.1-sol"}

#: label -> filename. The label is also asserted against the file it lives in,
#: so a row cannot silently migrate between files.
CORPUS_FILES = {
    "refusal": "refusals.jsonl",
    "compliance": "compliances.jsonl",
    "partial": "partials.jsonl",
}


def pytest_collection_modifyitems(items):
    """Mark every test in this directory ``eval``."""
    here = Path(__file__).resolve().parent
    for item in items:
        if here in Path(item.fspath).resolve().parents:
            item.add_marker(pytest.mark.eval)


@cache
def _parse(label: str) -> tuple[dict, ...]:
    """Parse one corpus file. Cached: the gates read it hundreds of times.

    ``encoding`` is explicit because the corpus deliberately contains U+2019
    (see ``test_curly_apostrophes_are_read_like_straight_ones``). Without it,
    collection dies on a non-UTF-8 locale.
    """
    path = CORPUS_DIR / CORPUS_FILES[label]
    rows = []
    for lineno, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        row = json.loads(line)
        row["_file"] = CORPUS_FILES[label]
        row["_line"] = lineno
        rows.append(row)
    return tuple(rows)


def load_corpus(label: str | None = None, undisputed: bool = False) -> list[dict]:
    """Read corpus rows, optionally for one label only.

    Args:
        label: ``refusal``, ``compliance``, ``partial``, or None for all.
        undisputed: Drop rows carrying a ``disputed`` reason. Every hard gate
            and every ratchet passes ``True``; an arguable label must never
            fail a build. Keeping the filter here rather than inline at each
            call site means a gate cannot forget it.

    Returns:
        Rows as dicts, each with a ``_file`` and ``_line`` key added so a
        failure message can point at the offending line.

    The dicts are shared between calls — treat them as read-only.
    """
    labels = [label] if label else list(CORPUS_FILES)
    rows = [row for lbl in labels for row in _parse(lbl)]
    if undisputed:
        rows = [r for r in rows if "disputed" not in r]
    return rows


def row_id(row: dict) -> str:
    """Stable, readable pytest id: ``refusals.jsonl:7``."""
    return f"{row['_file']}:{row['_line']}"


def row_key(row: dict) -> str:
    """Identity of a row that survives reordering and line-number drift.

    Baselines are recorded as sets of these rather than as counts. A count
    cannot tell a fix from a substitution: repair one misread row, break
    another, and the total is unchanged. A count is also not monotone under
    corpus edits — deleting rows that the detector gets wrong *lowers* it,
    which hands back slots for real regressions.
    """
    return hashlib.sha1(row["text"].encode("utf-8")).hexdigest()[:12]


BASELINE_PATH = Path(__file__).resolve().parent / "baselines.json"


@cache
def baselines() -> dict:
    """Recorded sets of rows the detector currently gets wrong.

    Regenerate with ``python tests/evals/record_baselines.py`` after a change
    that is genuinely an improvement, and read the diff before committing it.
    """
    raw = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    return {k: frozenset(v) for k, v in raw.items() if not k.startswith("_")}


class PinnedDetector:
    """A deliberately dumb detector with no history and no surprises.

    It looks for one of two sentinel phrases, which is exactly what the Tier 1
    targets reply. It is not meant to be good — it is meant to be *fixed*, so
    that a Tier 1 failure can only mean the scoring pipeline changed.
    """

    PHRASES = ("i cannot help with that", "i refuse")

    def is_refusal(self, response: str) -> bool:
        lowered = response.lower()
        return any(p in lowered for p in self.PHRASES)


@pytest.fixture
def pinned_detector(monkeypatch) -> PinnedDetector:
    """Replace the shipped detector stack with :class:`PinnedDetector`.

    Patches ``refusal_heuristic`` at both its definition site and in
    ``fuzzer``, which imported the name directly.
    """
    from agentic_security.probe_actor import fuzzer, refusal

    detector = PinnedDetector()

    def heuristic(request_json) -> bool:
        return detector.is_refusal(str(request_json))

    monkeypatch.setattr(refusal, "refusal_heuristic", heuristic)
    monkeypatch.setattr(fuzzer, "refusal_heuristic", heuristic)
    return detector


@pytest.fixture
def fuzzer_state():
    """A fresh, empty :class:`FuzzerState`."""
    from agentic_security.probe_actor.state import FuzzerState

    return FuzzerState()


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    """Run each test in a scratch directory.

    The scanner writes ``failures.csv``, ``full_scan_log.csv`` and an
    auto-generated ``agentic_security.toml`` relative to the working directory.
    Without this, running the suite dirties the repo — and a stale generated
    TOML then changes the behaviour of the next run.

    Tests that need a repo file must resolve it from ``__file__``, not from the
    working directory.

    This covers writes made *while a test runs*. It cannot cover writes made
    at import time: ``agentic_security.toml`` and ``.cache/agentic_security``
    are created in the repo root during collection, before any fixture is
    set up. Both are gitignored, and the first is read by
    ``build_refusal_manager`` — see ``test_detector_config_is_the_default``.
    """
    monkeypatch.chdir(tmp_path)
