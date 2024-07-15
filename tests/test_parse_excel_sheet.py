import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Add the root directory of the project to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.eep.eepower_utils import parse_excel_sheet

TEST_FILE_PATH = Path(__file__).parent / "tests_inputs" / "TCC_coordination_file.xlsx"


def test_parse_excel_sheet():
    result = parse_excel_sheet(TEST_FILE_PATH)
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(df, pd.DataFrame) for df in result)


def test_parse_excel_sheet_file_not_found():
    non_existent_file = Path("non_existent_file.xlsx")

    with pytest.raises(FileNotFoundError):
        parse_excel_sheet(non_existent_file)