# Dataset extension

You can add your prompts to a scan as local CSV files, or add a new dataset to the registry.

## Add local CSV files

1. Make a CSV file with a column that has the name `prompt`. Each row is one attack prompt.
2. Put the file in the `datasets` directory in the current directory.
3. Start the server or the scan from the same directory.

```bash
mkdir -p datasets
cp my_prompts.csv datasets/
```

The tool reads all `.csv` files in `datasets` when it starts. It shows the names of the files in the log.

> **NOTE:** The tool reads only CSV files. If a file does not have a `prompt` column, the tool shows a warning and ignores the file.

## Add a dataset to the registry

The registry is the list `REGISTRY` in `agentic_security/probe_data/__init__.py`. Add one entry for each dataset:

```python
{
    "dataset_name": "markush1/LLM-Jailbreak-Classifier",
    "num_prompts": 1119,
    "tokens": 19758,
    "approx_cost": 0.0,
    "source": "Hugging Face Datasets",
    "selected": True,
    "dynamic": False,
    "url": "https://huggingface.co/markush1/LLM-Jailbreak-Classifier",
},
```

The loaders in `agentic_security/probe_data/data.py` return a `ProbeDataset`. Refer to [Probe data](probe_data.md).

## Transformed datasets

The tool can make new datasets from the loaded prompts. It encodes a sample of the prompts with each function in [Stenography functions](stenography.md).
