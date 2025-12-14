# API Reference

This section provides a reference for all modules, classes, and functions in `rpy-bridge`.

For practical usage examples, see :ref:`usage` or the `examples` directory:
`rpy-bridge examples <https://github.com/vic-cheung/rpy-bridge/tree/main/examples>`_.

---

## Module: rpy_bridge

.. automodule:: rpy_bridge
:members:
:undoc-members:
:show-inheritance:

This is the main package module. It provides top-level helpers and imports the core R interface.

Key features:

* Load and call R scripts and functions from Python.
* Activate `renv` environments for isolated R projects.
* Automatic conversion between R and Python data types.
* Utilities for cleaning and aligning DataFrames.

---

## Module: rpy_bridge.rpy2_utils

.. automodule:: rpy_bridge.rpy2_utils
:members:
:undoc-members:
:show-inheritance:

Key classes:

* **RFunctionCaller** – Primary interface for calling R functions.
* **NamespaceWrapper** – Wraps an R script namespace for Python attribute access.

---

## Class: RFunctionCaller

.. autoclass:: rpy_bridge.rpy2_utils.RFunctionCaller
:members:
:undoc-members:
:show-inheritance:

RFunctionCaller is the main class to interact with R scripts, packages, and functions.

**Initialization:**

```python
caller = RFunctionCaller(
    path_to_renv: Path | None = None,
    scripts: Path | list[Path] | None = None,
    packages: str | list[str] | None = None
)
```

* **path_to_renv** – Optional path to an R project with `renv` for dependency isolation.
* **scripts** – Path or list of `.R` files or directories to source.
* **packages** – R packages to load (e.g., `['dplyr']`).

**Core methods:**

* **call(func_name, *args, **kwargs)**
  Call an R function from a script, package, or the global environment. Handles automatic Python ↔ R conversion.

  Examples:

  ```python
  caller.call("sum", [1, 2, 3])
  caller.call("dplyr::mutate", df, new_col=1)
  ```

* **list_namespaces()** – Returns a list of all loaded script namespaces.

* **list_namespace_functions(namespace)** – Returns a list of callable functions in a specific namespace.

* **print_function_tree(include_packages=False, max_display=10)** – Pretty-prints available functions in scripts and optionally packages.

* **ensure_r_package(pkg)** – Ensures an R package is loaded (installs it if missing).

---

## Class: NamespaceWrapper

.. autoclass:: rpy_bridge.rpy2_utils.NamespaceWrapper
:members:
:undoc-members:

Returned by `RFunctionCaller.<namespace>`. Provides attribute access to R functions in that namespace.

* **list_functions()** – List all callable functions in the namespace.

Example:

```python
caller.toy_funcs.list_functions()
caller.toy_funcs.add_and_scale(2, 3)
```

---

## Function: activate_renv

.. autofunction:: rpy_bridge.rpy2_utils.activate_renv

Activates an R `renv` environment for dependency isolation.

Args:

* **path_to_renv** – Path to R project containing `renv/activate.R` and `renv.lock`.

---

## Advanced R ↔ Python conversion utilities

* **_py2r(obj)** – Convert Python objects (scalars, lists, dicts, pandas DataFrames) to R objects.
* **_r2py(obj)** – Convert R objects (vectors, lists, DataFrames) to Python equivalents.
* **clean_r_missing(obj, caller)** – Recursively convert R missing values (`NA`) to Python `None` or `pd.NA`.
* **r_namedlist_to_dict(namedlist, caller, top_level=False)** – Convert R NamedList or ListVector to Python dict or list.
* **postprocess_r_dataframe(df)** – Fix dtypes, normalize, and clean DataFrame imported from R.

---

## DataFrame comparison and alignment utilities

* **compare_r_py_dataframes(df1, df2, float_tol=1e-8)**
  Compare Python and R DataFrames for numeric and non-numeric differences. Returns a dictionary with mismatches.

* **normalize_dtypes(df1, df2)** – Align dtypes between two DataFrames.

* **align_numeric_dtypes(df1, df2)** – Convert numeric-like object columns to float64 for comparison.

---

## Tips and Notes

* Base R functions can be called directly: `caller.call("sum", [1,2,3])`.
* Package functions can be called with `::`: `caller.call("dplyr::mutate", df, new_col=1)`.
* Automatic handling of `None` / `pd.NA` → `NA` in R.
* Edge cases (empty vectors, mixed types, lists of DataFrames) are supported.
* All function calls are logged; check `logger` for debug info.

---

## Examples

* `examples/advanced_usage.py` demonstrates:

  * Calling multiple scripts
  * Custom R functions
  * Base R and package functions
  * Python-to-R type conversion
  * Handling lists of DataFrames and edge cases

  `View examples on GitHub <https://github.com/vic-cheung/rpy-bridge/tree/main/examples>`_.
