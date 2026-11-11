"""``agentic_security ci`` must fail a build when a module exceeds max_th."""

import pytest

from agentic_security.__main__ import CLI
from agentic_security.lib import SecurityScanner

CONFIG = {
    "general": {
        "llmSpec": "POST http://localhost\n\n{}",
        "maxBudget": 1_000_000,
        "max_th": 0.3,
        "optimize": False,
        "enableMultiStepAttack": False,
    },
    "modules": {"demo": {"dataset_name": "demo"}},
}

PASSING = {"demo": {"failure_rate": 10.0, "status": "PASS", "threshold": 30.0}}
FAILING = {
    "demo": {"failure_rate": 10.0, "status": "PASS", "threshold": 30.0},
    "jailbreak": {"failure_rate": 80.0, "status": "FAIL", "threshold": 30.0},
}


@pytest.fixture
def scanner(monkeypatch):
    """A scanner with config loading stubbed out and ``scan`` canned."""

    def configure(results):
        monkeypatch.setattr(SecurityScanner, "config", CONFIG)
        monkeypatch.setattr(SecurityScanner, "has_local_config", lambda self: True)
        monkeypatch.setattr(
            SecurityScanner, "load_config", classmethod(lambda cls, path: None)
        )
        monkeypatch.setattr(
            SecurityScanner, "scan", classmethod(lambda cls, **kwargs: results)
        )

    return configure


def test_entrypoint_returns_zero_when_every_module_passes(scanner):
    scanner(PASSING)

    assert SecurityScanner().entrypoint() == 0


def test_entrypoint_returns_one_when_a_module_fails(scanner):
    scanner(FAILING)

    assert SecurityScanner().entrypoint() == 1


def test_entrypoint_survives_a_scan_that_returns_nothing(scanner):
    """``scan`` returning None must not raise; treat it as nothing to report."""
    scanner(None)

    assert SecurityScanner().entrypoint() == 0


def test_ci_exits_nonzero_when_a_module_fails(scanner):
    scanner(FAILING)

    with pytest.raises(SystemExit) as excinfo:
        CLI().ci()

    assert excinfo.value.code == 1


def test_ci_exits_zero_when_every_module_passes(scanner):
    scanner(PASSING)

    with pytest.raises(SystemExit) as excinfo:
        CLI().ci()

    assert excinfo.value.code == 0
