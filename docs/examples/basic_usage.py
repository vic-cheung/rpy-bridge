from pathlib import Path
from rpy_bridge import RFunctionCaller

# -----------------------------
# Example 1: Single R script
# -----------------------------
rfc = RFunctionCaller(scripts=Path("my_script.R"))

# Call a function from the script
result = rfc.call("add_numbers", 3, 5)
print("add_numbers(3,5) =", result)

# -----------------------------
# Example 2: Multiple scripts / namespaces
# -----------------------------
rfc_multi = RFunctionCaller(scripts=["script1.R", "script2.R"])

# List loaded namespaces
print("Namespaces:", rfc_multi.list_namespaces())

# List functions in script1
print("script1 functions:", rfc_multi.script1.list_functions())

# Call a function from script2 via namespace
result2 = rfc_multi.script2.multiply_numbers(4, 6)
print("multiply_numbers(4,6) =", result2)

# -----------------------------
# Example 3: Calling R package functions
# -----------------------------
# Call 'mean' from base R package
mean_val = rfc.call("base::mean", [1, 2, 3, 4])
print("mean([1,2,3,4]) =", mean_val)

# -----------------------------
# Example 4: Inspect available functions
# -----------------------------
rfc_multi.print_function_tree(include_packages=False)
