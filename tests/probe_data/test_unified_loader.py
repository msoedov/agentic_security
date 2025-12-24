"""Tests for unified dataset loader."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from agentic_security.probe_data.unified_loader import (
    InputSourceConfig,
    UnifiedDatasetLoader,
)
from agentic_security.probe_data.models import ProbeDataset


class TestInputSourceConfig:
    """Test InputSourceConfig validation."""

    def test_csv_source_config(self):
        """Test CSV source configuration."""
        config = InputSourceConfig(
            source_type="csv",
            dataset_name="test_csv",
            path="./test.csv",
            prompt_column="prompt",
            weight=1.5,
        )
        assert config.source_type == "csv"
        assert config.dataset_name == "test_csv"
        assert config.path == "./test.csv"
        assert config.weight == 1.5

    def test_huggingface_source_config(self):
        """Test HuggingFace source configuration."""
        config = InputSourceConfig(
            source_type="huggingface",
            dataset_name="test/dataset",
            split="train",
            max_samples=100,
        )
        assert config.source_type == "huggingface"
        assert config.split == "train"
        assert config.max_samples == 100

    def test_proxy_source_config(self):
        """Test proxy source configuration."""
        config = InputSourceConfig(
            source_type="proxy",
            dataset_name="proxy_test",
        )
        assert config.source_type == "proxy"
        assert config.enabled is True  # Default value

    def test_disabled_source(self):
        """Test disabled source configuration."""
        config = InputSourceConfig(
            source_type="csv",
            dataset_name="disabled_test",
            enabled=False,
        )
        assert config.enabled is False

    def test_weight_validation(self):
        """Test that weight must be non-negative."""
        with pytest.raises(ValueError):
            InputSourceConfig(
                source_type="csv",
                dataset_name="test",
                weight=-1.0,
            )


class TestUnifiedDatasetLoader:
    """Test UnifiedDatasetLoader functionality."""

    @pytest.mark.asyncio
    async def test_load_single_csv_source(self):
        """Test loading a single CSV source."""
        config = InputSourceConfig(
            source_type="csv",
            dataset_name="test_csv",
            path="test.csv",
        )
        loader = UnifiedDatasetLoader([config])

        # Mock the load_csv function
        mock_dataset = ProbeDataset(
            dataset_name="test_csv",
            prompts=["prompt1", "prompt2", "prompt3"],
            tokens=10,
            approx_cost=0.0,
            metadata={}
        )

        with patch(
            "agentic_security.probe_data.unified_loader.load_csv",
            return_value=mock_dataset
        ):
            result = await loader.load_all()

        assert result.dataset_name == "unified"
        assert len(result.prompts) == 3
        assert result.prompts == ["prompt1", "prompt2", "prompt3"]

    @pytest.mark.asyncio
    async def test_load_single_huggingface_source(self):
        """Test loading a single HuggingFace source."""
        config = InputSourceConfig(
            source_type="huggingface",
            dataset_name="test/dataset",
            split="train",
        )
        loader = UnifiedDatasetLoader([config])

        # Mock the load_dataset_generic function
        mock_dataset = ProbeDataset(
            dataset_name="test/dataset",
            prompts=["hf_prompt1", "hf_prompt2"],
            tokens=8,
            approx_cost=0.0,
            metadata={}
        )

        with patch(
            "agentic_security.probe_data.unified_loader.load_dataset_generic",
            return_value=mock_dataset
        ):
            result = await loader.load_all()

        assert result.dataset_name == "unified"
        assert len(result.prompts) == 2

    @pytest.mark.asyncio
    async def test_merge_multiple_sources(self):
        """Test merging multiple sources."""
        configs = [
            InputSourceConfig(
                source_type="csv",
                dataset_name="csv1",
                path="test1.csv",
                weight=1.0,
            ),
            InputSourceConfig(
                source_type="csv",
                dataset_name="csv2",
                path="test2.csv",
                weight=2.0,
            ),
        ]
        loader = UnifiedDatasetLoader(configs)

        # Mock datasets
        mock_dataset1 = ProbeDataset(
            dataset_name="csv1",
            prompts=["prompt1"],
            tokens=5,
            approx_cost=0.0,
            metadata={}
        )
        mock_dataset2 = ProbeDataset(
            dataset_name="csv2",
            prompts=["prompt2", "prompt3"],
            tokens=10,
            approx_cost=0.0,
            metadata={}
        )

        with patch(
            "agentic_security.probe_data.unified_loader.load_csv",
            side_effect=[mock_dataset1, mock_dataset2]
        ):
            result = await loader.load_all()

        assert result.dataset_name == "unified"
        # Weight 1.0 = include once, weight 2.0 = include twice
        # csv1: 1 prompt * 1 = 1
        # csv2: 2 prompts * 2 = 4
        assert len(result.prompts) == 5
        assert "csv1" in result.metadata["sources"]
        assert "csv2" in result.metadata["sources"]

    @pytest.mark.asyncio
    async def test_handle_disabled_sources(self):
        """Test that disabled sources are skipped."""
        configs = [
            InputSourceConfig(
                source_type="csv",
                dataset_name="enabled_csv",
                path="enabled.csv",
                enabled=True,
            ),
            InputSourceConfig(
                source_type="csv",
                dataset_name="disabled_csv",
                path="disabled.csv",
                enabled=False,
            ),
        ]
        loader = UnifiedDatasetLoader(configs)

        mock_dataset = ProbeDataset(
            dataset_name="enabled_csv",
            prompts=["prompt1"],
            tokens=5,
            approx_cost=0.0,
            metadata={}
        )

        with patch(
            "agentic_security.probe_data.unified_loader.load_csv",
            return_value=mock_dataset
        ) as mock_load:
            result = await loader.load_all()

        # Should only be called once (for enabled source)
        assert mock_load.call_count == 1
        assert len(result.prompts) == 1

    @pytest.mark.asyncio
    async def test_max_samples_limit(self):
        """Test that max_samples limits the number of prompts."""
        config = InputSourceConfig(
            source_type="csv",
            dataset_name="test_csv",
            path="test.csv",
            max_samples=2,
        )
        loader = UnifiedDatasetLoader([config])

        # Mock dataset with more prompts than max_samples
        mock_dataset = ProbeDataset(
            dataset_name="test_csv",
            prompts=["prompt1", "prompt2", "prompt3", "prompt4", "prompt5"],
            tokens=20,
            approx_cost=0.0,
            metadata={}
        )

        with patch(
            "agentic_security.probe_data.unified_loader.load_csv",
            return_value=mock_dataset
        ):
            result = await loader.load_all()

        # Should be limited to 2 prompts
        assert len(result.prompts) == 2

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test that errors are handled gracefully."""
        config = InputSourceConfig(
            source_type="csv",
            dataset_name="error_csv",
            path="nonexistent.csv",
        )
        loader = UnifiedDatasetLoader([config])

        with patch(
            "agentic_security.probe_data.unified_loader.load_csv",
            side_effect=Exception("File not found")
        ):
            result = await loader.load_all()

        # Should return empty dataset on error
        assert result.dataset_name == "unified_empty"
        assert len(result.prompts) == 0

    @pytest.mark.asyncio
    async def test_proxy_source_placeholder(self):
        """Test that proxy source returns empty dataset (not implemented in PoC)."""
        config = InputSourceConfig(
            source_type="proxy",
            dataset_name="proxy_test",
        )
        loader = UnifiedDatasetLoader([config])

        result = await loader.load_all()

        # Proxy not implemented in PoC, should return empty
        assert len(result.prompts) == 0

    @pytest.mark.asyncio
    async def test_weighted_sampling(self):
        """Test weighted sampling behavior."""
        configs = [
            InputSourceConfig(
                source_type="csv",
                dataset_name="low_weight",
                path="low.csv",
                weight=1.0,
            ),
            InputSourceConfig(
                source_type="csv",
                dataset_name="high_weight",
                path="high.csv",
                weight=3.0,
            ),
        ]
        loader = UnifiedDatasetLoader(configs)

        mock_dataset1 = ProbeDataset(
            dataset_name="low_weight",
            prompts=["a"],
            tokens=1,
            approx_cost=0.0,
            metadata={}
        )
        mock_dataset2 = ProbeDataset(
            dataset_name="high_weight",
            prompts=["b"],
            tokens=1,
            approx_cost=0.0,
            metadata={}
        )

        with patch(
            "agentic_security.probe_data.unified_loader.load_csv",
            side_effect=[mock_dataset1, mock_dataset2]
        ):
            result = await loader.load_all()

        # Weight 1.0: 1 prompt * 1 = 1
        # Weight 3.0: 1 prompt * 3 = 3
        # Total: 4 prompts
        assert len(result.prompts) == 4
        assert result.prompts.count("a") == 1
        assert result.prompts.count("b") == 3

    @pytest.mark.asyncio
    async def test_empty_configs_list(self):
        """Test loading with empty configs list."""
        loader = UnifiedDatasetLoader([])
        result = await loader.load_all()

        assert result.dataset_name == "unified_empty"
        assert len(result.prompts) == 0

    @pytest.mark.asyncio
    async def test_csv_with_url(self):
        """Test CSV loading from URL."""
        config = InputSourceConfig(
            source_type="csv",
            dataset_name="remote_csv",
            url="https://example.com/data.csv",
            prompt_column="text",
        )
        loader = UnifiedDatasetLoader([config])

        mock_dataset = ProbeDataset(
            dataset_name="remote_csv",
            prompts=["remote_prompt"],
            tokens=5,
            approx_cost=0.0,
            metadata={"source_type": "csv", "url": "https://example.com/data.csv"}
        )

        with patch(
            "agentic_security.probe_data.unified_loader.load_dataset_generic",
            return_value=mock_dataset
        ):
            result = await loader.load_all()

        assert len(result.prompts) == 1
        assert result.prompts[0] == "remote_prompt"
