import pytest
from pathlib import Path
import sys
import os

# Add the root directory of the project to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.File import validate_file_epow, FileError


def test_validate_file_epow_cc():
    # Test for valid short circuit (cc) files
    file_paths = [
        Path("tests/tests_inputs/30 Cycle Report ValidationTest.xlsx"),
        Path("tests/tests_inputs/LV Momentary ValidationTest.xlsx")
    ]
    for file_path in file_paths:
        result = validate_file_epow(file_path)
        assert result == "CC"


def test_validate_file_epow_af():
    # Test for a valid arc flash (af) file
    file_path = Path("tests/tests_inputs/Arc Flash Scenario ValidationTest.xlsx")
    result = validate_file_epow(file_path)
    assert result == "AF"


def test_validate_file_epow_ed():
    # Test for a valid equipment duty (ed) file
    file_path = Path("tests/tests_inputs/Equipment Duty ValidationTest.xlsx")
    result = validate_file_epow(file_path)
    assert result == "ED"


def test_validate_file_epow_tcc():
    # Test for a valid TCC coordination file
    file_path = Path("tests/tests_inputs/TCC Coordination ValidationTest.xlsx")
    result = validate_file_epow(file_path)
    assert result == "TCC"


def test_validate_file_epow_invalid_file_type():
    # Test for an invalid file type
    file_path = Path("tests/tests_inputs/Invalid File Type.txt")
    with pytest.raises(FileError,
                       match="Le fichier 'Invalid File Type.txt' ne semblent pas être un fichier géré par cet outil"):
        validate_file_epow(file_path)