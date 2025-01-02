import importlib
import signal
import subprocess
import time

import pytest

import agentic_security.test_spec_assets as test_spec_assets
from agentic_security.lib import AgenticSecurity


def has_module(module_name):
    module_obj = importlib.util.find_spec(module_name)
    return module_obj is not None


@pytest.fixture(scope="module")
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
        llmSpec = test_spec_assets.SAMPLE_SPEC
        maxBudget = 1000000
        max_th = 0.3
        datasets = make_test_registry()
        result = AgenticSecurity.scan(llmSpec, maxBudget, datasets, max_th)
        assert isinstance(result, dict)
        print(result)
        assert len(result) in [0, 1]

    # TODO: slow test
    def _test_class_msj(self, test_server):
        llmSpec = test_spec_assets.SAMPLE_SPEC
        maxBudget = 1000
        max_th = 0.3
        datasets = make_test_registry()
        result = AgenticSecurity.scan(
            llmSpec, maxBudget, datasets, max_th, enableMultiStepAttack=True
        )
        assert isinstance(result, dict)
        print(result)
        assert len(result) in [0, 1]

    @pytest.mark.skipif(not has_module("garak"), reason="Garak module not installed")
    def _test_garak(self, test_server):
        llmSpec = test_spec_assets.SAMPLE_SPEC
        maxBudget = 1000000
        max_th = 0.3
        datasets = [
            {
                "dataset_name": "Garak",
                "num_prompts": 10,
                "tokens": 0,
                "approx_cost": 0.0,
                "source": "Github: https://github.com/leondz/garak#v0.9.0.1",
                "selected": True,
                "url": "https://github.com/leondz/garak2",
                "dynamic": True,
                "opts": {"port": 9094},
            },
        ]
        result = AgenticSecurity.scan(llmSpec, maxBudget, datasets, max_th)
        assert isinstance(result, dict)
        print(result)
        assert len(result) in [0, 1]

    def test_backend(self, test_server):
        llmSpec = test_spec_assets.SAMPLE_SPEC
        maxBudget = 1000000
        max_th = 0.3
        datasets = [
            {
                "dataset_name": "AgenticBackend",
                "num_prompts": 0,
                "tokens": 0,
                "approx_cost": 0.0,
                "source": "Fine-tuned cloud hosted model",
                "selected": True,
                "url": "",
                "dynamic": True,
                "opts": {
                    "port": 9094,
                    "modules": ["encoding"],
                },
                "modality": "text",
            },
        ]
        result = AgenticSecurity.scan(llmSpec, maxBudget, datasets, max_th)
        assert isinstance(result, dict)
        print(result)
        assert len(result) in [0, 1]
