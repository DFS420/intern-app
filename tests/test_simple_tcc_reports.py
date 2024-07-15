import pytest
import pandas as pd
from app.eep.eepower_utils import simple_tcc_reports


def test_simple_tcc_reports():
    # Create a mock Excel file or use a test data file
    test_file_path = "tests/tests_inputs/TCC_coordination_file.xlsx"

    # Call the function
    result = simple_tcc_reports(test_file_path)

    # Assert that the result is a dictionary
    assert isinstance(result, dict)

    # Assert that the dictionary contains the expected keys
    expected_keys = ["fuse", "magnetothermique", "electronique"]
    assert all(key in result for key in expected_keys)

    # Assert that each value in the dictionary is a pandas DataFrame
    for df in result.values():
        assert isinstance(df, pd.DataFrame)

    # Check specific columns for each DataFrame
    fuse_columns = ["Manufacturier", "Type", "Style", "Modèle", "V", "Calibre"]
    assert all(col in result["fuse"].columns.get_level_values(1) for col in fuse_columns)
    assert all(col[0] == 'Description' for col in result["fuse"].columns)

    electronique_columns = [
        "Manuf.", "Type", "Style", "Format", "entrée", "Réglage", "Décl.(A)", "Délais (s)"
    ]
    assert all(col in result["electronique"].columns.get_level_values(1) for col in electronique_columns)

    # Check for specific first-level column names
    assert set(result["electronique"].columns.get_level_values(0)) == {
        "Description", "Seuil long", "LT Delay", "Seuil court", "Instantané"
    }

    magnetothermique_columns = ["Manuf.", "Type", "Style", "Format", "décl.", "Ajust.", "Réglage", "Décl.(A)"]
    assert all(col in result["magnetothermique"].columns.get_level_values(1) for col in magnetothermique_columns)

    # Check for specific first-level column names
    assert set(result["magnetothermique"].columns.get_level_values(0)) == {"Description", "Instantané"}