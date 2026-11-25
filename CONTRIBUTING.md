# Contributing to Agentic Security

This file is for anyone changing the repository and opening pull requests,
and above all for coding agents (Claude Code, Codex, Cursor, Aider), which
open a large share of the PRs here. `CLAUDE.md` is different: it guides
someone *using* the scanner. The step-by-step fork, branch and PR procedure
is in [docs/contributing.md](docs/contributing.md).

## Set up

```bash
poetry install --with dev
pre-commit install
pytest                      # unit suite; skips slow, eval and live tests
```

Python 3.15 is required. Test tiers are pytest markers:

| Marker | Runs by default | What it is for |
| ------ | --------------- | -------------- |
| (none) | yes | Unit and integration tests. No network, no real keys. |
| `slow` | no, set `RUN_SLOW_TESTS=1` | Long-running tests. |
| `eval` | no, `pytest -m eval tests/evals` | The scan evaluation suite. |
| `live` | no, opt in per test | Tests that use real API keys from your environment. |

## No real secrets, anywhere it gets published

This repository is public and it is a security tool, so fixtures are full of
things that *look* like credentials. Make sure none of them are real.

**Never put any of these in a commit, test, fixture, doc, commit message, PR
title, PR description or issue:**

- a real API key or token, even an expired or revoked one;
- a real customer's or employer's endpoint, model deployment name or prompt;
- output copied from a scan of a system you don't own.

**Do this instead:**

- Write keys by hand in an obviously fake shape: `sk-test-FAKE...`,
  `hf_FAKE...`, or the placeholder the suite already uses.
- Use reserved hosts for endpoints: `example.com`, `.example`, `.test`,
  `127.0.0.1`.
- Report live checks as counts only ("12 of 400 prompts got through"), not
  the prompts and replies themselves.

**Before you push**, grep the diff for key shapes:

```bash
git diff origin/main | grep '^+' | grep -oE '(sk-(ant-|proj-)?|hf_|AKIA|ghp_)[A-Za-z0-9_-]{12,}' | sort -u
```

Every hit should be a fake you wrote. Once something is pushed to a public
repository, deleting it later doesn't remove it: old commits stay reachable
by hash and PR descriptions keep an edit history.

## Tests never call paid APIs

The unit suite swaps every `*_API_KEY` in your environment for a placeholder
(`tests/conftest.py`), so a test that reaches a real provider fails instead of
spending money. To exercise a real SDK, use the `fake_llm_api` fixture: a
localhost OpenAI- and Anthropic-compatible server (`tests/fakes/fake_llm_api.py`)
that records request bodies and header *names*, never header values.

## Recipes

**A new provider preset** (the most common PR) touches three files. Copy the
shape of the TeamoRouter preset (commit `762f851`):

1. `agentic_security/routes/_specs.py`: the spec entry and its `LLM_SPECS` row.
2. `agentic_security/static/base.js`: the UI tile.
3. `tests/unit/test_<name>_spec.py`: asserts the spec parses (method, URL,
   `Bearer $<NAME>_API_KEY`, model, modality) and drives one request through
   `httpx.MockTransport`. No network.

**Anything that sends model output to a judge LLM** goes through
`agentic_security/refusal_classifier/untrusted.py:fence`. The model under test
is attacker-influenced, and unfenced output can steer the verdict.

**Anything that logs URLs, headers or specs** goes through the standard
logger (`agentic_security/logutils.py`), whose filter masks credentials.
Don't `print()` them.

## Pull requests

- Keep each PR to one change. A preset, a fix and a refactor are three PRs.
- Fill in the template: what changed, how you tested it, and the checklist.
- Update the docs when behaviour changes.
- `pre-commit run --all-files` must pass. It runs black, flake8, pyupgrade,
  pycln and codespell.

## Security issues

Don't open a public issue. See [SECURITY.md](SECURITY.md).
