from inline_snapshot import snapshot

from .data import ProbeDataset, prepare_prompts


class TestPreparePrompts:
    # Empty dataset_names input returns an empty list
    def test_empty_dataset_list(self):
        # Call the prepare_prompts function with an empty dataset_names list
        prepared_prompts = prepare_prompts([], 100)

        # Assert that the prepared_prompts list is empty
        assert prepared_prompts == []

        assert len(
            prepare_prompts(["markush1/LLM-Jailbreak-Classifier"], 100)
        ) == snapshot(1)

        assert len(
            prepare_prompts(
                ["markush1/LLM-Jailbreak-Classifier", "llm-adaptive-attacks"],
                100,
            )
        ) == snapshot(2)
