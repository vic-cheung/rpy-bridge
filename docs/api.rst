API Reference
=============

This page documents the public API of **rpy-bridge**.
For almost all use cases, users only need to work with a single class:
``RFunctionCaller``.

For practical examples, see :ref:`usage` or the examples directory:
`rpy-bridge examples <https://github.com/vic-cheung/rpy-bridge/tree/main/examples>`_.


How it works internally
-----------------------

Internally, ``RFunctionCaller`` embeds an R session inside Python.
Each sourced R script is loaded into its own isolated environment
(namespace), preventing name collisions between scripts.

When ``call()`` is invoked:

1. Python arguments are converted to R objects
2. The requested R function is resolved (script, package, or base R)
3. The function is executed inside the R session
4. The return value is converted back into a Python object

These details are abstracted away so users can focus on calling R functions
without managing R sessions, environments, or type conversion manually.


Overview
--------

``RFunctionCaller`` provides a unified interface for:

* Loading one or more R scripts
* Calling functions defined in those scripts
* Calling base R and package functions
* Inspecting available functions in loaded namespaces
* Optionally activating a ``renv`` project

Typical usage looks like:

.. code-block:: python

    from rpy_bridge import RFunctionCaller

    rfc = RFunctionCaller(scripts="my_script.R")
    result = rfc.call("my_function", 1, 2)


RFunctionCaller
---------------

.. autoclass:: rpy_bridge.RFunctionCaller
   :members:
   :undoc-members:
   :show-inheritance:


Initialization
^^^^^^^^^^^^^^

.. code-block:: python

    rfc = RFunctionCaller(
        path_to_renv=None,
        scripts="my_script.R",
        packages=["dplyr"],
    )

**Parameters**

* **path_to_renv**
  Optional path to an R project that uses ``renv``. This may point either to
  the project root or directly to the ``renv/`` directory.

* **scripts**
  One or more R scripts or directories containing ``.R`` files. Scripts are
  sourced and loaded into isolated namespaces.

* **packages**
  Optional R packages to load (and install if missing), for example
  ``["dplyr"]``.


Calling R Functions
^^^^^^^^^^^^^^^^^^^

The primary method users will interact with is ``call``.

.. code-block:: python

    # Base R
    rfc.call("sum", [1, 2, 3])

    # Package function
    rfc.call("dplyr::n_distinct", [1, 2, 2, 3])

    # Function from a sourced R script
    rfc.call("add_and_scale", 2, 3, scale=10)


Inspecting Loaded Functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^

When working with larger scripts or multiple namespaces, it is often useful
to inspect what functions are available.

.. code-block:: python

    rfc.list_namespaces()
    rfc.print_function_tree()


Accessing Script Namespaces (Advanced)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each sourced R script is loaded into its own namespace and can be accessed
as an attribute on the ``RFunctionCaller`` instance.

.. code-block:: python

    rfc.my_script.add_and_scale(2, 3)
    rfc.my_script.list_functions()

This is optional syntactic sugar; all functions can always be called via
``rfc.call(...)``.


Notes and Best Practices
------------------------

* Base R functions can be called directly (e.g. ``"sum"``, ``"mean"``).
* Package functions should use ``package::function`` syntax.
* Missing values (``None``, ``pd.NA``) are mapped to R ``NA`` automatically.
* Empty vectors, mixed types, and lists of DataFrames are supported.
* For most workflows, users should rely on ``call()`` and
  ``print_function_tree()`` exclusively.


Examples
--------

The following example scripts demonstrate real-world usage:

* ``examples/basic_usage.py`` – Minimal usage patterns
* ``examples/advanced_usage.py`` – Multiple scripts, packages, edge cases
* ``examples/renv_usage.py`` – Using project-specific ``renv`` environments

View all examples on GitHub:
`https://github.com/vic-cheung/rpy-bridge/tree/main/examples <https://github.com/vic-cheung/rpy-bridge/tree/main/examples>`_
