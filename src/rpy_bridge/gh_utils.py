"""
GitHub helper utilities: token retrieval and file fetching.

These helpers centralize GitHub API interactions and token lookup so other
modules can import them without duplicating code.
"""

from __future__ import annotations

import base64
import json
import urllib.request
import urllib.error
import subprocess
from pathlib import Path
from typing import Optional, Tuple
import tempfile
import time


def get_github_token() -> Optional[str]:
    """
    Get a GitHub token from env vars or the git credential helper.

    Returns the token string or None if not found.
    """
    token = None
    try:
        # Lazy import to avoid top-level side effects in importing modules
        import os

        token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        if token:
            return token
    except Exception:
        pass

    try:
        proc = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n",
            text=True,
            capture_output=True,
            timeout=5,
        )
        if proc.returncode == 0 and proc.stdout:
            for line in proc.stdout.splitlines():
                if line.startswith("password="):
                    return line.split("password=", 1)[1]
    except Exception:
        return None

    return None


def fetch_r_script_from_github(
    repo: str,
    path: str,
    ref: str = "main",
    token: Optional[str] = None,
    cache_dir: Optional[Path] = None,
) -> Tuple[Path, str]:
    """Fetch a file from the GitHub Contents API, cache it by commit SHA.

    Returns a tuple of (local_path, sha). Raises RuntimeError on failure.
    """
    if cache_dir is None:
        cache_dir = Path.home() / ".cache" / "rpy-bridge"
    cache_dir.mkdir(parents=True, exist_ok=True)

    api_url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={ref}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    tok = token or get_github_token()
    if tok:
        headers["Authorization"] = f"token {tok}"

    # Simple retry loop with exponential backoff for transient network errors
    attempts = 3
    backoff = 0.5
    data = None
    for attempt in range(1, attempts + 1):
        req = urllib.request.Request(api_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.load(resp)
            break
        except urllib.error.HTTPError as e:
            # For 4xx errors, don't retry
            if 400 <= getattr(e, "code", 0) < 500:
                raise RuntimeError(f"GitHub API request failed: {e.code} {e.reason}")
            if attempt == attempts:
                raise RuntimeError(f"GitHub API request failed after retries: {e}")
        except Exception as e:
            if attempt == attempts:
                raise RuntimeError(f"Failed to fetch from GitHub after {attempts} attempts: {e}")
            time.sleep(backoff)
            backoff *= 2

    if "content" not in data or "sha" not in data:
        raise RuntimeError("Unexpected response from GitHub API; 'content' or 'sha' missing")

    sha = data["sha"]
    content_b64 = data["content"]
    try:
        content_bytes = base64.b64decode(content_b64)
    except Exception as e:
        raise RuntimeError(f"Failed to decode GitHub content: {e}")

    fname = cache_dir / f"{repo.replace('/', '-')}-{sha}-{Path(path).name}"
    if not fname.exists():
        # Write to a temporary file and move into place to avoid partial writes
        fd, tmp_path = tempfile.mkstemp(dir=str(cache_dir), prefix="rpy-bridge-")
        try:
            with open(fd, "wb") as fh:
                fh.write(content_bytes)
            Path(tmp_path).rename(fname)
        except Exception:
            try:
                Path(tmp_path).unlink()
            except Exception:
                pass
            raise

    return fname, sha
