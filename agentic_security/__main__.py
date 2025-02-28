import os
import sys

import fire
import uvicorn

from agentic_security.app import app
from agentic_security.banner import init_banner
from agentic_security.lib import AgenticSecurity


class CLI:
    def server(self, port: int = 8718, host: str = "0.0.0.0"):
        """
        Launch the Agentic Security server.

        Args:
            port (int): Port number for the server to listen on. Default is 8718.
            host (str): Host address for the server. Default is "0.0.0.0".
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
        AgenticSecurity().entrypoint()

    def init(self, host: str = "0.0.0.0", port: int = 8718):
        """
        Generate the default CI configuration file.
        """
        sys.path.append(os.path.dirname("."))
        AgenticSecurity().generate_default_cfg(host, port)

    i = init

    def ls(self):
        """
        List all available security checks.
        """
        sys.path.append(os.path.dirname("."))
        AgenticSecurity().list_checks()


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
