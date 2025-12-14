Basic Usage Examples for rpy-bridge
===================================

.. toctree::
   :maxdepth: 1

   ../examples/basic_usage.py

This page demonstrates common usage patterns for `rpy-bridge`:

- Loading R scripts and calling functions
- Accessing multiple namespaces
- Calling functions from R packages
- Inspecting available functions in scripts and packages

Python Example
--------------

.. literalinclude:: ../examples/basic_usage.py
   :language: python
   :linenos:


.. note::

    All paths to R scripts are relative to your Python working directory.
    Make sure R and rpy2 are installed and accessible in your environment.
