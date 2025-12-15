.. rpy-bridge documentation master file
======================================

Welcome to rpy-bridge's documentation!

rpy-bridge is a **Python-controlled R execution orchestrator** (not a thin rpy2 wrapper).
It delivers deterministic, headless-safe R startup, project-root inference, out-of-tree
``renv`` activation, isolated script namespaces, and robust Python↔R conversions.

Why it’s different
------------------
- Finds R project roots via markers (``.git``, ``.Rproj``, ``renv.lock``, ``DESCRIPTION``)
- Activates ``renv`` even when it lives outside the calling directory
- Executes from the inferred project root so relative paths behave as R expects
- Runs headless by default (no GUI probing), isolates scripts from ``globalenv()``
- Normalizes return values for Python (NAs, dtypes, data.frames)

Quickstart
----------

Call a package function (no scripts):

.. code-block:: python

   from rpy_bridge import RFunctionCaller

   rfc = RFunctionCaller()
   samples = rfc.call("stats::rnorm", 5, mean=0, sd=1)
   median_val = rfc.call("stats::median", samples)

Call a function from a local script with ``renv``:

.. code-block:: python

   from pathlib import Path
   from rpy_bridge import RFunctionCaller

   project = Path("/path/to/project")
   script = project / "scripts" / "example.R"

   rfc = RFunctionCaller(path_to_renv=project, scripts=script)
   result = rfc.call("some_function", 42, named_arg="value")

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   usage
   api
   examples/basic_usage
   examples/renv_usage
   examples/advanced_usage

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
