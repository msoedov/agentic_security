import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pytest

from agentic_security.report_chart import plot_security_report, generate_identifiers

def test_generate_identifiers_short():
    """Test generate_identifiers for a short DataFrame with 3 rows."""
    df = pd.DataFrame({
        'failureRate': [10, 20, 30],
        'tokens': [100, 200, 300],
        'module': ['Module1', 'Module2', 'Module3']
    })
    ids = generate_identifiers(df)
    assert ids == ["A1", "A2", "A3"]

def test_generate_identifiers_long():
    """Test generate_identifiers for a longer DataFrame to validate wrapping of identifiers beyond 26 rows."""
    num_rows = 30
    data = {
        "failureRate": np.linspace(0, 100, num_rows),
        "tokens": np.linspace(50, 150, num_rows),
        "module": [f"module_{i}" for i in range(num_rows)]
    }
    df = pd.DataFrame(data)
    ids = generate_identifiers(df)
    assert ids[0] == "A1"
    # For row 26: letter index = 26//26 = 1, (26 %26)+1 = 1 so identifier is "B1"
    assert ids[26] == "B1"
    # For row 29: expected "B4"
    assert ids[29] == "B4"

def test_plot_security_report_output():
    """Test that plot_security_report returns a valid PNG image in a BytesIO object."""
    table = [
        {"failureRate": 50, "tokens": 100, "module": "ModuleA"},
        {"failureRate": 70, "tokens": 150, "module": "ModuleB"},
        {"failureRate": 30, "tokens": 80, "module": "ModuleC"}
    ]
    buf = plot_security_report(table)
    assert isinstance(buf, io.BytesIO)
    content = buf.getvalue()
    # PNG signature: 0x89 50 4E 47 0D 0A 1A 0A
    assert content.startswith(b'\211PNG\r\n\032\n')
    # Ensure that the output has a reasonable size
    assert len(content) > 1000

def test_plot_report_with_more_rows():
    """Test plot_security_report with multiple rows to ensure proper handling of angles and color mapping."""
    num_rows = 10
    table = []
    for i in range(num_rows):
        table.append({
            "failureRate": np.random.uniform(10, 90),
            "tokens": np.random.randint(50, 200),
            "module": f"Module_{i}"
        })
    buf = plot_security_report(table)
    content = buf.getvalue()
    assert content.startswith(b'\211PNG\r\n\032\n')
    assert len(content) > 1000

def test_plot_closure():
    """Test that the matplotlib figure is closed after generating the plot."""
    table = [{"failureRate": 40, "tokens": 120, "module": "ModuleX"}]
    buf = plot_security_report(table)
    # After plot generation, there should be no open matplotlib figures.
    assert plt.get_fignums() == []
def test_generate_identifiers_empty():
    """Test that generate_identifiers returns an empty list when given an empty DataFrame."""
    df = pd.DataFrame(columns=["failureRate", "tokens", "module"])
    ids = generate_identifiers(df)
    assert ids == []

def test_plot_security_report_empty():
    """Test that plot_security_report with an empty table raises a KeyError due to missing required columns."""
    with pytest.raises(KeyError):
        plot_security_report([])

def test_plot_security_report_missing_tokens():
    """Test that plot_security_report raises a KeyError when the 'tokens' field is missing."""
    table = [{"failureRate": 50, "module": "ModuleA"}]
    with pytest.raises(KeyError):
        plot_security_report(table)

def test_plot_security_report_missing_module():
    """Test that plot_security_report raises a KeyError when the 'module' field is missing."""
    table = [{"failureRate": 50, "tokens": 100}]
    with pytest.raises(KeyError):
        plot_security_report(table)

def test_plot_security_report_non_numeric():
    """Test that plot_security_report raises an error when non-numeric values are provided for 'failureRate' and 'tokens'."""
    table = [{"failureRate": "high", "tokens": "many", "module": "ModuleA"}]
    with pytest.raises(Exception):
        plot_security_report(table)
def test_generate_identifiers_exact_twenty_six():
    """Test generate_identifiers for a DataFrame with exactly 26 rows."""
    df = pd.DataFrame({
        'failureRate': list(range(26)),
        'tokens': list(range(26)),
        'module': [f'Module{i}' for i in range(26)]
    })
    ids = generate_identifiers(df)
    # The 26th row (index 25) should be "A26"
    assert ids[25] == "A26"

def test_plot_security_report_negative_failure_rate():
    """Test plot_security_report with a negative failureRate value to ensure valid output."""
    table = [
        {"failureRate": -20, "tokens": 80, "module": "ModuleNegative"},
        {"failureRate": 10, "tokens": 100, "module": "ModulePositive"}
    ]
    buf = plot_security_report(table)
    content = buf.getvalue()
    # Check PNG signature
    assert content.startswith(b'\211PNG\r\n\032\n')
    assert len(content) > 1000

def test_plot_security_report_with_equal_tokens():
    """Test plot_security_report with tokens having the same value to check normalization edge cases."""
    table = [
        {"failureRate": 30, "tokens": 100, "module": "Module1"},
        {"failureRate": 60, "tokens": 100, "module": "Module2"},
        {"failureRate": 45, "tokens": 100, "module": "Module3"}
    ]
    buf = plot_security_report(table)
    content = buf.getvalue()
    assert content.startswith(b'\211PNG\r\n\032\n')
    assert len(content) > 1000
def test_generate_identifiers_double_wrap():
    """Test generate_identifiers with 52 rows to validate wrapping of identifiers into two-letter sequences."""
    num_rows = 52
    data = {
        "failureRate": np.linspace(0, 100, num_rows),
        "tokens": np.linspace(10, 100, num_rows),
        "module": [f"module_{i}" for i in range(num_rows)]
    }
    df = pd.DataFrame(data)
    ids = generate_identifiers(df)
    assert ids[0] == "A1"
    assert ids[25] == "A26"
    assert ids[26] == "B1"
    assert ids[-1] == "B26"

def test_plot_security_report_dataframe_input():
    """Test that plot_security_report accepts a DataFrame as input and produces a valid PNG image."""
    # Create a DataFrame with the required columns.
    df = pd.DataFrame({
        "failureRate": [55, 65, 75],
        "tokens": [120, 130, 140],
        "module": ["ModuleDF1", "ModuleDF2", "ModuleDF3"]
    })
    buf = plot_security_report(df)
    assert isinstance(buf, io.BytesIO)
    content = buf.getvalue()
    # Verify the image is a PNG by checking its signature:
    assert content.startswith(b'\211PNG\r\n\032\n')
    # Check that the image has a reasonable size.
    assert len(content) > 1000