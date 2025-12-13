

# caller fixture is injected from conftest.py
def test_call_stats_functions(caller):
    """Smoke test: load `stats` and call `rnorm` and `median`."""

    samples = caller.call("rnorm", 10, mean=5)
    assert hasattr(samples, "__len__")
    assert len(samples) == 10

    med = caller.call("stats::median", samples)
    # median may come back as a scalar or a single-element array
    if hasattr(med, "__len__") and not isinstance(med, (int, float)):
        assert len(med) == 1
    else:
        assert isinstance(med, (int, float))
