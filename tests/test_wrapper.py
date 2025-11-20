
from rpy_bridge import rpy2_utils


class DummyCaller:
    def __init__(self, *a, **k):
        pass

    def call(self, name, *args, **kwargs):
        return {"called": name}


def test_call_wrapper_monkeypatch():
    original = rpy2_utils.RFunctionCaller.from_github
    try:
        rpy2_utils.RFunctionCaller.from_github = staticmethod(lambda **kw: DummyCaller())
        res = rpy2_utils.call_r_function_from_github(
            repo="owner/repo",
            file_path="scripts/x.R",
            function_name="foo",
            trust_remote_code=True,
        )
        assert res == {"called": "foo"}
    finally:
        rpy2_utils.RFunctionCaller.from_github = original
