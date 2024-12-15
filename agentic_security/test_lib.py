import signal
import subprocess
import time

import pytest
from agentic_security.lib import AgenticSecurity

SAMPLE_SPEC = """
POST http://0.0.0.0:9094/v1/self-probe
Authorization: Bearer XXXXX
Content-Type: application/json

{
    "prompt": "<<PROMPT>>"
}
"""


@pytest.fixture(scope="session")
def test_server(request):
    # Start server process
    server = subprocess.Popen(
        ["uvicorn", "agentic_security.app:app", "--host", "0.0.0.0", "--port", "9094"],
        preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN),
    )

    # Give the server time to start
    time.sleep(2)

    def cleanup():
        server.terminate()
        server.wait()

    request.addfinalizer(cleanup)
    return server


def make_test_registry():
    return [
        {
            "dataset_name": "rubend18/ChatGPT-Jailbreak-Prompts",
            "num_prompts": 79,
            "tokens": 26971,
            "approx_cost": 0.0,
            "source": "Hugging Face Datasets",
            "selected": True,
            "dynamic": False,
            "url": "https://huggingface.co/rubend18/ChatGPT-Jailbreak-Prompts",
        },
    ]


class TestAS:
    # Handles an empty dataset list.
    def test_class(self, test_server):
        llmSpec = SAMPLE_SPEC
        maxBudget = 1000000
        max_th = 0.3
        datasets = make_test_registry()
        result = AgenticSecurity.scan(llmSpec, maxBudget, datasets, max_th)
        assert isinstance(result, dict)
        print(result)
        assert len(result) in [0, 1]

    # TODO: slow test
    def test_class_msj(self, test_server):
        llmSpec = SAMPLE_SPEC
        maxBudget = 1000
        max_th = 0.3
        datasets = make_test_registry()
        result = AgenticSecurity.scan(
            llmSpec, maxBudget, datasets, max_th, enableMultiStepAttack=True
        )
        assert isinstance(result, dict)
        print(result)
        assert len(result) in [0, 1]
