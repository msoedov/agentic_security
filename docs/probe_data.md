# Probe data

The `agentic_security.probe_data` package loads the attack datasets. It can also change the prompts and make image or audio attacks.

## Datasets

`agentic_security.probe_data.data`:

| Function | Description |
| --- | --- |
| `prepare_prompts` | Loads and transforms the selected registry datasets for a scan. |
| `load_dataset_generic` | Loads a CSV URL or a Hugging Face dataset into a `ProbeDataset`. |
| `load_local_csv` | Loads all CSV files in `./datasets` into one `ProbeDataset`. |
| `load_local_csv_files` | Loads each CSV file in `./datasets` into a separate `ProbeDataset`. |

`ProbeDataset` in `agentic_security.probe_data.models` keeps the prompts and the metadata of one dataset. `ImageProbeDataset` adds the images.

## Transforms

`agentic_security.probe_data.stenography_fn` has encoding functions, for example `rot13`, `base64_encode`, and `mirror_words`. Refer to [Stenography functions](stenography.md).

## Images and audio

- `generate_image` and `generate_image_dataset` in `probe_data.image_generator`. Refer to [Image generation](image_generation.md).
- `generate_audioform` in `probe_data.audio_generator`. It makes a WAV file. On macOS it uses the `say` command. On other systems it uses gTTS.

```python
from agentic_security.probe_data.audio_generator import generate_audioform

audio_bytes = generate_audioform("Hello, world!")
```

## Prompt selection

`probe_data.modules.rl_model` has prompt selectors. Refer to [RL prompt selection](rl_model.md).

```python
from agentic_security.probe_data.modules.rl_model import QLearningPromptSelector

selector = QLearningPromptSelector(["What is AI?", "Explain machine learning"])
next_prompt = selector.select_next_prompt("What is AI?", passed_guard=True)
selector.update_rewards("What is AI?", next_prompt, reward=1.0, passed_guard=True)
```
