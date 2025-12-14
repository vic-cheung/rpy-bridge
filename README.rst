rpy-bridge
=========

Usage example (local script):

.. code-block:: python

    from rpy_bridge.rpy2_utils import RFunctionCaller

    # Use a local script path (clone or download remote scripts yourself)
    script_path = "/path/to/cloned/repo/scripts/my_script.R"
    caller = RFunctionCaller(path_to_renv=None, script=script_path)
    result = caller.call("my_func")
