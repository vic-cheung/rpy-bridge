import json
import base64

from rpy_bridge.gh_utils import fetch_r_script_from_github


def test_fetch_r_script_from_github(monkeypatch, tmp_path):
    content = "print('hello')\n"

    data = {
        "sha": "deadbeef",
        "content": base64.b64encode(content.encode()).decode(),
    }

    def dummy_urlopen(req, *args, **kwargs):
        import io

        return io.BytesIO(bytes(json.dumps(data), "utf-8"))

    import urllib.request

    monkeypatch.setattr(urllib.request, "urlopen", dummy_urlopen)

    local_path, sha = fetch_r_script_from_github("owner/repo", "scripts/x.R", cache_dir=tmp_path)
    assert sha == "deadbeef"
    assert local_path.exists()
