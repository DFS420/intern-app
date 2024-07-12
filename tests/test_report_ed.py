import pytest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import sys
import os

# Add the root directory of the project to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.eep.eep_traitement import report_ed

@patch('app.eep.eep_traitement.simple_ed_report')
def test_report_ed(mock_simple_ed_report):
    # Configure the mock to return a simulated DataFrame with necessary columns
    mock_simple_ed_report.return_value = pd.DataFrame({
        "Bus": ["Bus1", "Bus2"],
        "Équipement": ["Equip1", "Equip2"],
        "Type de défault": ["Type1", "Type2"],
        "Bus (V)": [13800, 480],
        "Manufacturier": ["Manuf1", "Manuf2"],
        "Style": ["Style1", "Style2"],
        "Standard de test": ["Standard1", "Standard2"],
        "Capacité pour 1/2 cycle (kA)": [50, 40],
        "Utilisation pour 1/2 cycle (kA)": [25, 20],
        "Utilisation pour 1/2 cycle (%)": [50, 50],
        "Commentaires": ["Comment1", "Comment2"]
    })

    data = {
        "FILES": [Path("tests/test_data/equipment_duty_file.xlsx")],
        "BUS_EXCLUS": []
    }
    target_rep = "tests/output"

    # Test normal operation
    xl_path, tex_path = report_ed(data, target_rep)
    assert xl_path.exists()
    assert tex_path.exists()

    # Test errors
    data["FILES"] = []
    with pytest.raises(FileNotFoundError):
        report_ed(data, target_rep)

if __name__ == "__main__":
    pytest.main()
