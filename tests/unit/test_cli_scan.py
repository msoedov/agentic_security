import io
import json

import pytest

from agentic_security import cli_scan
from agentic_security import config
from agentic_security.primitives import ScanResult

SAMPLE_SPEC = """\
POST https://example.com/v1/chat
Content-Type: application/json

{"prompt": "<<PROMPT>>"}
"""


def test_load_spec_from_file(tmp_path):
    path = tmp_path / "target.http"
    path.write_text(SAMPLE_SPEC, encoding="utf-8")

    assert cli_scan.load_spec(str(path)) == SAMPLE_SPEC


def test_load_spec_from_stdin():
    assert cli_scan.load_spec("-", io.StringIO(SAMPLE_SPEC)) == SAMPLE_SPEC


def test_stateless_settings_do_not_create_a_config_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AGENTIC_SECURITY_STATELESS", "1")
    config._get_or_create_config.cache_clear()
    config._settings_var.cache_clear()

    assert config.settings_var("network.retry", 3) == 3
    assert not (tmp_path / "agentic_security.toml").exists()


def test_select_datasets_accepts_comma_separated_names():
    datasets = cli_scan.select_datasets(
        "deepset/prompt-injections, rubend18/ChatGPT-Jailbreak-Prompts"
    )

    assert [item["dataset_name"] for item in datasets] == [
        "deepset/prompt-injections",
        "rubend18/ChatGPT-Jailbreak-Prompts",
    ]
    assert all(item["selected"] for item in datasets)


def test_select_datasets_rejects_server_backed_dataset():
    with pytest.raises(cli_scan.CLIUsageError, match="requires the web server"):
        cli_scan.select_datasets("AgenticBackend")


@pytest.mark.asyncio
async def test_stream_scan_emits_json_lines_and_uses_final_failure_rate(monkeypatch):
    async def fake_scan_router(**kwargs):
        assert kwargs["artifacts_dir"] is None
        yield ScanResult(
            module="test-dataset",
            tokens=1,
            cost=0,
            progress=50,
            failureRate=50,
        ).model_dump_json()
        yield ScanResult(
            module="test-dataset",
            tokens=2,
            cost=0,
            progress=100,
            failureRate=20,
        ).model_dump_json()

    monkeypatch.setattr(cli_scan, "_scan_events", fake_scan_router)
    stdout = io.StringIO()

    exit_code = await cli_scan.stream_scan(
        spec_text=SAMPLE_SPEC,
        datasets=[{"dataset_name": "test-dataset", "selected": True}],
        max_budget=100,
        max_th=0.3,
        optimize=False,
        artifacts_dir=None,
        stdout=stdout,
    )

    events = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert [event["failureRate"] for event in events] == [50, 20]
    assert exit_code == cli_scan.EXIT_OK


@pytest.mark.asyncio
async def test_stream_scan_returns_findings_exit_code(monkeypatch):
    async def fake_scan_router(**kwargs):
        yield ScanResult(
            module="test-dataset",
            tokens=1,
            cost=0,
            progress=100,
            failureRate=40,
        ).model_dump_json()

    monkeypatch.setattr(cli_scan, "_scan_events", fake_scan_router)

    exit_code = await cli_scan.stream_scan(
        spec_text=SAMPLE_SPEC,
        datasets=[{"dataset_name": "test-dataset", "selected": True}],
        max_budget=100,
        max_th=0.3,
        optimize=False,
        artifacts_dir=None,
        stdout=io.StringIO(),
    )

    assert exit_code == cli_scan.EXIT_FINDINGS


@pytest.mark.asyncio
async def test_stream_scan_returns_error_for_runtime_failure(monkeypatch):
    async def fake_scan_router(**kwargs):
        yield ScanResult.status_msg("Scan failed: dataset unavailable")

    monkeypatch.setattr(cli_scan, "_scan_events", fake_scan_router)

    exit_code = await cli_scan.stream_scan(
        spec_text=SAMPLE_SPEC,
        datasets=[{"dataset_name": "test-dataset", "selected": True}],
        max_budget=100,
        max_th=0.3,
        optimize=False,
        artifacts_dir=None,
        stdout=io.StringIO(),
    )

    assert exit_code == cli_scan.EXIT_ERROR


@pytest.mark.asyncio
async def test_stream_scan_rejects_empty_results_and_deduplicates_completion(
    monkeypatch,
):
    async def fake_scan_router(**kwargs):
        yield ScanResult.status_msg("Scan completed.")
        yield ScanResult.status_msg("Scan completed.")

    monkeypatch.setattr(cli_scan, "_scan_events", fake_scan_router)
    stdout = io.StringIO()

    exit_code = await cli_scan.stream_scan(
        spec_text=SAMPLE_SPEC,
        datasets=[{"dataset_name": "test-dataset", "selected": True}],
        max_budget=100,
        max_th=0.3,
        optimize=False,
        artifacts_dir=None,
        stdout=stdout,
    )

    events = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert [event["module"] for event in events] == [
        "Scan failed: no dataset results.",
        "Scan completed.",
    ]
    assert exit_code == cli_scan.EXIT_ERROR


def test_run_scan_command_reports_usage_errors_without_stdout():
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = cli_scan.run_scan_command(
        spec=SAMPLE_SPEC,
        dataset="not-a-real-dataset",
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == cli_scan.EXIT_ERROR
    assert stdout.getvalue() == ""
    assert "Unknown dataset" in stderr.getvalue()
