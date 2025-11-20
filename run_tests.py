import runpy
import sys
from pathlib import Path

# Ensure the package src is on sys.path so imports work
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

tests = [
    "tests/test_github_fetch.py",
    "tests/test_wrapper.py",
]

failed = False
for t in tests:
    path = ROOT / t
    print("Running", path)
    try:
        runpy.run_path(str(path), run_name="__main__")
    except SystemExit as e:
        if e.code != 0:
            failed = True
    except Exception as e:
        print("Test failed:", e)
        failed = True

if failed:
    sys.exit(1)
print("All tests executed (check outputs).")
