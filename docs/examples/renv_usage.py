"""
examples/renv_usage.py

Demonstrates rpy-bridge usage with a project-specific renv environment.
"""

from pathlib import Path
from rpy_bridge import RFunctionCaller

# ----------------------------------------
# Example 1: Activate a renv Project
# ----------------------------------------

# Point to the root of your R project (containing renv/)
project_dir = Path("/path/to/my_r_project")  # or Path("/path/to/my_r_project/renv")
script_path = project_dir / "scripts" / "my_script.R"

# Initialize RFunctionCaller with renv
rfc = RFunctionCaller(path_to_renv=project_dir, scripts=script_path)

# Call a function from the script
result = rfc.call("add_numbers", 10, 5)
print("add_numbers(10,5) =", result)


# ----------------------------------------
# Example 2: Call Installed Packages within renv
# ----------------------------------------

# Call 'mean' from base R
mean_val = rfc.call("base::mean", [1, 2, 3, 4])
print("mean([1,2,3,4]) =", mean_val)

# Call a function from a package installed in renv, e.g., dplyr::n_distinct
n_unique = rfc.call("dplyr::n_distinct", [1, 2, 2, 3, 3, 3])
print("dplyr::n_distinct([1,2,2,3,3,3]) =", n_unique)
