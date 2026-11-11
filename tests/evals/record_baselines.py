"""Regenerate ``baselines.json`` from the current detector and corpus.

Run from the repo root::

    python tests/evals/record_baselines.py

The gates record *which* rows the detector gets wrong, not how many, so this
script is how an intentional change is accepted. Read the diff before
committing it: every row that leaves a set is a fix, and every row that joins
one is a regression you are choosing to take.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tests.evals.conftest import (
    BASELINE_PATH,
    load_corpus,
    row_key,
)


def main() -> None:
    from agentic_security.probe_actor.refusal import (
        DefaultRefusalClassifier,
        refusal_classifier_manager,
    )

    phrases = DefaultRefusalClassifier()
    full = refusal_classifier_manager.is_refusal
    only = phrases.is_refusal

    def keys(label: str, pred, want: bool, kind: str | None = None) -> list[str]:
        rows = load_corpus(label, undisputed=True)
        if kind:
            rows = [r for r in rows if r["kind"] == kind]
        return sorted({row_key(r) for r in rows if pred(r["text"]) is want})

    data = {
        "_README": "Regenerate with tests/evals/record_baselines.py. Sets of "
        "row_key() hashes; see conftest.row_key for why these are sets and "
        "not counts.",
        "missed_refusals": keys("refusal", full, False),
        "misread_compliances": keys("compliance", full, True),
        "misread_attack_successes": keys(
            "compliance", full, True, kind="attack_success"
        ),
        "partials_read_as_refusals": keys("partial", full, True),
        "phrase_missed_refusals": keys("refusal", only, False),
        "phrase_misread_compliances": keys("compliance", only, True),
    }
    BASELINE_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    for k, v in data.items():
        if not k.startswith("_"):
            print(f"{k:<28} {len(v)}")


if __name__ == "__main__":
    main()
