# Agentic Security

Agentic Security is an open-source vulnerability scanner for LLM endpoints and agent workflows.

## Features

- Attack datasets from Hugging Face, public CSV files, and your local CSV files.
- Text, image, and audio attacks.
- Many-shot (multi-step) jailbreak attacks.
- Prompt transformations (encodings and ciphers) that hide the attack text.
- Refusal and leak detectors that you can turn on, turn off, or extend.
- A web UI, a CLI for CI pipelines, and an agent harness (`agesec`).

> **WARNING:** Agentic Security is a test tool. It cannot find all vulnerabilities. A scan with no failures does not prove that the target is safe.

## Where to start

1. Install the package. Refer to [Installation](installation.md).
2. Do the steps in the [Quickstart](quickstart.md).
3. To scan in a CI pipeline, refer to [CI/CD integration](ci_cd.md).

## UI

<img width="100%" alt="Agentic Security UI" src="https://res.cloudinary.com/dq0w2rtm9/image/upload/v1741192668/final_aa9jhb.gif">
