<p align="center">
  <h1 align="center">Agentic Security</h1>
  <p align="center">
    <b>Jailbreak and prompt-injection tests for LLM apps and agents.</b><br />
    An open-source red-team scanner for chatbots, RAG apps and AI agents. Point it at any HTTP endpoint, pin the attacks you care about, and fail the build when one gets through. It covers multimodal attacks with images and audio, multi-step jailbreaks, and fuzzing with encoded and mutated prompts.  </p>
  <p align="center">
    <a href="https://pypi.org/project/agentic_security/"><img alt="PyPI" src="https://img.shields.io/pypi/v/agentic_security"></a>
    <a href="https://github.com/msoedov/agentic_security/blob/main/LICENSE"><img alt="License: Apache 2.0" src="https://img.shields.io/badge/license-Apache%202.0-blue"></a>
    <a href="https://github.com/msoedov/agentic_security/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/msoedov/agentic_security"></a>
  </p>
  <p align="center">
    <a href="#try-it-in-two-minutes-no-api-key">Try it (no API key)</a> ·
    <a href="#scan-your-own-endpoint">Scan your endpoint</a> ·
    <a href="#run-it-in-ci">CI gate</a> ·
    <a href="#let-a-coding-agent-run-the-pentest">Agent harness</a> ·
    <a href="https://agentic-security.vercel.app">Docs</a> ·
    <a href="https://github.com/msoedov/agentic_security/issues">Questions</a>
  </p>
</p>

Apache 2.0, runs on your machine, and has no SaaS or account. Ask questions in [GitHub issues](https://github.com/msoedov/agentic_security/issues).

## Try it in two minutes (no API key)

```shell
uv tool install --python 3.15 git+https://github.com/msoedov/agentic_security   # installs agentic_security and agesec
# or, if you already run Python 3.15+:
pip install git+https://github.com/msoedov/agentic_security
agentic_security                                  # terminal 1: UI + a built-in mock LLM on :8718
```

```shell
agentic_security init                             # terminal 2: writes agentic_security.toml
agentic_security ci                               # 416 jailbreak prompts against the mock
```

```text
+---------------------------------------+----------------+----------+----------+
| Module                                | Failure Rate   | Status   | Margin   |
+=======================================+================+==========+==========+
| simonycl/aya-23-8B_advbench_jailbreak | 24.8%          | ✔        | 5.2%     |
+---------------------------------------+----------------+----------+----------+
```

The mock refuses about one prompt in five at random, so its score changes on every run. It shows how a scan works, but the number means nothing. The first run downloads the dataset from Hugging Face.

<img width="100%" alt="Agentic Security scan UI" src="https://raw.githubusercontent.com/msoedov/agentic_security/refs/heads/main/docs/images/demo.gif">

## Scan your own endpoint

`agentic_security init` wrote `agentic_security.toml`. Replace `llmSpec` with the request your app makes, and put `<<PROMPT>>` where the user input goes:

```toml
[general]
llmSpec = """
POST https://api.openai.com/v1/chat/completions
Authorization: Bearer sk-...
Content-Type: application/json

{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "<<PROMPT>>"}]}
"""
max_th = 0.3          # fail if more than 30% of attacks get through

[modules.aya-23-8B_advbench_jailbreak]
dataset_name = "simonycl/aya-23-8B_advbench_jailbreak"   # 416 prompts
```

```shell
agentic_security ls    # every dataset, with its prompt count and modality
agentic_security ci    # runs only the [modules] you listed; exit 1 if one is above max_th
```

Add datasets to `[modules]` one at a time, because each one costs API calls. The UI (`agentic_security`) has presets for OpenAI, Claude, Gemini, Azure OpenAI, Groq, Together, OpenRouter, Cohere, Replicate, Requesty and others. Image and audio endpoints use `<<BASE64_IMAGE>>` and file uploads. Refer to the [HTTP spec reference](docs/http_spec.md).

> `agentic_security scan --spec=target.http` runs **every** dataset in the registry (hundreds of thousands of prompts) and prints JSON lines. Use it against a local model or the mock, not a paid API.

## Run it in CI

Commit the config as a template with `$OPENAI_API_KEY` in place of the key:

```yaml
# .github/workflows/llm-security.yml
name: LLM security scan
on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.15"
      - run: pip install git+https://github.com/msoedov/agentic_security@main   # pin a commit SHA for reproducible builds
      - run: envsubst < agentic_security.tpl.toml > agentic_security.toml && agentic_security ci
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

The job fails when any pinned module goes above `max_th`. Refer to the [CI/CD guide](docs/ci_cd.md).

## Let a coding agent run the pentest

The `agesec` harness sends one attack at a time and waits for a decision (`continue`, `escalate`, `switch` or `stop`) from a rule set, a CI job, or Claude Code or Codex. Each run is logged and can be replayed offline as evidence.

```shell
# agesec comes with the GitHub install above
agesec run --spec target.http --seed 42      # built-in default policy
agesec report RUN_ID -o report.json          # findings, decisions, cost
```

Skills are included for [Claude Code](integrations/claude) and [Codex](integrations/codex). Refer to the [harness guide](docs/harness.md).

## What it tests

| Risk ([OWASP Top 10 for LLM Apps, 2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/)) | What the probes do |
| --- | --- |
| LLM01 Prompt Injection | Jailbreak corpora, multi-step jailbreaks, base64/rot13/noise obfuscation, image and audio inputs |
| LLM02 Sensitive Information Disclosure | Data-leak and PII probes |
| LLM03 Excessive Agency | Agent backend and tool-abuse probes |
| LLM07 Misinformation | Hallucination and refuse-to-answer probes |
| LLM10 Improper Output Handling | Malware-generation probes |

Beyond single text prompts:

- **Multimodal attacks.** Sends attacks as images (`<<BASE64_IMAGE>>`) and audio files, not only as text.
- **Multi-step jailbreaks.** Runs attack sequences across several turns. Turn it on with `enableMultiStepAttack = true` in `agentic_security.toml`.
- **Fuzzing.** Rewrites prompts with mutations such as base64, rot13, mirrored words, random case and noise characters, to find inputs that slip past filters. Refer to [stenography](docs/stenography.md).

Each dataset gets one tag, chosen from its name and source ([`owasp.py`](agentic_security/probe_data/owasp.py)). The tag tells you what a probe aims at. It does not prove coverage of the whole Top 10.

The probes come from Hugging Face jailbreak datasets, [garak](https://github.com/leondz/garak), [InspectAI](https://github.com/UKGovernmentBEIS/inspect_ai) and [llm-adaptive-attacks](https://github.com/tml-epfl/llm-adaptive-attacks). If you already run garak, this tool loads its probes and adds the CI gate, an HTTP target that works with any API, and the agent harness on top.

Your own prompts: any CSV with a `prompt` column in the working directory loads on startup. That makes it easy to turn the leak you found last month into a regression test.

> Use it only on systems you own or have written permission to test.

## Extend it

[Datasets](docs/datasets.md) · [Mutations](docs/stenography.md) · [Custom modules](docs/external_module.md) · [Refusal classifiers](docs/refusal_classifier_plugins.md) · [Contributing](docs/contributing.md)

Next on the roadmap is an RL-trained attacker that evolves jailbreaks against your defenses, plus a community module ecosystem.

## License

Apache 2.0. No affiliation with any cryptocurrency, token or blockchain project.
