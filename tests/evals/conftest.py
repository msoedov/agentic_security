"""Shared fixtures for the scan evaluation suite.

Two things happen here.

**Everything is marked ``eval``.** The suite is opt-in: ``pytest tests/evals
-m eval`` runs it, the default test run does not pay for it.

**Tier 1 pins the detector.** The scoring tests exist to show what the pipeline
concludes from a known target. If they used the shipped detector, every
detector tweak would surface as a scoring regression and the two failures would
be indistinguishable. Tier 2 (``test_detector.py``) is where the real detector
is measured, and it opts out of the pin.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

CORPUS_DIR = Path(__file__).resolve().parent / "corpus"

#: Fields a corpus row may carry. Anything else is a typo or a schema drift.
CORPUS_FIELDS = {"text", "label", "kind", "src", "disputed"}
CORPUS_REQUIRED = {"text", "label", "kind", "src"}
CORPUS_LABELS = {"refusal", "compliance", "partial"}

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


def load_corpus(label: str | None = None) -> list[dict]:
    """Read corpus rows, optionally for one label only.

    Args:
        label: ``refusal``, ``compliance``, ``partial``, or None for all.

    Returns:
        Rows as dicts, each with a ``_file`` and ``_line`` key added so a
        failure message can point at the offending line.
    """
    labels = [label] if label else list(CORPUS_FILES)
    rows: list[dict] = []
    for lbl in labels:
        path = CORPUS_DIR / CORPUS_FILES[lbl]
        for lineno, line in enumerate(path.read_text().splitlines(), start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_file"] = CORPUS_FILES[lbl]
            row["_line"] = lineno
            rows.append(row)
    return rows


def row_id(row: dict) -> str:
    """Stable, readable pytest id: ``refusals.jsonl:7``."""
    return f"{row['_file']}:{row['_line']}"


@pytest.fixture(scope="session")
def corpus() -> list[dict]:
    """Every labelled row."""
    return load_corpus()


@pytest.fixture(scope="session")
def undisputed_corpus(corpus) -> list[dict]:
    """Rows whose label is not arguable.

    Hard gates run on these only. An arguable label should never fail a build;
    disputed rows are reported separately instead.
    """
    return [r for r in corpus if "disputed" not in r]


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
    """
    monkeypatch.chdir(tmp_path)
