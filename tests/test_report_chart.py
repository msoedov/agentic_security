import io
import string
import pytest
import pandas as pd
import numpy as np
from agentic_security.report_chart import plot_security_report, generate_identifiers

class TestReportChart:
    """Test suite for agentic_security.report_chart module."""

    def test_generate_identifiers_short(self):
        """Test generate_identifiers with a small dataset."""
        df = pd.DataFrame([{'dummy': i} for i in range(5)])
        identifiers = generate_identifiers(df)
        expected = ['A1', 'A2', 'A3', 'A4', 'A5']
        assert identifiers == expected

    def test_generate_identifiers_edge(self):
        """Test generate_identifiers with more than 26 items to cover cycling over the alphabet."""
        n = 30
        df = pd.DataFrame([{'dummy': i} for i in range(n)])
        identifiers = generate_identifiers(df)
        # For i=25, identifier should be A26, and for i=26, identifier should be B1
        assert identifiers[25] == 'A26'
        assert identifiers[26] == 'B1'
        assert len(identifiers) == n

    def test_generate_identifiers_empty(self):
        """Test generate_identifiers with an empty dataframe."""
        df = pd.DataFrame([])
        identifiers = generate_identifiers(df)
        assert identifiers == []

    def test_plot_security_report_png_output(self):
        """Test plot_security_report returns valid PNG output."""
        # Create a sample table with required columns
        table = [
            {"failureRate": 10, "tokens": 100, "module": "Module1"},
            {"failureRate": 30, "tokens": 200, "module": "Module2"},
            {"failureRate": 20, "tokens": 150, "module": "Module3"},
        ]
        buf = plot_security_report(table)
        # Check that buf is a BytesIO object and starts with PNG header bytes
        assert isinstance(buf, io.BytesIO)
        buf.seek(0)
        header = buf.read(8)
        assert header.startswith(b'\x89PNG')

    def test_plot_security_report_ordering(self, monkeypatch):
        """Test that the table embedded in the plot contains correctly sorted order by descending failure rate."""
        table = [
            {"failureRate": 15, "tokens": 110, "module": "ModuleA"},
            {"failureRate": 25, "tokens": 210, "module": "ModuleB"},
            {"failureRate": 5,  "tokens": 90,  "module": "ModuleC"},
        ]
        result_holder = {}
        from matplotlib.axes import Axes
        original_table = Axes.table
        def fake_table(self, *args, **kwargs):
            result_holder['cellText'] = kwargs.get('cellText')
            return original_table(self, *args, **kwargs)
        monkeypatch.setattr(Axes, "table", fake_table)
        plot_security_report(table)
        cell_text = result_holder.get('cellText')
        assert cell_text is not None
        # Verify header row in the table
        assert cell_text[0] == ["Threat"]
        # Since the data are sorted (highest failure rate first), ModuleB (25.0%) should appear in one of the rows.
        found = any("ModuleB (25.0%)" in row[0] for row in cell_text[1:])
        assert found

    def test_plot_security_report_one_entry(self):
        """Test plot_security_report with a single entry."""
        table = [{"failureRate": 50, "tokens": 300, "module": "OnlyModule"}]
        buf = plot_security_report(table)
        assert isinstance(buf, io.BytesIO)
        buf.seek(0)
        content = buf.read()
        assert content.startswith(b'\x89PNG')
    def test_generate_identifiers_many(self):
        """Test generate_identifiers with 52 items to verify identifier sequence."""
        n = 52
        df = pd.DataFrame([{'dummy': i} for i in range(n)])
        identifiers = generate_identifiers(df)
        assert identifiers[0] == "A1"
        assert identifiers[25] == "A26"
        assert identifiers[26] == "B1"
        assert identifiers[51] == "B26"

    def test_plot_security_report_missing_failureRate(self):
        """Test plot_security_report raises KeyError when 'failureRate' column is missing."""
        table = [{"tokens": 100, "module": "Mod1"}]  # Missing 'failureRate'
        with pytest.raises(KeyError):
            plot_security_report(table)

    def test_plot_security_report_missing_tokens(self):
        """Test plot_security_report raises KeyError when 'tokens' column is missing."""
        table = [{"failureRate": 10, "module": "Mod1"}]  # Missing 'tokens'
        with pytest.raises(KeyError):
            plot_security_report(table)

    def test_plot_security_report_empty_table(self):
        """Test plot_security_report raises KeyError when the table is empty."""
        table = []
        with pytest.raises(KeyError):
            plot_security_report(table)
    def test_plot_security_report_missing_module(self):
        """Test plot_security_report raises KeyError when 'module' column is missing."""
        table = [{"failureRate": 10, "tokens": 100}]  # Missing 'module'
        with pytest.raises(KeyError):
            plot_security_report(table)

    def test_plot_security_report_failure_rate_labels(self, monkeypatch):
        """Test that plot_security_report calls ax.text for each failure rate bar label."""
        table = [
            {"failureRate": 10, "tokens": 100, "module": "Mod1"},
            {"failureRate": 20, "tokens": 150, "module": "Mod2"},
            {"failureRate": 30, "tokens": 200, "module": "Mod3"},
        ]
        # Count the number of times ax.text is called for drawing failure rate labels.
        call_count = [0]
        from matplotlib.axes import Axes
        original_text = Axes.text
        def fake_text(self, *args, **kwargs):
            call_count[0] += 1
            return original_text(self, *args, **kwargs)
        monkeypatch.setattr(Axes, "text", fake_text)
        plot_security_report(table)
        # The loop inside plot_security_report calls ax.text once for each data point.
        assert call_count[0] == len(table)

    def test_plot_security_report_non_numeric_failureRate(self):
        """Test that plot_security_report raises an exception when failureRate is non-numeric."""
        table = [{"failureRate": "invalid", "tokens": 100, "module": "ModX"}]
        with pytest.raises(Exception):
            plot_security_report(table)