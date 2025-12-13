"""
Run toy examples for RFunctionCaller.

This script demonstrates:
- running a local R script with `RFunctionCaller`
- calling base R functions, package functions, and custom R functions
- auto-conversion of Python types to R vectors
- safe repeated calls to different functions without reloading the script

Adjust paths before running.

Optional improvements / limitations:
- Calling package functions from libraries not loaded in your script:
  you might need `library(pkg)` inside the R script or inside `RFunctionCaller`.
- Named R lists conversion:
  currently, list(a=1, b=2) converts to a Python dict, but more complex nested
  named lists may need recursive handling (depends on _r2py).
- Multiple R scripts:
  to source multiple scripts safely, extend `RFunctionCaller` to track _script_loaded
  for each script.
"""

# %%
from pathlib import Path

from rpy_bridge import RFunctionCaller


# %%
def run_local():
    script = Path("./toy_funcs.R")
    print("Local script exists:", script.exists())

    # Initialize with dplyr in packages so it's auto-installed/loaded
    caller = RFunctionCaller(path_to_renv=None, script_path=script, packages=["dplyr"])

    # --- Call functions from your script ---
    print("Calling add_and_scale(2,3):", caller.call("add_and_scale", 2, 3))
    print(
        "Calling add_and_scale(2,3, scale=10):",
        caller.call("add_and_scale", 2, 3, scale=10),
    )

    df = caller.call("multiply_table", 2, 5, times=4)
    print("multiply_table result:\n", df)

    # --- Base R functions ---
    print("\nBase R: sum(c(1,2,3,4,5)) →", caller.call("sum", [1, 2, 3, 4, 5]))
    print(
        "Base R: seq(from=1, to=5, by=0.5) →", caller.call("seq", from_=1, to=5, by=0.5)
    )
    print("Base R: mean(c(1.0, 2.0, 3.0)) →", caller.call("mean", [1.0, 2.0, 3.0]))
    print("Base R: min(c(10,5,7)) →", caller.call("min", [10, 5, 7]))
    print(
        "Base R: toupper(c('hello','world')) →",
        caller.call("toupper", ["hello", "world"]),
    )
    print(
        "Base R: paste(c('a','b'), c('1','2'), sep='-') →",
        caller.call("paste", ["a", "b"], ["1", "2"], sep="-"),
    )
    print("Base R: any(c(TRUE,FALSE,TRUE)) →", caller.call("any", [True, False, True]))
    print("Base R: all(c(TRUE,TRUE,TRUE)) →", caller.call("all", [True, True, True]))
    print("Base R: rep(c(1,2), times=3) →", caller.call("rep", [1, 2], times=3))

    # --- R objects ---
    print("\nBase R: c(1,2,3) → vector:", caller.call("c", 1, 2, 3))
    print(
        "Base R: list(a=1, b='foo', c=c(1,2,3)) →",
        caller.call("list", a=1, b="foo", c=[1, 2, 3]),
    )
    print(
        "Base R: data.frame(x=c(1,2,3), y=c('a','b','c')) →",
        caller.call("data.frame", x=[1, 2, 3], y=["a", "b", "c"]),
    )

    # --- Named arguments / default arguments ---
    print(
        "Base R: round(c(1.234, 5.678), digits=1) →",
        caller.call("round", [1.234, 5.678], digits=1),
    )

    # --- Edge cases ---
    print("Base R: sum(empty vector) →", caller.call("sum", []))
    print("Base R: mixed type c(1,'a',TRUE) →", caller.call("c", 1, "a", True))

    # --- Using dplyr ---
    df_pkg = caller.call("data.frame", x=[1, 2, 3])
    nrows = caller.call("nrow", df_pkg)
    print("\nUsing dplyr::nrow(data.frame(x=1:3)) →", nrows)

    # --- Function returning list of DataFrames ---
    # Make sure toy_funcs.R defines:
    # make_list_of_dfs <- function() list(df1=data.frame(a=1:3), df2=data.frame(b=4:6))
    list_of_dfs = caller.call("make_list_of_dfs")
    print("\nList of DataFrames from R function:", list_of_dfs)

    # --- Mixed Python list types ---
    df_mixed = caller.call("data.frame", x=[1, None, 3], y=["a", "b", None])
    print("\nDataFrame with NAs:", df_mixed)


if __name__ == "__main__":
    run_local()

# %%
