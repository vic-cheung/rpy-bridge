from pathlib import Path
import pytest

from rpy_bridge import RFunctionCaller


def test_missing_script_raises():
    # If script_path does not exist, the constructor should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        RFunctionCaller(path_to_renv=None, script_path=Path("/does/not/exist.R"))
