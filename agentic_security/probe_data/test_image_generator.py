from unittest.mock import patch

import pytest

from agentic_security.probe_data.image_generator import (
    generate_image,
    generate_image_dataset,
)
from agentic_security.probe_data.models import ImageProbeDataset, ProbeDataset


@pytest.mark.parametrize("variant", [0, 1, 2, 3])
def test_generate_image(variant):
    prompt = "Test prompt"
    image_bytes = generate_image(prompt, variant)

    assert isinstance(image_bytes, bytes)
    assert len(image_bytes) > 0


@patch("agentic_security.probe_data.image_generator.generate_image")
def test_generate_image_dataset(mock_generate_image):
    mock_generate_image.return_value = b"dummy_image_bytes"

    prompt = "Test prompt"
    test_dataset_name = "test_dataset"
    test_datasets = [
        ProbeDataset(
            dataset_name=test_dataset_name,
            prompts=[prompt],
            metadata={},
            tokens=[],
            approx_cost=0.0,
        )
    ]
    image_datasets = generate_image_dataset(test_datasets)

    assert len(image_datasets) == 1
    assert isinstance(image_datasets[0], ImageProbeDataset)
    assert image_datasets[0].test_dataset.dataset_name == test_dataset_name
    assert image_datasets[0].image_prompts[0] == b"dummy_image_bytes"
