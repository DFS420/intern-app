import pytest
import pandas as pd
import sys
import os

# Add the root directory of the project to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.eep.eepower_utils import simple_ed_report

def test_simple_ed_report():
    file_path = "tests/tests_inputs/equipment_duty_file.xlsx"
    bus_exclus = ["TEST"]

    report = simple_ed_report(file_path, bus_exclus)

    assert isinstance(report, pd.DataFrame)
    assert not report.empty
    assert report.index.name == "Équipement"

    expected_columns = ["Bus", "Type de défault", "Bus (V)", "Manufacturier", "Style", "Standard de test", "Capacité pour 1/2 cycle (kA)", "Utilisation pour 1/2 cycle (kA)", "Utilisation pour 1/2 cycle (%)", "Commentaires"]
    assert all(col in report.columns for col in expected_columns)

    assert report['Bus (V)'].dtype == float

    # Check that 'TEST' is not in the index (Équipement column)
    if bus_exclus:
        for bus in bus_exclus:
            assert not report.index.str.contains(bus).any()