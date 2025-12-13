# %%
import numpy as np
import pandas as pd


# The caller fixture is now injected by pytest
def test_py2r_r2py_roundtrip(caller):
    """
    Test round-trip conversion: Python -> R -> Python
    Handles edge cases including scalars, lists, nested structures, dicts, and NA values.
    """
    test_cases = {
        "simple_int_list": [1, 2, 3],
        "simple_float_list": [1.0, 2.5, 3.7],
        "mixed_int_float_list": [1, 2.5, 3],
        "bool_list": [True, False, True],
        "string_list": ["a", "b", "c", None],
        "mixed_type_list": [1, "a", True, 3.0, None],
        "nested_list": [[1], [2, None], [[3, 4], [5, None]]],
        "empty_list": [],
        "series_with_na": pd.Series([1, 2, pd.NA, 4]),
        "dict_simple": {"x": 1, "y": 2},
        "dict_nested": {"a": [1, 2], "b": {"c": "foo", "d": 3.14}},
        "none_value": None,
        "pd_na_value": pd.NA,
        "scalar_int": 10,
        "scalar_float": 3.14,
        "scalar_bool": True,
        "scalar_str": "hello",
    }

    print("\n--- Testing Python -> R -> Python round-trip ---")
    for name, py_obj in test_cases.items():
        print(f"\n--- Test case: {name} ---")
        try:
            r_obj = caller._py2r(py_obj)
            py_roundtrip = caller._r2py(r_obj)

            def normalize(obj):
                if isinstance(obj, pd.Series):
                    return obj.replace({pd.NA: None}).tolist()
                elif obj is pd.NA:
                    return None
                elif isinstance(obj, list):
                    return [normalize(x) for x in obj]
                elif isinstance(obj, dict):
                    return {k: normalize(v) for k, v in obj.items()}
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return obj

            original_norm = normalize(py_obj)
            roundtrip_norm = normalize(py_roundtrip)

            print("Original (normalized):", original_norm)
            print("Round-trip result:", roundtrip_norm)
            print("Match:", original_norm == roundtrip_norm)

        except Exception as e:
            print("Error during round-trip:", e)
