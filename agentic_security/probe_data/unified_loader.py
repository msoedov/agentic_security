"""Unified dataset loader for CSV, HuggingFace, and proxy sources."""

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field

from agentic_security.logutils import logger
from agentic_security.probe_data.data import (
    load_dataset_generic,
    load_csv,
    create_probe_dataset,
)
from agentic_security.probe_data.models import ProbeDataset


class InputSourceConfig(BaseModel):
    """Configuration for a single input source."""

    source_type: Literal["csv", "huggingface", "proxy"] = Field(
        description="Type of input source"
    )
    enabled: bool = Field(default=True, description="Whether this source is enabled")
    dataset_name: str = Field(description="Name/identifier of the dataset")
    weight: float = Field(default=1.0, ge=0.0, description="Sampling weight for merging")

    # CSV-specific fields
    path: Optional[str] = Field(
        default=None, description="File path for CSV sources"
    )
    prompt_column: Optional[str] = Field(
        default="prompt", description="Column name containing prompts"
    )

    # HuggingFace-specific fields
    split: Optional[str] = Field(
        default="train", description="Dataset split to load (train/test/validation)"
    )
    max_samples: Optional[int] = Field(
        default=None, ge=1, description="Maximum number of samples to load"
    )

    # URL for custom sources
    url: Optional[str] = Field(
        default=None, description="URL for remote CSV files"
    )


class UnifiedDatasetLoader:
    """Loads and merges datasets from multiple sources."""

    def __init__(self, configs: list[InputSourceConfig]):
        """Initialize with list of input source configurations.

        Args:
            configs: List of InputSourceConfig objects defining data sources
        """
        self.configs = configs
        logger.info(f"Initialized UnifiedDatasetLoader with {len(configs)} sources")

    async def load_all(self) -> ProbeDataset:
        """Load all enabled sources and merge into a single dataset.

        Returns:
            ProbeDataset: Merged dataset from all enabled sources
        """
        datasets = []

        for config in self.configs:
            if not config.enabled:
                logger.debug(f"Skipping disabled source: {config.dataset_name}")
                continue

            try:
                dataset = await self._load_single(config)
                if dataset and dataset.prompts:
                    datasets.append((dataset, config.weight))
                    logger.info(
                        f"Loaded {len(dataset.prompts)} prompts from {config.dataset_name} "
                        f"(weight={config.weight})"
                    )
                else:
                    logger.warning(f"No prompts loaded from {config.dataset_name}")
            except Exception as e:
                logger.error(f"Error loading {config.dataset_name}: {e}")

        if not datasets:
            logger.warning("No datasets loaded successfully")
            return create_probe_dataset("unified_empty", [], {"sources": []})

        return self._merge_weighted(datasets)

    async def _load_single(self, config: InputSourceConfig) -> ProbeDataset:
        """Load a single dataset based on its configuration.

        Args:
            config: Configuration for the source to load

        Returns:
            ProbeDataset: Loaded dataset
        """
        if config.source_type == "csv":
            return self._load_csv_source(config)
        elif config.source_type == "huggingface":
            return self._load_huggingface_source(config)
        elif config.source_type == "proxy":
            return self._load_proxy_source(config)
        else:
            raise ValueError(f"Unknown source type: {config.source_type}")

    def _load_csv_source(self, config: InputSourceConfig) -> ProbeDataset:
        """Load dataset from CSV file.

        Args:
            config: CSV source configuration

        Returns:
            ProbeDataset: Dataset loaded from CSV
        """
        if config.path:
            # Local CSV file
            logger.info(f"Loading CSV from path: {config.path}")
            dataset = load_csv(config.path)
        elif config.url:
            # Remote CSV file
            logger.info(f"Loading CSV from URL: {config.url}")
            mappings = {config.prompt_column: "prompt"} if config.prompt_column else None
            dataset = load_dataset_generic(
                name=config.dataset_name,
                url=config.url,
                mappings=mappings,
                metadata={"source_type": "csv", "url": config.url}
            )
        else:
            raise ValueError(f"CSV source {config.dataset_name} requires either path or url")

        # Apply max_samples limit if specified
        if config.max_samples and len(dataset.prompts) > config.max_samples:
            logger.info(
                f"Limiting {config.dataset_name} from {len(dataset.prompts)} "
                f"to {config.max_samples} samples"
            )
            dataset.prompts = dataset.prompts[:config.max_samples]

        return dataset

    def _load_huggingface_source(self, config: InputSourceConfig) -> ProbeDataset:
        """Load dataset from HuggingFace.

        Args:
            config: HuggingFace source configuration

        Returns:
            ProbeDataset: Dataset loaded from HuggingFace
        """
        logger.info(
            f"Loading HuggingFace dataset: {config.dataset_name} "
            f"(split={config.split})"
        )

        # Build column mappings
        mappings = None
        if config.prompt_column and config.prompt_column != "prompt":
            mappings = {config.prompt_column: "prompt"}

        dataset = load_dataset_generic(
            name=config.dataset_name,
            mappings=mappings,
            metadata={
                "source_type": "huggingface",
                "split": config.split,
            }
        )

        # Apply max_samples limit if specified
        if config.max_samples and len(dataset.prompts) > config.max_samples:
            logger.info(
                f"Limiting {config.dataset_name} from {len(dataset.prompts)} "
                f"to {config.max_samples} samples"
            )
            dataset.prompts = dataset.prompts[:config.max_samples]

        return dataset

    def _load_proxy_source(self, config: InputSourceConfig) -> ProbeDataset:
        """Load dataset from proxy queue (placeholder for PoC).

        Args:
            config: Proxy source configuration

        Returns:
            ProbeDataset: Empty dataset (proxy integration not implemented in PoC)
        """
        logger.warning(
            f"Proxy source {config.dataset_name} not implemented in PoC - returning empty dataset"
        )
        return create_probe_dataset(
            config.dataset_name,
            [],
            {"source_type": "proxy", "status": "not_implemented"}
        )

    def _merge_weighted(
        self, datasets: list[tuple[ProbeDataset, float]]
    ) -> ProbeDataset:
        """Merge multiple datasets with weighted sampling.

        For PoC, this implements simple concatenation with optional weighting.
        Production version would implement proper stratified sampling.

        Args:
            datasets: List of (ProbeDataset, weight) tuples

        Returns:
            ProbeDataset: Merged dataset
        """
        if not datasets:
            return create_probe_dataset("unified_empty", [], {"sources": []})

        # For PoC: simple concatenation, repeat prompts based on weight
        all_prompts = []
        source_names = []
        total_tokens = 0

        for dataset, weight in datasets:
            source_names.append(dataset.dataset_name)

            # Calculate how many times to include this dataset based on weight
            # Weight of 1.0 = include once, 2.0 = include twice, etc.
            repeat_count = max(1, int(weight))

            for _ in range(repeat_count):
                all_prompts.extend(dataset.prompts)

            total_tokens += dataset.tokens * repeat_count

        logger.info(
            f"Merged {len(datasets)} datasets into {len(all_prompts)} total prompts "
            f"from sources: {source_names}"
        )

        return ProbeDataset(
            dataset_name="unified",
            metadata={
                "sources": source_names,
                "source_count": len(datasets),
                "weights": {ds.dataset_name: w for ds, w in datasets},
            },
            prompts=all_prompts,
            tokens=total_tokens,
            approx_cost=0.0,
        )
