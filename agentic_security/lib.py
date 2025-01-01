import asyncio
import json
from datetime import datetime

import colorama
import tqdm.asyncio
from tabulate import tabulate

from agentic_security.models.schemas import Scan
from agentic_security.probe_data import REGISTRY
from agentic_security.routes.scan import streaming_response_generator

# Enhanced color and style definitions
RESET = colorama.Style.RESET_ALL
BRIGHT = colorama.Style.BRIGHT
RED = colorama.Fore.RED
GREEN = colorama.Fore.GREEN
YELLOW = colorama.Fore.YELLOW
BLUE = colorama.Fore.BLUE


class AgenticSecurity:
    @classmethod
    async def async_scan(
        cls,
        llmSpec: str,
        maxBudget: int,
        datasets: list[dict],
        max_th: float,
        optimize: bool = False,
        enableMultiStepAttack: bool = False,
        probe_datasets: list[dict] = [],
    ):
        start_time = datetime.now()
        total_modules = len(datasets)
        completed_modules = 0
        failure_by_module = {}
        detailed_results = {}

        gen = streaming_response_generator(
            Scan(
                llmSpec=llmSpec,
                maxBudget=maxBudget,
                datasets=datasets,
                optimize=optimize,
                enableMultiStepAttack=enableMultiStepAttack,
                probe_datasets=probe_datasets,
            )
        )

        async for update in tqdm.asyncio.tqdm(gen, desc="Scanning modules"):
            update = json.loads(update)
            if update["status"]:
                continue

            if "module" in update:
                module = update["module"]
                failure_rate = update["failureRate"]
                failure_by_module[module] = failure_rate

                # Store detailed results including timestamp and additional metrics
                detailed_results[module] = {
                    "failure_rate": failure_rate,
                    "timestamp": datetime.now().isoformat(),
                    "status": "PASS" if failure_rate <= max_th * 100 else "FAIL",
                    "threshold": max_th * 100,
                    "margin": abs(max_th * 100 - failure_rate),
                }
                completed_modules += 1

        duration = datetime.now() - start_time
        cls.show_enhanced_table(
            failure_by_module, detailed_results, max_th, duration, total_modules
        )
        return detailed_results

    @classmethod
    def show_enhanced_table(
        cls, failure_by_module, detailed_results, max_th, duration, total_modules
    ):
        # Header
        print(f"\n{BRIGHT}Security Scan Results{RESET}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {duration.total_seconds():.1f}s")
        print(f"Modules Scanned: {total_modules}")
        print(f"Threshold: {max_th * 100}%\n")

        # Prepare table data with enhanced formatting
        table_data = []
        total_failures = 0
        for module, failure_rate in failure_by_module.items():
            result = detailed_results[module]
            status_color = GREEN if result["status"] == "PASS" else RED
            status_symbol = "✔" if result["status"] == "PASS" else "✘"

            # Color coding for failure rates
            rate_color = (
                GREEN
                if failure_rate < max_th * 50
                else (YELLOW if failure_rate < max_th * 100 else RED)
            )

            formatted_row = [
                f"{BRIGHT}{module}{RESET}",
                f"{rate_color}{failure_rate:.1f}%{RESET}",
                f"{status_color}{status_symbol}{RESET}",
                f"{result['margin']:.1f}%",
            ]
            table_data.append(formatted_row)

            if result["status"] == "FAIL":
                total_failures += 1

        # Sort table by failure rate
        table_data.sort(
            key=lambda x: float(
                x[1]
                .replace(GREEN, "")
                .replace(YELLOW, "")
                .replace(RED, "")
                .replace(RESET, "")
                .replace("%", "")
            )
        )

        print(
            tabulate(
                table_data,
                headers=["Module", "Failure Rate", "Status", "Margin"],
                tablefmt="grid",
                stralign="left",
            )
        )

        # Summary statistics
        pass_rate = (
            ((total_modules - total_failures) / total_modules) * 100
            if total_modules > 0
            else 0
        )
        print("\nSummary:")
        print(
            f"Total Passing: {total_modules - total_failures}/{total_modules} ({pass_rate:.1f}%)"
        )

        if total_failures > 0:
            print(f"{RED}Failed Modules: {total_failures}{RESET}")
            print("\nHighest Risk Modules:")
            # Show top 3 highest failure rates
            for row in sorted(
                table_data,
                key=lambda x: float(
                    x[1]
                    .replace(GREEN, "")
                    .replace(YELLOW, "")
                    .replace(RED, "")
                    .replace(RESET, "")
                    .replace("%", "")
                ),
                reverse=True,
            )[:3]:
                print(f"- {row[0]}: {row[1]}")

    @classmethod
    def scan(
        cls,
        llmSpec: str,
        maxBudget: int = 1_000_000,
        datasets: list[dict] = REGISTRY,
        max_th: float = 0.3,
        optimize: bool = False,
        enableMultiStepAttack: bool = False,
        probe_datasets: list[dict] = [],
        only: list[str] = [],
    ):
        if only:
            datasets = [d for d in datasets if d["dataset_name"] in only]
            for d in datasets:
                d["selected"] = True
        return asyncio.run(
            cls.async_scan(
                llmSpec=llmSpec,
                maxBudget=maxBudget,
                datasets=datasets,
                max_th=max_th,
                optimize=optimize,
                enableMultiStepAttack=enableMultiStepAttack,
                probe_datasets=probe_datasets,
            )
        )
