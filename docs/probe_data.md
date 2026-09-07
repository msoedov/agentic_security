# Probe data

The `probe_data` package loads attack datasets, optionally transforms prompts,
and can generate image or audio payloads for multi-modal specs.

## Datasets

`agentic_security.probe_data.data`:

- `load_dataset_generic` — load a CSV URL or Hugging Face dataset into a `ProbeDataset`
- `load_local_csv` / `load_local_csv_files` — datasets from local CSV files
- `prepare_prompts` — select and transform registry datasets for a scan

`agentic_security.probe_data.models.ProbeDataset` is the in-memory dataset type.
Image datasets wrap that as `ImageProbeDataset`.

## Transforms

`agentic_security.probe_data.stenography_fn` provides encoding helpers such as
`rot13`, `base64_encode`, and `mirror_words`. See [stenography](stenography.md).

## Image and audio

- `generate_image` / `generate_image_dataset` in `probe_data.image_generator`
- `generate_audioform` in `probe_data.audio_generator`

```python
from agentic_security.probe_data.audio_generator import generate_audioform

audio_bytes = generate_audioform("Hello, world!")
```

## Prompt selection

`probe_data.modules.rl_model` implements `PromptSelectionInterface` with
`RandomPromptSelector`, `CloudRLPromptSelector`, and `QLearningPromptSelector`.
`update_rewards` returns `None`. Boolean arguments are Python `True` / `False`.

```python
from agentic_security.probe_data.modules.rl_model import QLearningPromptSelector

selector = QLearningPromptSelector(["What is AI?", "Explain machine learning"])
next_prompt = selector.select_next_prompt("What is AI?", passed_guard=True)
selector.update_rewards("What is AI?", next_prompt, reward=1.0, passed_guard=True)
```

See [RL model](rl_model.md) for the selector options.
