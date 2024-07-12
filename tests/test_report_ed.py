import pytest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import sys
import os

# Add the root directory of the project to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.eep.eep_traitement import report_ed

def test_report_ed():
    # Set up test data
    data = {
        "BUS_EXCLUS": ["TEST"],
        "FILES": [Path("tests/tests_inputs/equipment_duty_file.xlsx")]
    }
    target_rep = "tests/tests_outputs"

    # Call the function
    xl_path, tex_path = report_ed(data, target_rep)

    # Check if the output files exist
    assert xl_path.exists()
    assert tex_path.exists()

    # Check if the file names are correct
    assert xl_path.name == "eep-ed-output.xlsx"
    assert tex_path.name == "tab_ed.tex"

    # Check Excel file content
    df = pd.read_excel(xl_path, index_col=0)
    assert not df.empty
    assert "Bus" in df.columns
    assert "Bus (V)" in df.columns

    if data["BUS_EXCLUS"]:
        for bus in data["BUS_EXCLUS"]:
            assert not df.index.str.contains(bus).any()