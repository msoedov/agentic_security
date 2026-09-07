import os
import sys

import fire  # type: ignore[import-untyped]


class CLI:
    def server(self, port: int = 8718, host: str = "127.0.0.1"):
        """
        Launch the Agentic Security server.

        Args:
            port (int): Port number for the server to listen on. Default is 8718.
            host (str): Host address for the server. Default is "127.0.0.1".
        """
        import uvicorn

        from agentic_security.app import app

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
        from agentic_security.lib import SecurityScanner

        sys.path.append(os.path.dirname("."))
        SecurityScanner().entrypoint()

    def scan(
        self,
        spec: str,
        dataset: str,
        max_budget: int = 1_000,
        max_th: float = 0.3,
        optimize: bool = False,
        artifacts_dir: str | None = None,
    ):
        """
        Run a stateless scan and stream JSON lines to stdout.

        Args:
            spec: HTTP spec text, a file path, or "-" to read standard input.
            dataset: Registry name, or a comma-separated list of registry names.
            max_budget: Maximum scan budget.
            max_th: Failure-rate threshold from 0 to 1.
            optimize: Enable adaptive scan optimization.
            artifacts_dir: Optional directory for CSV artifacts.
        """
        os.environ["AGENTIC_SECURITY_STATELESS"] = "1"
        from agentic_security.cli_scan import run_scan_command

        raise SystemExit(
            run_scan_command(
                spec=spec,
                dataset=dataset,
                max_budget=max_budget,
                max_th=max_th,
                optimize=optimize,
                artifacts_dir=artifacts_dir,
            )
        )

    def init(self, host: str = "127.0.0.1", port: int = 8718):
        """
        Generate the default CI configuration file.
        """
        from agentic_security.lib import SecurityScanner

        sys.path.append(os.path.dirname("."))
        SecurityScanner().generate_default_settings(host, port)

    i = init

    def ls(self):
        """
        List all available security checks.
        """
        from agentic_security.lib import SecurityScanner

        sys.path.append(os.path.dirname("."))
        SecurityScanner().list_checks()


def main():
    """
    Entry point for the CLI. Default behavior launches the server,
    while subcommands allow CI or configuration generation.
    """
    fire.Fire(
        CLI,
    )


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] != "scan":
        from agentic_security.misc.banner import init_banner

        init_banner()
    main()
