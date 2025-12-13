import pytest

from rpy_bridge import RFunctionCaller


def test_call_stats_functions():
    """Smoke test: load `stats` and call `rnorm` and `median`.

    This test will be skipped if R or rpy2 are not available in the test
    environment.
    """
    try:
        caller = RFunctionCaller(path_to_renv=None, packages=["stats"])
    except Exception as e:
        pytest.skip(f"Skipping because R/rpy2 not available: {e}")

    samples = caller.call("rnorm", 10, mean=5)
    assert hasattr(samples, "__len__")
    assert len(samples) == 10

    med = caller.call("stats::median", samples)
    # median may come back as a scalar or a single-element array
    if hasattr(med, "__len__") and not isinstance(med, (int, float)):
        assert len(med) == 1
    else:
        assert isinstance(med, (int, float))
