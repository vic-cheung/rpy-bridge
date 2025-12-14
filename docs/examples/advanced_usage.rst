Advanced Usage Examples for rpy-bridge
======================================

This page demonstrates advanced usage of `rpy-bridge`, including:

- Calling custom R functions
- Handling multiple scripts
- Base R functions and package functions
- Python-to-R conversion and edge cases
- Using functions returning lists or data frames

.. note::

    Adjust paths to the R scripts as needed for your system.
    Make sure R and `rpy2` are installed and accessible.

R Scripts used in this example
------------------------------

- ``examples/toy_funcs.R``
- ``examples/toy_funcs_more.R``

These scripts contain toy functions like `add_and_scale`, `multiply_table`, `make_list_of_dfs`, `seq_vector`, `square_table`, and `make_named_list`.
You can find them in `rpy-bridge examples directory <https://github.com/vic-cheung/rpy-bridge/tree/main/examples>`_ on GitHub.


Python Example
--------------

.. literalinclude:: ../examples/advanced_usage.py
   :language: python
   :linenos:

Explanation
-----------

- **Multiple scripts**: `RFunctionCaller` can load multiple R scripts at once. Functions are accessible via their namespaces.
- **Custom R functions**: You can call your own R functions and pass Python objects directly.
- **Base R functions**: Built-in R functions like `sum`, `mean`, `toupper`, etc., can be called directly from Python.
- **Package functions**: Use `package::function` syntax to call functions from installed R packages, e.g., `dplyr::n_distinct`.
- **Data conversion**: Python scalars, lists, and dictionaries are automatically converted to R vectors, lists, or data frames, and vice versa.
- **Edge cases**: Handles empty vectors, mixed types, and missing values (Python `None` → R `NULL`).

.. note::

    This example is intended to **illustrate functionality**. You may need to adjust paths to R scripts and ensure packages are installed in your R environment for execution.
