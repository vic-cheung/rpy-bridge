Usage
=====

Quick examples showing common usage patterns for `RFunctionCaller`.

Local script
------------

If you have a local R script, source it and call its functions:

.. code-block:: python

    from pathlib import Path
    from rpy_bridge import RFunctionCaller

    script_path = Path("./scripts/my_funcs.R")
    caller = RFunctionCaller(path_to_renv=None, script=script_path)
    result = caller.call("my_function", 1, named_arg="x")

Call installed R packages
-------------------------

Load installed R packages and call package functions directly (no script required):

.. code-block:: python

    from rpy_bridge import RFunctionCaller

    # Load the `stats` package and call `rnorm`
    caller = RFunctionCaller(path_to_renv=None, packages=["stats"])
    samples = caller.call("rnorm", 5, mean=10)
    # Use namespace syntax for clarity
    median_val = caller.call("stats::median", samples)

