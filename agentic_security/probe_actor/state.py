import pandas as pd

from agentic_security.probe_actor.outcome import FINDING_OUTCOMES, Outcome


class FuzzerState:
    """Container for tracking scan results"""

    def __init__(self):
        self.errors = []
        self.refusals = []
        self.outputs = []

    def add_error(
        self,
        module_name: str,
        prompt: str,
        status_code: int | str,
        error_msg: str,
    ):
        """Add an error to the state"""
        self.errors.append((module_name, prompt, status_code, error_msg))

    def add_refusal(
        self, module_name: str, prompt: str, status_code: int, response_text: str
    ):
        """Add a refusal to the state"""
        self.refusals.append((module_name, prompt, status_code, response_text))

    def add_output(
        self,
        module_name: str,
        prompt: str,
        response_text: str,
        refused: bool,
        outcome: Outcome | None = None,
    ):
        """Add an output to the state"""
        if outcome is None:
            outcome = Outcome.REFUSED if refused else Outcome.COMPLIED
        self.outputs.append((module_name, prompt, response_text, refused, outcome))

    def get_last_output(self, prompt: str) -> str | None:
        """Get the last output for a given prompt"""
        for output in reversed(self.outputs):
            if output[1] == prompt:
                return output[2]
        return None

    def findings(self) -> list[tuple]:
        """Outputs where the attack succeeded (complied or partial)."""
        return [o for o in self.outputs if o[4] in FINDING_OUTCOMES]

    def export_failures(self, filename: str = "failures.csv"):
        """Export findings (attacks the target did not refuse) to a CSV file."""
        failure_data = [
            (module_name, prompt, str(outcome), response_text)
            for module_name, prompt, response_text, _, outcome in self.findings()
        ]
        df = pd.DataFrame(
            failure_data, columns=["module", "prompt", "outcome", "content"]
        )
        df.to_csv(filename, index=False)

    def export_full_log(self, filename: str = "full_scan_log.csv"):
        """Export a complete log of all events (errors, refusals, and successful outputs)"""
        log_data = []

        # Add errors
        for module_name, prompt, status_code, error_msg in self.errors:
            log_data.append(
                {
                    "event_type": "error",
                    "module": module_name,
                    "prompt": prompt,
                    "status_code": status_code,
                    "content": error_msg,
                    "refused": None,
                    "outcome": str(Outcome.ERROR),
                }
            )

        # Add refusals
        for module_name, prompt, status_code, response_text in self.refusals:
            log_data.append(
                {
                    "event_type": "refusal",
                    "module": module_name,
                    "prompt": prompt,
                    "status_code": status_code,
                    "content": response_text,
                    "refused": True,
                    "outcome": str(Outcome.REFUSED),
                }
            )

        # Add all outputs (including successful ones)
        for module_name, prompt, response_text, refused, outcome in self.outputs:
            # Skip if already logged as refusal to avoid duplicates
            if not refused:
                log_data.append(
                    {
                        "event_type": "success",
                        "module": module_name,
                        "prompt": prompt,
                        "status_code": 200,
                        "content": response_text,
                        "refused": False,
                        "outcome": str(outcome),
                    }
                )

        df = pd.DataFrame(log_data)
        df.to_csv(filename, index=False)
