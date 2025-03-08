import asyncio
import importlib.util
import json
import os
import subprocess

from agentic_security.logutils import logger

# TODO: add probes modules

GARAK_CONFIG = "garak_rest.json"


def write_garak_config_json(port):
    with open(GARAK_CONFIG, "w") as f:
        f.write(json.dumps(SPEC, indent=4).replace("$PORT", str(port)))


# TODO: add config params to data registry


class Module:
    def __init__(self, prompt_groups: [], tools_inbox: asyncio.Queue, opts: dict = {}):
        self.tools_inbox = tools_inbox
        if not self.is_garak_installed():
            logger.error(
                "Garak module is not installed. Please install it using 'pip install garak'"
            )
        self.opts = opts

    def is_garak_installed(self) -> bool:
        garak_spec = importlib.util.find_spec("garak")
        return garak_spec is not None

    async def apply(self) -> []:
        env = os.environ.copy()
        # Command to be executed
        command = [
            "python",
            "-m",
            "garak",
            "--model_type",
            "rest",
            "-G",
            GARAK_CONFIG,
            "--probes",
            "encoding",
        ]
        logger.info("Starting Garak tool. Writing config file.")
        write_garak_config_json(port=self.opts.get("port", 8718))
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
        if process.returncode != 0:
            logger.error(f"Error executing command: {command}")
            logger.error(f"err: {err}")
            return


SPEC = {
    "rest": {
        "RestGenerator": {
            "name": "Agentic Security Proxy Service",
            "uri": "http://0.0.0.0:$PORT/proxy/chat/completions",
            "method": "POST",
            "headers": {
                "Authorization": "Bearer $OPENAI_API_KEY",
                "Content-Type": "application/json",
            },
            "req_template_json_object": {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "$INPUT"}],
                "max_tokens": 1050,
                "temperature": 0.7,
            },
            "response_json": True,
            "response_json_field": "$.choices[0].message.content",
        }
    }
}
