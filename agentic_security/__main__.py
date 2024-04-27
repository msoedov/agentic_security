import os
import sys

import fire
import uvicorn

from agentic_security.app import app


class T:
    def server(self, port=8718, host="0.0.0.0"):
        sys.path.append(os.path.dirname("."))
        config = uvicorn.Config(
            app, port=port, host=host, log_level="info", reload=True
        )
        server = uvicorn.Server(config)
        server.run()
        return

    def headless(self):
        sys.path.append(os.path.dirname("."))


def entrypoint():
    fire.Fire(T().server)


def ci_entrypoint():
    fire.Fire(T().headless)


if __name__ == "__main__":
    entrypoint()
