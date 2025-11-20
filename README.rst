rpy-bridge
=========

Usage example (safe fetch only):

.. code-block:: python

    from rpy_bridge.rpy2_utils import RFunctionCaller

    # Download the script but don't execute it yet
    local_path = RFunctionCaller.from_github(
        repo="owner/repo",
        file_path="scripts/my_script.R",
        trust_remote_code=False,
    )

    print("Downloaded to:", local_path)

Execute and call a function (explicit opt-in):

.. code-block:: python

    from rpy_bridge.rpy2_utils import call_r_function_from_github

    result = call_r_function_from_github(
        repo="owner/repo",
        file_path="scripts/my_script.R",
        function_name="my_func",
        trust_remote_code=True,
    )
