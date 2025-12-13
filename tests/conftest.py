import pytest
from rpy_bridge import RFunctionCaller


@pytest.fixture
def caller():
    """
    Provides a reusable RFunctionCaller instance for tests.
    Skips tests if R/rpy2 are not available.
    """
    try:
        instance = RFunctionCaller(path_to_renv=None, packages=["stats"])
        instance._ensure_r_loaded()
        return instance
    except Exception as e:
        pytest.skip(f"Skipping because R/rpy2 not available: {e}")
