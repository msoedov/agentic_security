import os
import sys

import fire
import uvicorn

from agentic_security.app import app
from agentic_security.lib import SecurityScanner
from agentic_security.misc.banner import init_banner


class CLI:
    def server(self, port: int = 8718, host: str = "127.0.0.1"):
        """
        Launch the Agentic Security server.

        Args:
            port (int): Port number for the server to listen on. Default is 8718.
            host (str): Host address for the server. Default is "127.0.0.1".
        """
        sys.path.append(os.path.dirname("."))
        config = uvicorn.Config(
            app, port=port, host=host, log_level="info", reload=True
        )
        server = uvicorn.Server(config)
        server.run()

    s = server

    def ci(self):
        """
        Run Agentic Security in CI mode.
        """
        sys.path.append(os.path.dirname("."))
        SecurityScanner().entrypoint()

    def init(self, host: str = "127.0.0.1", port: int = 8718):
        """
        Generate the default CI configuration file.
        """
        sys.path.append(os.path.dirname("."))
        SecurityScanner().generate_default_settings(host, port)

    i = init

    def ls(self):
        """
        List all available security checks.
        """
        sys.path.append(os.path.dirname("."))
        SecurityScanner().list_checks()

    def scan(
        self,
        spec: str = "-",
        max_budget: int = 1_000_000,
        max_th: float = 0.3,
        optimize: bool = False,
        enable_multi_step_attack: bool = False,
    ):
        """
        Run a stateless security scan from an HTTP LLM spec.

        Args:
            spec: File path, inline HTTP spec text, or '-' to read from stdin.
            max_budget: Maximum probe budget for the scan.
            max_th: Failure-rate threshold (0-1); modules above it fail the run.
        """
        if spec == "-":
            llm_spec = sys.stdin.read()
        elif os.path.isfile(spec):
            with open(spec, encoding="utf-8") as handle:
                llm_spec = handle.read()
        else:
            llm_spec = spec

        exit_code = SecurityScanner.scan_cli(
            llm_spec.strip(),
            max_budget=max_budget,
            max_th=max_th,
            optimize=optimize,
            enable_multi_step_attack=enable_multi_step_attack,
        )
        raise SystemExit(exit_code)


def main():
    """
    Entry point for the CLI. Default behavior launches the server,
    while subcommands allow CI or configuration generation.
    """
    fire.Fire(
        CLI,
    )


if __name__ == "__main__":
    init_banner()
    main()
