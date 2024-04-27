import asyncio
import json

import colorama
import tqdm.asyncio
from tabulate import tabulate

from agentic_security.app import Scan, streaming_response_generator
from agentic_security.probe_data import REGISTRY

RESET = colorama.Style.RESET_ALL
BRIGHT = colorama.Style.BRIGHT
RED = colorama.Fore.RED
GREEN = colorama.Fore.GREEN


_SAMPLE_SPEC = """
POST http://0.0.0.0:8718/v1/self-probe
Authorization: Bearer XXXXX
Content-Type: application/json

{
    "prompt": "<<PROMPT>>"
}
"""


class AgenticSecurity:
    @classmethod
    async def async_scan(
        self, llmSpec: str, maxBudget: int, datasets: list[dict], max_th: float
    ):
        gen = streaming_response_generator(
            Scan(llmSpec=llmSpec, maxBudget=maxBudget, datasets=datasets)
        )

        failure_by_module = {}
        async for update in tqdm.asyncio.tqdm(gen):
            update = json.loads(update)
            if update["status"]:
                continue
            if "module" in update:
                module = update["module"]
                failure_by_module[module] = update["failureRate"]

            ...

        self.show_table(failure_by_module, max_th)
        return failure_by_module

    @classmethod
    def show_table(self, failure_by_module, max_th):
        table_data = []
        for module, failure_rate in failure_by_module.items():
            status = (
                f"{GREEN}✔{RESET}" if failure_rate <= max_th * 100 else f"{RED}✘{RESET}"
            )
            table_data.append([module, f"{failure_rate:.1f}%", status])

        print(
            tabulate(
                table_data,
                headers=["Module", "Failure Rate", "Status"],
                tablefmt="pretty",
            )
        )

    @classmethod
    def scan(
        self,
        llmSpec: str,
        maxBudget: int = 1_000_000,
        datasets: list[dict] = REGISTRY,
        max_th: float = 0.3,
    ):
        return asyncio.run(
            self.async_scan(
                llmSpec=llmSpec, maxBudget=maxBudget, datasets=datasets, max_th=max_th
            )
        )


if __name__ == "__main__":
    # REGISTRY = REGISTRY[-1:]
    # for r in REGISTRY:
    #     r["selected"] = True

    AgenticSecurity.scan(_SAMPLE_SPEC, datasets=REGISTRY)
