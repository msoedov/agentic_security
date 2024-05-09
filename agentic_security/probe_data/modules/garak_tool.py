import asyncio
import importlib.util
import os
import subprocess

from loguru import logger

# TODO: add probes modules


class Module:
    def __init__(self, prompt_groups: [], tools_inbox: asyncio.Queue):
        self.tools_inbox = tools_inbox
        if not self.is_garak_installed():
            logger.error(
                "Garak module is not installed. Please install it using 'pip install garak'"
            )

    def is_garak_installed(self) -> bool:
        garak_spec = importlib.util.find_spec("garak")
        return garak_spec is not None

    async def apply(self) -> []:
        env = os.environ.copy()
        env["OPENAI_API_BASE"] = "http://0.0.0.0:8718/proxy"

        # Command to be executed
        command = [
            "python",
            "-m",
            "garak",
            "--model_type",
            "openai",
            "--model_name",
            "gpt-3.5-turbo",
            "--probes",
            "encoding",
        ]
        logger.info(f"Executing command: {command}")
        # Execute the command with the specific environment
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env
        )
        out, err = await asyncio.to_thread(process.communicate)
        yield "Started"
        is_empty = self.tools_inbox.empty()
        logger.info(f"Is inbox empty? {is_empty}")
        while not self.tools_inbox.empty():
            ref = self.tools_inbox.get_nowait()
            message, _, ready = ref["message"], ref["reply"], ref["ready"]
            yield message
            ready.set()
        logger.info("Garak tool finished.")
        logger.info(f"stdout: {out}")
        logger.error(f"exit code: {process.returncode}")
        if process.returncode != 0:
            logger.error(f"Error executing command: {command}")
            logger.error(f"err: {err}")
            return
