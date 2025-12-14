rpy-bridge Usage
================

rpy-bridge provides a Python interface to R scripts, R functions, and R environments with
automatic conversion between Python and R data types. This page shows how to get started
and highlights common usage patterns.

---

Getting Started
---------------

Installation
------------

**Prerequisites**

- System R installed and available on `PATH` (rpy2 requires a working R installation).
- Python 3.12+

**From PyPI:**

.. code-block:: bash

    python3 -m pip install rpy-bridge[r]

**Using UV package manager:**

.. code-block:: bash

    uv add rpy-bridge


---

Basic Usage Examples
-------------------

For full working examples, see the `examples/basic_usage.py` script:

.. literalinclude:: ../examples/basic_usage.py
   :language: python
   :linenos:

---

RFunctionCaller
===============

.. py:class:: RFunctionCaller(path_to_renv=None, scripts=None, packages=None)

   Provides a Python interface to R scripts, functions, and environments.

   **Args:**
     - path_to_renv (Path, optional): Directory containing a renv environment.
     - scripts (Path or list[Path], optional): R scripts or directories to load.
     - packages (str or list[str], optional): R packages to load.

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

- Ensure R is installed and in PATH

Function Not Found
------------------

- Check that the script has been loaded
- Use `list_namespaces()` and `list_namespace_functions()` to inspect

Data Conversion Issues
---------------------

- Missing values in R map to `None` or ``pd.NA``
- Use `clean_r_dataframe()` or `fix_r_dataframe_types()` as needed

---

Examples Folder
===============

See the examples in the repository:

- ``examples/basic_usage.py`` — Loading scripts and calling functions
- ``examples/renv_usage.py`` — Working with renv environments
- ``examples/advanced_usage.py`` — More advanced examples and other features
