"""
Run toy examples for RFunctionCaller.

This script demonstrates:
- running a local R script with `RFunctionCaller`

Adjust paths before running.
"""

# %%
from pathlib import Path

from rpy_bridge import RFunctionCaller


# %%
def run_local():
    script = Path("./toy_funcs.R")
    print("Local script exists:", script.exists())

    caller = RFunctionCaller(path_to_renv=None, script_path=script)

    print("Calling add_and_scale(2,3)")
    print(caller.call("add_and_scale", 2, 3))

    print("Calling add_and_scale(2,3, scale=10)")
    print(caller.call("add_and_scale", 2, 3, scale=10))

    print("Calling multiply_table(2,5,times=4)")
    df = caller.call("multiply_table", 2, 5, times=4)
    print(df)


if __name__ == "__main__":
    run_local()

# %%
