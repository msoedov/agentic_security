import asyncio
import os
import uuid as U

import httpx

from agentic_security.logutils import logger

AUTH_TOKEN: str = os.getenv("AS_TOKEN", "gh0-5f4a8ed2-37c6-4bd7-a0cf-7070eae8115b")


class Module:
    def __init__(
        self, prompt_groups: list[str], tools_inbox: asyncio.Queue, opts: dict = {}
    ):
        self.tools_inbox = tools_inbox
        self.opts = opts
        self.prompt_groups = prompt_groups
        self.max_prompts = self.opts.get("max_prompts", 2000)  # Default max M prompts
        self.run_id = U.uuid4().hex
        self.batch_size = self.opts.get("batch_size", 500)

    async def apply(self):
        for _ in range(max(self.max_prompts // self.batch_size, 1)):
            # Fetch prompts from the API
            prompts = await self.fetch_prompts()

            if not prompts:
                logger.error("No prompts retrieved from the API.")
                return

            logger.info(f"Retrieved {len(prompts)} prompts.")

            for i, prompt in enumerate(
                prompts[: self.max_prompts]
            ):  # Limit to max_prompts
                logger.info(f"Processing prompt {i+1}/{len(prompts)}: {prompt}")
                # response = await self.post_prompt(prompt)
                # logger.info(f"Response: {response}")
                yield prompt

                while not self.tools_inbox.empty():
                    ref = await self.tools_inbox.get()
                    message, _, ready = ref["message"], ref["reply"], ref["ready"]
                    yield message
                    ready.set()

    async def post_prompt(self, prompt: str):
        port = self.opts.get("port", 8718)
        uri = f"http://0.0.0.0:{port}/proxy/chat/completions"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1050,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(uri, headers=headers, json=data)
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Failed to post prompt: {e}")
                return {}

    async def fetch_prompts(self) -> list[str]:
        api_url = "https://edge.metaheuristic.co/infer"
        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    api_url,
                    headers=headers,
                    json={"batch_size": self.batch_size, "run_id": self.run_id},
                )
                response.raise_for_status()
                data = response.json()
                return data.get("prompts", [])
            except httpx.RequestError as e:
                logger.error(f"Failed to fetch prompts: {e}")
                return []
