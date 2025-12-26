import importlib
import os
import signal
import socket
import subprocess
import tempfile
import time

import pytest

import agentic_security.test_spec_assets as test_spec_assets
from agentic_security.lib import SecurityScanner


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

    def wait_for_port(host: str, port: int, timeout: float = 5.0) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.2)
                try:
                    sock.connect((host, port))
                    return True
                except OSError:
                    time.sleep(0.1)
        return False

    if not wait_for_port("127.0.0.1", 9094):
        server.kill()
        pytest.skip("Test server failed to start within timeout")

    def cleanup():
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=2)

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


class TestLibraryLevel:
    # Handles an empty dataset list.
    def test_class(self, test_server):
        llmSpec = test_spec_assets.SAMPLE_SPEC
        maxBudget = 1000000
        max_th = 0.3
        datasets = make_test_registry()
        result = SecurityScanner.scan(llmSpec, maxBudget, datasets, max_th)
        assert isinstance(result, dict)
        print(result)
        assert len(result) in [0, 1]

    @pytest.mark.slow
    def test_class_msj(self, test_server):
        llmSpec = test_spec_assets.SAMPLE_SPEC
        maxBudget = 1000
        max_th = 0.3
        datasets = make_test_registry()
        result = SecurityScanner.scan(
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
        result = SecurityScanner.scan(llmSpec, maxBudget, datasets, max_th)
        assert isinstance(result, dict)
        print(result)
        assert len(result) in [0, 1]

    @pytest.mark.slow
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
        result = SecurityScanner.scan(llmSpec, maxBudget, datasets, max_th)
        assert isinstance(result, dict)
        print(result)
        assert len(result) in [0, 1]

    @pytest.mark.skip
    def test_image_modality(self):
        llmSpec = test_spec_assets.IMAGE_SPEC
        maxBudget = 2
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
                    # "port": 8718,
                    "port": 9094,
                    "modules": ["encoding"],
                    "max_prompts": 2,
                },
                "modality": "text",
            },
        ]
        result = SecurityScanner.scan(llmSpec, maxBudget, datasets, max_th)
        assert isinstance(result, dict)
        print(result)
        assert len(result) in [0, 1]


class TestEntrypointCI:
    def test_generate_default_cfg_to_tmp_path(self):
        """
        Test that the `generate_default_settings` method generates a valid default config file in a temporary path.
        """
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = os.path.join(tmpdir, "custom_agesec.toml")

            # Override default_path to the temporary path
            SecurityScanner.default_path = temp_path

            # Generate the default configuration
            security = SecurityScanner()
            security.generate_default_settings()

            # Check that the config file was created at the temporary path
            assert os.path.exists(temp_path), f"{temp_path} file should be generated."

            # Validate the contents of the generated config file
            with open(temp_path) as f:
                generated_content = f.read()
                assert (
                    "maxBudget = 1000000" in generated_content
                ), "maxBudget should be 1000000"

    def test_load_generated_tmp_config(self):
        """
        Test that the configuration generated in a temporary path can be loaded successfully.
        """
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = os.path.join(tmpdir, "custom_agesec.toml")

            # Override default_path to the temporary path
            SecurityScanner.default_path = temp_path

            # Generate the default configuration
            security = SecurityScanner()
            security.generate_default_settings()

            # Load the generated configuration
            SecurityScanner.load_config(temp_path)

            # Validate loaded configuration
            config = SecurityScanner.config
            assert (
                config["general"]["maxBudget"] == 1000000
            ), "maxBudget should be 1000000"
            assert config["general"]["max_th"] == 0.3, "max_th should be 0.3"
            assert (
                config["modules"]["AgenticBackend"]["dataset_name"] == "AgenticBackend"
            ), "Dataset name should be 'AgenticBackend'"
