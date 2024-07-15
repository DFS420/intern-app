import pytest
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.eep.eep_traitement import report_tcc, FUSE_XL_FILE_NAME, SST_XL_FILE_NAME, MT_XL_FILE_NAME, FUSE_TEX_FILE_NAME, SST_TEX_FILE_NAME, MT_TEX_FILE_NAME

def test_report_tcc():
    test_file_path = Path("tests/tests_inputs/TCC_coordination_file.xlsx")
    target_rep = Path("tests/tests_outputs")
    target_rep.mkdir(exist_ok=True)

    data = {
        "FILES": [test_file_path],
        "BUS_EXCLUS": ["TEST"]
    }

    result = report_tcc(data, target_rep)

    assert len(result) == 6

    expected_files = [
        FUSE_XL_FILE_NAME, SST_XL_FILE_NAME, MT_XL_FILE_NAME,
        FUSE_TEX_FILE_NAME, SST_TEX_FILE_NAME, MT_TEX_FILE_NAME
    ]
    for file in expected_files:
        assert (target_rep / file).exists()

    for path in result:
        assert path.exists()

    with pytest.raises(FileNotFoundError):
        report_tcc({"FILES": []}, target_rep)

