import pandas as pd


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
        self, module_name: str, prompt: str, response_text: str, refused: bool
    ):
        """Add an output to the state"""
        self.outputs.append((module_name, prompt, response_text, refused))

    def get_last_output(self, prompt: str) -> str | None:
        """Get the last output for a given prompt"""
        for output in reversed(self.outputs):
            if output[1] == prompt:
                return output[2]
        return None

    def export_failures(self, filename: str = "failures.csv"):
        """Export failures to a CSV file"""
        failure_data = self.errors + self.refusals
        df = pd.DataFrame(
            failure_data, columns=["module", "prompt", "status_code", "content"]
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
                }
            )

        # Add all outputs (including successful ones)
        for module_name, prompt, response_text, refused in self.outputs:
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
                    }
                )

        df = pd.DataFrame(log_data)
        df.to_csv(filename, index=False)
