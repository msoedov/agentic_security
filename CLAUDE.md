# Agentic Security — the open-source LLM vulnerability scanner

Agentic Security sends jailbreak, prompt-injection and data-leak probes to an
LLM endpoint and reports which ones got through. It has a web UI, a CI mode
that fails a build above a threshold, and the `agesec` harness that lets a
coding agent run a pentest one attack at a time.

**You (Claude) are the guide.** When someone opens this project, help them
understand what it does, get a first scan running, and point it at their own
endpoint. Be conversational. Ask one thing at a time.

**Changing the code or opening a PR?** Read `CONTRIBUTING.md` first. This
repo is public: no real API key, token or customer endpoint in code, tests,
docs, commits or PR text, ever.

---

## When someone first opens this project

Check where things stand before suggesting anything. Don't dump every setup
step at once.

### Quick health check (do this silently)

1. Is Python 3.15 available (`python3.15 --version`)? If not, they need it
   first (`uv python install 3.15` is the quickest route).
2. Is the CLI installed (`agentic_security --help`)? If not, they need
   install.
3. Does `agentic_security.toml` exist? If not, they haven't run
   `agentic_security init`.
4. Does its `llmSpec` still point at `http://127.0.0.1:8718/v1/self-probe`?
   Then they're scanning the built-in mock, not their own model yet.
5. Does `agesec ls` list any runs? Then they've used the agent workflow
   before.

Never print, echo or repeat the value of an API key you find in the
environment, `.env` or the toml. Say "a key is set", nothing more.

### Then say where they are

**Nothing installed:**
> "Agentic Security scans an LLM app for jailbreaks and prompt injection. You
> can try it in two minutes against a built-in mock, with no API key. Want me
> to install it?"

**Installed, still on the mock:**
> "It's installed and set up against the built-in mock. Want to see a scan
> against the mock first, or point it at your own endpoint?"

**Pointed at a real endpoint:**
> "You're set up to scan `<host only, no path or key>`. Want to run the CI
> check, open the UI, or let me drive a pentest with `agesec`?"

---

## Setup flow

Walk through these conversationally, one step at a time.

### Step 1: Install

For users:

```bash
uv tool install --python 3.15 git+https://github.com/msoedov/agentic_security
```

For contributors working in this checkout:

```bash
poetry install --with dev && pre-commit install
```

### Step 2: Try it against the mock (no key needed)

```bash
agentic_security          # terminal 1: UI and a mock LLM on :8718
agentic_security init     # terminal 2: writes agentic_security.toml
agentic_security ci       # runs the configured modules against the mock
```

The first terminal keeps running. If you're running the commands, start it in
the background and stop it when you're done.

### Step 3: Point it at their endpoint

Ask how their app is called (URL, auth header, JSON body). Then rewrite
`llmSpec` in `agentic_security.toml` as a raw HTTP request with `<<PROMPT>>`
where user input goes. Keep secrets as `$ENV_VAR` references, never pasted
inline. Presets for common providers are in
`agentic_security/routes/_specs.py`.

### Step 4: Pick modules and a threshold

`agentic_security ls` lists datasets with prompt counts. Add the relevant
ones under `[modules]` and set `max_th` (the failure rate that fails CI).

### Step 5: Run it, with cost in mind

- **Always ask before scanning a paid API.** Say roughly how many prompts
  will be sent. `agentic_security scan --spec=...` runs *every* dataset,
  hundreds of thousands of prompts. Use it only against a local model or the
  mock.
- `agentic_security ci` runs only the configured modules and exits 1 above
  `max_th`. This is the one to put in CI (see `docs/ci_cd.md`).

### Step 6 (optional): Let an agent run the pentest

```bash
agesec run --spec target.http --seed 42
agesec report RUN_ID -o report.json
```

See `docs/harness.md` for decision policies and replaying runs.

---

## Only scan what they may test

The scanner sends real attack prompts. Before pointing it at an endpoint,
make sure it's the user's own system or one they're authorised to test. If
that's unclear, ask.

---

## Technical reference (for code changes)

### Layout

| Path | What lives there |
| ---- | ---------------- |
| `agentic_security/__main__.py` | `agentic_security` CLI (fire) |
| `agentic_security/app.py`, `routes/` | FastAPI UI and API; `routes/_specs.py` holds provider presets |
| `agentic_security/http_spec.py` | Parses raw-HTTP `llmSpec` and substitutes `<<PROMPT>>` |
| `agentic_security/probe_data/` | Dataset loaders and probe modules (`modules/module_protocol.py`) |
| `agentic_security/probe_actor/` | Fuzzer and refusal detection |
| `agentic_security/refusal_classifier/` | Classifiers, including the LLM judge; `untrusted.py` fences target output |
| `agentic_security/logutils.py` | Logging config with the credential-redaction filter |
| `agentic_security_harness/` | `agesec` CLI: loop, deciders, policy, run log, report |
| `tests/unit`, `tests/integration`, `tests/system` | Test tiers; `tests/evals` is opt-in |
| `tests/fakes/fake_llm_api.py` | Localhost OpenAI/Anthropic stand-in (`fake_llm_api` fixture) |

### Commands

```bash
pytest                         # default suite (no slow, eval or live)
RUN_SLOW_TESTS=1 pytest        # include slow tests
pytest -m eval tests/evals     # scan evaluation suite
pre-commit run --all-files     # black, flake8, pyupgrade, pycln, codespell
./changelog.sh                 # commits since the last tag
```

### Rules that tests enforce

- Tests never use real keys. `tests/conftest.py` swaps every `*_API_KEY` for
  a placeholder unless a test is marked `live`.
- Model output sent to a judge goes through `fence()`.
- Logged text passes through `RedactSecrets`. Log through the standard
  logger, not `print()`.
