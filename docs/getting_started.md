# Getting Started

Welcome to Agentic Security! This guide will help you orient yourself within the project and start using the tool quickly.

## Project Overview

Agentic Security is an open-source vulnerability scanner for Large Language Models (LLMs). It provides both a command line interface and a FastAPI server so you can probe models for weaknesses such as jailbreaks or refusal patterns. The tool supports multimodal attacks, multi-step scans and reinforcement-learning based probes.

## Repository Layout

```
agentic_security/
├── __main__.py    - CLI entry point
├── app.py         - FastAPI app assembly
├── lib.py         - SecurityScanner and utilities
├── config.py      - Configuration handling
├── core/          - app state and logging helpers
├── probe_actor/   - scanning logic and RL modules
├── probe_data/    - dataset registry and loaders
├── routes/        - API endpoints
└── ui/            - Web UI assets (Vue)
```

`tests/` contains unit tests, and `docs/` houses the project documentation.

## Quick Start

1. Ensure you have completed the [installation](installation.md) steps.
2. Run the following command to start the application:
   ```bash
   agentic_security
   ```
   The server will start on `http://localhost:8718`.
3. Explore available commands with:
   ```bash
   agentic_security --help
   ```

## Basic Usage

- To view available commands, run:
  ```bash
  agentic_security --help
  ```

## Next Steps

- Review the [Quickstart Guide](quickstart.md) for a fast setup walkthrough.
- Check [http_spec.md](http_spec.md) to learn how LLM endpoints are described.
- Browse the `probe_actor` and `probe_data` modules to understand how scanning works and how datasets are loaded.
- Explore the [Configuration](configuration.md) section to customize your setup.
- Run the tests in `tests/` to verify your environment once dependencies are installed.

This guide should give you a solid foundation for exploring and extending Agentic Security. For more details, see the rest of the documentation.
