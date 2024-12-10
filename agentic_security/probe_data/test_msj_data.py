from unittest.mock import patch, Mock

from agentic_security.probe_data.msj_data import (
    ProbeDataset,
    load_dataset_generic,
    prepare_prompts,
)


class TestProbeDataset:
    def test_metadata_summary(self):
        dataset = ProbeDataset(
            dataset_name="test_dataset",
            metadata={"key": "value"},
            prompts=["prompt1", "prompt2"],
            tokens=100,
            approx_cost=0.5,
        )

        expected_summary = {
            "dataset_name": "test_dataset",
            "num_prompts": 2,
            "tokens": 100,
            "approx_cost": 0.5,
        }

        assert dataset.metadata_summary() == expected_summary


class TestLoadDatasetGeneric:
    @patch("datasets.load_dataset")
    def test_load_dataset_success(self, mock_load_dataset):
        # Mock the dataset response
        mock_dataset = {"train": {"prompt": ["test prompt 1", "test prompt 2"]}}
        mock_load_dataset.return_value = mock_dataset

        result = load_dataset_generic("test/dataset")

        assert isinstance(result, ProbeDataset)
        assert result.dataset_name == "test/dataset"
        assert result.prompts == ["test prompt 1", "test prompt 2"]
        assert len(result.prompts) == 2

    @patch("datasets.load_dataset")
    def test_load_dataset_custom_getter(self, mock_load_dataset):
        mock_dataset = {"validation": {"text": ["custom text 1", "custom text 2"]}}
        mock_load_dataset.return_value = mock_dataset

        def custom_getter(x):
            return x["validation"]["text"]

        result = load_dataset_generic("test/dataset", getter=custom_getter)

        assert result.prompts == ["custom text 1", "custom text 2"]


class TestPreparePrompts:
    @patch("agentic_security.probe_data.msj_data.load_dataset_generic")
    def test_empty_dataset_names(self, mock_load_dataset_generic):
        # Mock the dataset responses
        mock_dataset1 = ProbeDataset(
            dataset_name="data-is-better-together/10k_prompts_ranked",
            metadata={},
            prompts=["prompt1"],
            tokens=0,
            approx_cost=0.0,
        )
        mock_dataset2 = ProbeDataset(
            dataset_name="fka/awesome-chatgpt-prompts",
            metadata={},
            prompts=["prompt2"],
            tokens=0,
            approx_cost=0.0,
        )
        mock_load_dataset_generic.side_effect = [mock_dataset1, mock_dataset2]

        result = prepare_prompts(dataset_names=[])
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(ds, ProbeDataset) for ds in result)

    @patch("agentic_security.probe_data.msj_data.load_dataset_generic")
    def test_known_dataset_names(self, mock_load_dataset_generic):
        # Mock the dataset responses
        mock_dataset1 = ProbeDataset(
            dataset_name="data-is-better-together/10k_prompts_ranked",
            metadata={},
            prompts=["prompt1"],
            tokens=0,
            approx_cost=0.0,
        )
        mock_dataset2 = ProbeDataset(
            dataset_name="fka/awesome-chatgpt-prompts",
            metadata={},
            prompts=["prompt2"],
            tokens=0,
            approx_cost=0.0,
        )
        mock_load_dataset_generic.side_effect = [mock_dataset1, mock_dataset2]

        result = prepare_prompts(
            dataset_names=[
                "data-is-better-together/10k_prompts_ranked",
                "fka/awesome-chatgpt-prompts",
            ]
        )
        assert len(result) == 2
        assert all(isinstance(ds, ProbeDataset) for ds in result)

    @patch("agentic_security.probe_data.msj_data.load_dataset_generic")
    def test_dataset_contents(self, mock_load_dataset_generic):
        # Mock the dataset responses
        mock_dataset1 = ProbeDataset(
            dataset_name="data-is-better-together/10k_prompts_ranked",
            metadata={"key": "value"},
            prompts=["test prompt"],
            tokens=100,
            approx_cost=0.5,
        )
        mock_dataset2 = ProbeDataset(
            dataset_name="fka/awesome-chatgpt-prompts",
            metadata={"key": "value"},
            prompts=["another prompt"],
            tokens=50,
            approx_cost=0.25,
        )
        mock_load_dataset_generic.side_effect = [mock_dataset1, mock_dataset2]

        result = prepare_prompts(
            dataset_names=["data-is-better-together/10k_prompts_ranked"]
        )
        assert len(result) == 2
        assert all(isinstance(ds.prompts, list) for ds in result)
        assert all(isinstance(ds.metadata, dict) for ds in result)
        assert result[0].prompts == ["test prompt"]
        assert result[1].prompts == ["another prompt"]
