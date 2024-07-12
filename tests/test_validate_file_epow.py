import pytest
from pathlib import Path
import sys
import os

# Add the root directory of the project to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.File import validate_file_epow

def test_validate_file_epow_cc():
    # Test for a valid short circuit (cc) file
    file_path = Path("tests/tests_inputs/30 Cycle Report ValidationTest.xlsx")
    file_path = Path("tests/tests_inputs/LV Momentary ValidationTest.xlsx")
    result = validate_file_epow(file_path)
    assert result == "CC"