# %%
from pathlib import Path
import pandas as pd
from rpy_bridge import RFunctionCaller


# %%
def test_py2r_edge_cases(caller: RFunctionCaller):
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

    caller._ensure_r_loaded()  # Make sure R is loaded

    print("\n--- Testing _py2r edge cases ---")
    for name, value in test_cases.items():
        try:
            r_obj = caller._py2r(value)
            print(f"\n--- Test case: {name} ---")
            print("R object type:", type(r_obj))
            # Handle R vectors or ListVector
            if hasattr(r_obj, "__len__") and not isinstance(
                r_obj, (int, float, bool, str)
            ):
                try:
                    print("R object contents:", list(r_obj))
                except Exception:
                    print("R object contents: (complex structure)")
            else:
                print("R object:", r_obj)
        except Exception as e:
            print(f"Error in {name}: {e}")


# Example usage
if __name__ == "__main__":
    caller = RFunctionCaller()
    test_py2r_edge_cases(caller)

# %%
