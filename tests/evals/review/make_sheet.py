"""Build a blind-review sheet from the undisputed corpus.

    python tests/evals/review/make_sheet.py

Writes ``answer-key.json`` and ``for-reviewer/`` beside itself. Both are
gitignored: the key must not be committed, and the sheet is regenerated on
demand.

Deterministic: fixed seed, rows sorted by row_key before sampling, so
re-running produces the same sheet. Stratified by (label, kind), deliberately
over-weighting the hard kinds -- the point is to test whether the labelling
rules are unambiguous, not to estimate population accuracy. Within a stratum,
real captured replies are preferred over synthetic ones up to half the quota,
because the real ones carry U+2019 apostrophes and the hedging that invented
replies lack.

The answer key records a digest of the corpus it was drawn from, so ``score.py``
can tell when a sheet is being scored against a corpus that has since moved.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import shutil
import sys
from pathlib import Path

GENERATOR_VERSION = 2
SEED = 20261106
HERE = Path(__file__).resolve().parent
SHEET_DIR = HERE / "for-reviewer"

#: (label, kind) -> how many to draw. Sums to 30.
QUOTA = {
    ("refusal", "explicit"): 4,
    ("refusal", "soft"): 4,
    ("compliance", "disclosure"): 4,
    ("compliance", "attack_success"): 3,
    ("compliance", "fp_trap"): 3,
    ("compliance", "roleplay"): 2,
    ("compliance", "benign"): 2,
    ("partial", "refuse_then_disclose"): 4,
    ("partial", "refuse_then_comply"): 2,
    ("partial", "refuse_then_hint"): 2,
}


def find_repo(explicit: str | None) -> Path:
    """Locate the agentic_security checkout without hardcoding a home dir."""
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    # This file lives at tests/evals/review/, so the checkout is three up.
    candidates.append(HERE.parents[2])
    import os

    if os.environ.get("AGENTIC_SECURITY_REPO"):
        candidates.append(Path(os.environ["AGENTIC_SECURITY_REPO"]))
    candidates += [Path.cwd(), *Path.cwd().parents]

    for base in candidates:
        if (base / "tests" / "evals" / "corpus").is_dir():
            return base.resolve()
    sys.exit(
        "cannot find the agentic_security checkout.\n"
        "Pass --repo /path/to/agentic_security, set AGENTIC_SECURITY_REPO, "
        "or run this from inside the repo."
    )


def corpus_digest(rows) -> str:
    """Fingerprint of the undisputed corpus, so a stale key is detectable."""
    payload = sorted(f"{r['_key']}:{r['label']}:{r['kind']}" for r in rows)
    return hashlib.sha256("\n".join(payload).encode("utf-8")).hexdigest()[:16]


def load(repo: Path, row_key) -> list[dict]:
    rows = []
    for path in sorted((repo / "tests" / "evals" / "corpus").glob("*.jsonl")):
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("disputed"):
                continue
            row["_file"] = path.name
            row["_line"] = lineno
            row["_key"] = row_key(row)
            rows.append(row)
    return rows


def draw(pool: list[dict], n: int, rng: random.Random, real: set[str]) -> list[dict]:
    """Take ``n`` rows, preferring real captures for up to half the quota."""
    pool = sorted(pool, key=lambda r: r["_key"])
    captured = [r for r in pool if r["src"] in real]
    synthetic = [r for r in pool if r["src"] not in real]

    want_real = min(len(captured), max(1, n // 2)) if captured else 0
    picked = rng.sample(captured, want_real) if want_real else []
    picked += rng.sample(synthetic, n - len(picked))
    return picked


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", help="path to the agentic_security checkout")
    args = ap.parse_args()

    repo = find_repo(args.repo)
    sys.path.insert(0, str(repo / "tests" / "evals"))
    from conftest import CORPUS_KINDS, REAL_SOURCES, row_key

    rng = random.Random(SEED)
    rows = load(repo, row_key)

    strata: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        assert row["kind"] in CORPUS_KINDS[row["label"]], row
        strata.setdefault((row["label"], row["kind"]), []).append(row)

    picked: list[dict] = []
    for stratum, n in sorted(QUOTA.items()):
        pool = strata.get(stratum, [])
        if len(pool) < n:
            sys.exit(f"{stratum}: quota {n}, only {len(pool)} undisputed rows")
        picked += draw(pool, n, rng, REAL_SOURCES)

    # Shuffle so the sheet is not ordered by kind -- grouping would leak.
    rng.shuffle(picked)

    SHEET_DIR.mkdir(exist_ok=True)
    rules = SHEET_DIR / "RULES.md"
    source_rules = HERE / "RULES.md"
    if source_rules.exists():
        shutil.copy2(source_rules, rules)
    if not rules.exists():
        sys.exit(f"the reviewer package needs RULES.md; none found at {rules}")

    key = {}
    # utf-8-sig: the corpus contains U+2019 and em dashes, which Excel on
    # Windows mangles without a BOM.
    with (SHEET_DIR / "review-sheet.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as fh:
        w = csv.writer(fh)
        w.writerow(["id", "model_reply", "your_label", "your_kind", "notes"])
        for i, row in enumerate(picked, start=1):
            rid = f"R{i:02d}"
            w.writerow([rid, row["text"], "", "", ""])
            key[rid] = {
                "label": row["label"],
                "kind": row["kind"],
                "src": row["src"],
                "file": row["_file"],
                "line": row["_line"],
                "row_key": row["_key"],
            }

    (HERE / "answer-key.json").write_text(
        json.dumps(
            {
                "generator_version": GENERATOR_VERSION,
                "seed": SEED,
                "corpus_digest": corpus_digest(rows),
                "corpus_rows": len(rows),
                "rows": key,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    captured = sum(1 for v in key.values() if v["src"] in REAL_SOURCES)
    print(
        f"{len(picked)} rows ({captured} real captures, "
        f"{len(picked) - captured} synthetic) "
        f"-> for-reviewer/review-sheet.csv + for-reviewer/RULES.md"
    )


if __name__ == "__main__":
    main()
