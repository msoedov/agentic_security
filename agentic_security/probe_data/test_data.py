from inline_snapshot import snapshot

from .data import _normalize_google_sheets_url, prepare_prompts


class TestNormalizeGoogleSheetsUrl:
    def test_passthrough_non_sheets_url(self):
        url = "https://raw.githubusercontent.com/example/repo/main/data.csv"
        assert _normalize_google_sheets_url(url) == url

    def test_edit_url_converted_to_export(self):
        url = "https://docs.google.com/spreadsheets/d/ABC123/edit#gid=0"
        result = _normalize_google_sheets_url(url)
        assert "export?format=csv" in result
        assert "ABC123" in result
        assert "gid=0" in result

    def test_edit_url_no_gid(self):
        url = "https://docs.google.com/spreadsheets/d/ABC123/edit"
        result = _normalize_google_sheets_url(url)
        assert (
            result == "https://docs.google.com/spreadsheets/d/ABC123/export?format=csv"
        )

    def test_already_export_url_unchanged(self):
        url = "https://docs.google.com/spreadsheets/d/ABC123/export?format=csv"
        assert _normalize_google_sheets_url(url) == url

    def test_pub_csv_url_unchanged(self):
        url = "https://docs.google.com/spreadsheets/d/ABC123/pub?output=csv"
        assert _normalize_google_sheets_url(url) == url


class TestPreparePrompts:
    # Empty dataset_names input returns an empty list
    def test_empty_dataset_list(self):
        # Call the prepare_prompts function with an empty dataset_names list
        prepared_prompts = prepare_prompts([], 100)

        # Assert that the prepared_prompts list is empty
        assert prepared_prompts == []

        # assert len(
        #     prepare_prompts(["markush1/LLM-Jailbreak-Classifier"], 100)
        # ) == snapshot(1)

        assert len(
            prepare_prompts(
                ["llm-adaptive-attacks"],
                100,
            )
        ) == snapshot(1)
