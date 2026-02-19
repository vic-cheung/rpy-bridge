rpy-bridge Usage
================

rpy-bridge is a Python-controlled R execution orchestrator (not a thin rpy2 wrapper).
It handles headless-safe R startup, project-root inference, out-of-tree ``renv`` activation,
isolated script namespaces, and Python↔R conversion with dtype/NA normalization.

---

Getting Started
---------------

Installation
------------

**Prerequisites**

- System R installed and available on ``PATH`` (rpy2 requires a working R installation).
- Python 3.11+ (tested on 3.11–3.12)

**From PyPI:**

.. code-block:: bash

    python3 -m pip install rpy-bridge rpy2

**Using uv package manager:**

.. code-block:: bash

    uv add rpy-bridge rpy2


---

Quickstart examples
-------------------

Call a package function (no scripts):

.. code-block:: python

    from rpy_bridge import RFunctionCaller

    rfc = RFunctionCaller()
    samples = rfc.call("stats::rnorm", 5, mean=0, sd=1)
    median_val = rfc.call("stats::median", samples)

Call a script function with ``renv`` activation (out-of-tree allowed):

.. code-block:: python

    from pathlib import Path
    from rpy_bridge import RFunctionCaller

    project = Path("/path/to/project")
    script = project / "scripts" / "example.R"

    rfc = RFunctionCaller(path_to_renv=project, scripts=script)
    result = rfc.call("some_function", 42, named_arg="value")

See the full working examples in ``examples/basic_usage.py``:

.. literalinclude:: ../examples/basic_usage.py
    :language: python
    :linenos:

---

RFunctionCaller
===============

.. py:class:: RFunctionCaller(path_to_renv: str | Path | None = None, scripts: str | Path | list[str | Path] | None = None, packages: str | list[str] | None = None)

   Provides a Python interface to R scripts, functions, and environments.

   **Args:**
    - path_to_renv (str | Path, optional): Directory containing a renv environment.
    - scripts (Path | str | list[Path] | list[str], optional): R scripts or directories to load.
    - packages (str | list[str], optional): R packages to load.

   **Raises:**
     - FileNotFoundError: If a script path does not exist
     - RuntimeError: If R is not found or rpy2 is missing

Core Methods
------------

**call(func_name, *args, **kwargs)**

Call an R function from a script, package, or global environment.

Args:
    - func_name (str): Name of the R function. Can be:
        - 'function_name' for functions in scripts or global env
        - 'package::function_name' for package functions
    - *args: Positional arguments for the R function
    - **kwargs: Keyword arguments for the R function

Returns:
    Any: Python object corresponding to R return value.

Raises:
    ValueError: Function not found
    RuntimeError: Function call failed in R

---

**list_namespaces()**

Return a list of all loaded script namespaces.

.. code-block:: python

    namespaces = rfc.list_namespaces()

---

**list_namespace_functions(namespace)**

List callable functions in a specific script namespace.

.. code-block:: python

    funcs = rfc.list_namespace_functions("script1")

---

**print_function_tree(include_packages=False, max_display=10)**

Pretty-print functions from loaded scripts and optionally packages. Example usage:

.. code-block:: python

    rfc.print_function_tree(include_packages=False, max_display=5)

Example output:

.. code-block:: text

    script1/
      add_numbers
      multiply_numbers
      ...
    script2/
      divide_numbers
      subtract_numbers
      ...

---

Troubleshooting
===============

R Not Found
-----------

- Ensure R is installed and on PATH
- Set ``R_HOME`` explicitly if R is installed in a non-default location

Function Not Found
------------------

- Check that the script has been loaded
- Use ``list_namespaces()`` and ``list_namespace_functions()`` to inspect
- For package functions, use ``package::function`` syntax

Data Conversion Issues
---------------------

- Missing values in R map to ``None`` or ``pd.NA``
- Use ``clean_r_dataframe()`` or ``fix_r_dataframe_types()`` as needed
- For dtype alignment, see ``normalize_dtypes`` / ``compare_r_py_dataframes``

CI and headless tips
--------------------
- Headless defaults are applied automatically; avoid GUI probing in CI
- To skip ``renv`` when R is absent in CI, set ``RPY_BRIDGE_SKIP_RENV=1``

Logging
-------
- Logs emit through the Python `logging` stdlib with a dedicated ``[RFunctionCaller]`` handler
- Adjust log level globally via stdlib `logging` configuration in your app

---

Examples Folder
===============

See the examples in the repository:

- ``examples/basic_usage.py`` — Loading scripts and calling functions
- ``examples/renv_usage.py`` — Working with renv environments
- ``examples/advanced_usage.py`` — More advanced examples and other features
