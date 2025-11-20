"""
Run toy examples for RFunctionCaller.

This script demonstrates:
- running a local R script with `RFunctionCaller`
- fetching a script from GitHub (inspect-first) and executing it (opt-in)

Adjust paths and repo identifiers before running.
"""

from pathlib import Path

from rpy_bridge import RFunctionCaller, call_r_function_from_github


def run_local():
    script = Path("examples/toy_funcs.R")
    print("Local script exists:", script.exists())

    caller = RFunctionCaller(path_to_renv=None, script_path=script)

    print("Calling add_and_scale(2,3)")
    print(caller.call("add_and_scale", 2, 3))

    print("Calling add_and_scale(2,3, scale=10)")
    print(caller.call("add_and_scale", 2, 3, scale=10))

    print("Calling multiply_table(2,5,times=4)")
    df = caller.call("multiply_table", 2, 5, times=4)
    print(df)


def run_github_inspect_then_run():
    repo = "vic-cheung/rpy-bridge"  # replace with the remote repo that contains the script
    path = "examples/toy_funcs.R"

    # Inspect first (safe): download but do not execute
    cached = call_r_function_from_github(
        repo=repo,
        file_path=path,
        function_name="add_and_scale",
        trust_remote_code=False,
    )
    print("Downloaded script to:", cached)

    # After you review the file, execute it explicitly (opt-in)
    result = call_r_function_from_github(
        repo=repo,
        file_path=path,
        function_name="add_and_scale",
        trust_remote_code=True,
        path_to_renv=None,
        require_token=False,
        *[4, 6],
        scale=2,
    )
    print("Remote call result:", result)


if __name__ == "__main__":
    run_local()
    # Uncomment to test GitHub flow (ensure repo/path are correct)
    # run_github_inspect_then_run()
