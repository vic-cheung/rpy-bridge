import pytest
from rpy_bridge.rpy2_utils import RFunctionCaller


def test_require_token_raises(monkeypatch, tmp_path):
    # Force token discovery to return None
    monkeypatch.setattr("rpy_bridge.rpy2_utils.get_github_token", lambda: None)

    with pytest.raises(RuntimeError):
        RFunctionCaller.from_github(
            repo="owner/repo",
            file_path="scripts/x.R",
            require_token=True,
            cache_dir=tmp_path,
            trust_remote_code=False,
        )
