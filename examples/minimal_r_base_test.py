# %%
from rpy_bridge import RFunctionCaller

# Minimal test: only call base R sum
caller = RFunctionCaller()
print("Base R: sum([1, 2, 3]) →", caller.call("sum", [1, 2, 3]))

# %%
