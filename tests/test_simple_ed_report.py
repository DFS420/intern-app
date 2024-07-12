import pytest
import pandas as pd
import sys
import os

# Add the root directory of the project to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.eep.eepower_utils import simple_ed_report

def test_simple_ed_report():
    file_path = "tests/test_data/equipment_duty_file.xlsx"
    bus_exclus = []

    report = simple_ed_report(file_path, bus_exclus)
    print("Final columns:", report.columns)  # Debugging line to print the final columns of the DataFrame
    assert isinstance(report, pd.DataFrame)
    assert not report.empty

    # Verify necessary columns are present
    expected_columns = {
        "Bus", "Type de défault", "Bus (V)", "Manufacturier", "Style",
        "Standard de test", "Capacité pour 1/2 cycle (kA)", "Utilisation pour 1/2 cycle (kA)",
        "Utilisation pour 1/2 cycle (%)", "Commentaires"
    }
    actual_columns = set(report.columns)
    missing_columns = expected_columns - actual_columns
    extra_columns = actual_columns - expected_columns
    print("Expected columns:", expected_columns)
    print("Actual columns:", actual_columns)
    print("Missing columns:", missing_columns)
    print("Extra columns:", extra_columns)

    assert actual_columns == expected_columns

    # Verify the content of the index
    assert report.index.name == "Équipement"

if __name__ == "__main__":
    pytest.main()
