import io

import matplotlib
import pytest
from inline_snapshot import snapshot

from agentic_security.report_chart import (
    _generate_identifiers,
    generate_identifiers,
    plot_security_report,
)


@pytest.fixture(autouse=True)
def use_agg_backend():
    matplotlib.use("Agg")


class TestGenerateIdentifiers:
    def test_single_row(self):
        data = type("DF", (), {"__len__": lambda s: 1})()
        result = _generate_identifiers(data)
        assert result == ["A1"]

    def test_multiple_rows(self):
        data = type("DF", (), {"__len__": lambda s: 5})()
        result = _generate_identifiers(data)
        assert result == ["A1", "A2", "A3", "A4", "A5"]

    def test_alphabet_wraparound(self):
        data = type("DF", (), {"__len__": lambda s: 27})()
        result = _generate_identifiers(data)
        assert result[0] == "A1"
        assert result[25] == "A26"
        assert result[26] == "B1"

    def test_empty_dataframe(self):
        data = type("DF", (), {"__len__": lambda s: 0})()
        result = _generate_identifiers(data)
        assert result == []

    def test_public_generate_identifiers(self):
        import pandas as pd

        df = pd.DataFrame({"a": [1, 2, 3]})
        result = generate_identifiers(df)
        assert result == ["A1", "A2", "A3"]


class TestPlotSecurityReport:
    def test_returns_bytesio(self):
        table_data = [
            {"module": "test", "failureRate": 10.0, "tokens": 100},
        ]
        result = plot_security_report(table_data)
        assert isinstance(result, io.BytesIO)

    def test_multiple_modules(self):
        table_data = [
            {"module": "mod_a", "failureRate": 5.0, "tokens": 50},
            {"module": "mod_b", "failureRate": 15.0, "tokens": 200},
            {"module": "mod_c", "failureRate": 25.0, "tokens": 500},
        ]
        result = plot_security_report(table_data)
        # A real plot was rendered: non-empty buffer carrying the PNG signature.
        png = result.getvalue()
        assert len(png) > 0
        assert png[:8] == snapshot(b"\x89PNG\r\n\x1a\n")

    def test_handles_empty_data(self):
        result = plot_security_report([])
        assert isinstance(result, io.BytesIO)

    def test_handles_missing_keys(self):
        table_data = [{"module": "test"}]
        result = plot_security_report(table_data)
        assert isinstance(result, io.BytesIO)

    def test_handles_none_values(self):
        table_data = [
            {"module": "test", "failureRate": None, "tokens": None},
        ]
        result = plot_security_report(table_data)
        assert isinstance(result, io.BytesIO)
