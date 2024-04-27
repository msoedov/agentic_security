import subprocess
import os
import asyncio
from loguru import logger
import asyncio


class Module:

    def __init__(self, prompt_groups: [], tools_inbox: asyncio.Queue):
        self.tools_inbox = tools_inbox

    async def apply(self) -> []:
        env = os.environ.copy()
        env["OPENAI_API_BASE"] = "http://0.0.0.0:8718/proxy"

        # Command to be executed
        command = [
            "python3",
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
