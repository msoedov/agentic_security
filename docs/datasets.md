# Dataset Extension

Agentic Security allows you to extend datasets to enhance its capabilities.

## Adding New Datasets

1. Place your dataset files in the `datasets` directory.
1. Ensure each file contains a `prompt` column for processing.

## Supported Formats

- CSV
- JSON
- Public Google Sheets links

## Example

To add a new dataset:

```bash
cp my_dataset.csv datasets/
```

## Google Sheets datasets

Public Google Sheets can be used as CSV-backed datasets. Share the sheet so it is viewable by link, keep a `prompt` column in the first row, and pass the sheet URL as a custom CSV source.

Agentic Security accepts the normal browser URL and converts it to the matching CSV export URL at load time:

```text
https://docs.google.com/spreadsheets/d/<sheet-id>/edit#gid=0
```

Example unified loader configuration:

```python
from agentic_security.probe_data.data import prepare_prompts_unified

datasets = await prepare_prompts_unified(
    [
        {
            "source_type": "csv",
            "dataset_name": "team-redteam-sheet",
            "url": "https://docs.google.com/spreadsheets/d/<sheet-id>/edit#gid=0",
            "prompt_column": "prompt",
        }
    ]
)
```

## Further Reading

For more details on dataset formats and processing, refer to the [API Reference](api_reference.md).
