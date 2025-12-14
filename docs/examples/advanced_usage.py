"""
examples/advanced_usage.py

Demonstrates advanced usage of RFunctionCaller.
- Multiple scripts
- Custom R functions
- Base R and package functions
- Python-to-R type conversion
- Handling edge cases and lists of DataFrames
"""

from pathlib import Path

from rpy_bridge import RFunctionCaller

# -----------------------------
# Setup: paths to R scripts
# -----------------------------
scripts_dir = Path("./examples")  # directory containing toy_funcs.R
script1 = scripts_dir / "toy_funcs.R"
script2 = scripts_dir / "toy_funcs_more.R"  # optional second script

# Initialize RFunctionCaller with multiple scripts and packages
caller = RFunctionCaller(
    path_to_renv=None,
    scripts=[script1, script2],
    packages=["dplyr"],  # ensure package is loaded
)


# -----------------------------
# Call custom R functions
# -----------------------------
print("add_and_scale(2,3) →", caller.call("add_and_scale", 2, 3))
print("add_and_scale(2,3, scale=5) →", caller.call("add_and_scale", 2, 3, scale=5))

df = caller.call("multiply_table", 2, 5, times=4)
print("multiply_table result:\n", df)

# --- Call toy_funcs_more.R ---
print(
    "seq_vector(1,10, step=2, reverse=True) →",
    caller.call("seq_vector", start=1, end=10, step=2, reverse=True),
)
print("square_table(5) →", caller.call("square_table", n=5))
print("make_named_list() →", caller.call("make_named_list"))

# -----------------------------
# Base R functions
# -----------------------------
print("sum([1,2,3,4,5]) →", caller.call("sum", [1, 2, 3, 4, 5]))
print("mean([1.0, 2.0, 3.0]) →", caller.call("mean", [1.0, 2.0, 3.0]))
print("toupper(['hello','world']) →", caller.call("toupper", ["hello", "world"]))
print("all([True,True,False]) →", caller.call("all", [True, True, False]))
print("rep([1,2], times=3) →", caller.call("rep", [1, 2], times=3))

# --- R objects ---
print("c(1,2,3) → vector:", caller.call("c", 1, 2, 3))
print(
    "list(a=1, b='foo', c=c(1,2,3)) →", caller.call("list", a=1, b="foo", c=[1, 2, 3])
)
print(
    "data.frame(x=[1,2,3], y=['a','b','c']) →",
    caller.call("data.frame", x=[1, 2, 3], y=["a", "b", "c"]),
)

# --- Named/default arguments ---
print(
    "round([1.234, 5.678], digits=1) →", caller.call("round", [1.234, 5.678], digits=1)
)

# --- Edge cases ---
print("sum([]) →", caller.call("sum", []))
print("mixed type c(1,'a',True) →", caller.call("c", 1, "a", True))

# --- Using dplyr ---
df_pkg = caller.call("data.frame", x=[1, 2, 3])
nrows = caller.call("nrow", df_pkg)
print("dplyr::nrow(data.frame(x=1:3)) →", nrows)

# --- Function returning list of DataFrames ---
list_of_dfs = caller.call("make_list_of_dfs")
print("List of DataFrames:", list_of_dfs)

# --- Mixed Python list types ---
df_mixed = caller.call("data.frame", x=[1, None, 3], y=["a", "b", None])
print("DataFrame with NAs:", df_mixed)
