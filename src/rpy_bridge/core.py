"""
Core orchestration for rpy-bridge.

`RFunctionCaller` is the primary public interface for loading R scripts,
activating renv, and calling R functions with automatic conversion.
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .convert import clean_r_missing, r_namedlist_to_dict
from .dataframe import postprocess_r_dataframe
from .env import CI_TESTING, R_HOME
from .logging import log_r_call, logger
from .renv import activate_renv, find_project_root, normalize_scripts
from .rpy2_loader import ensure_rpy2


class NamespaceWrapper:
    """
    Wrap an R script namespace for Python attribute access.
    """

    def __init__(self, env):
        self._env = env

    def __getattr__(self, func_name):
        if func_name in self._env:
            return self._env[func_name]
        raise AttributeError(f"Function '{func_name}' not found in R namespace")

    def list_functions(self):
        """Return a list of callable functions in this namespace."""
        return [k for k, v in self._env.items() if callable(v)]


class RFunctionCaller:
    """
    Primary interface for calling R functions from Python.

    `RFunctionCaller` loads one or more R scripts into isolated namespaces and
    provides a unified `call()` method for executing functions from scripts,
    installed R packages, or base R.
    """

    def __init__(
        self,
        path_to_renv: str | Path | None = None,
        scripts: str | Path | list[str | Path] | None = None,
        packages: str | list[str] | None = None,
        headless: bool = True,
        skip_renv_if_no_r: bool = True,
        **kwargs,
    ):
        if path_to_renv is not None and not isinstance(path_to_renv, Path):
            path_to_renv = Path(path_to_renv)
        self.path_to_renv = path_to_renv.resolve() if path_to_renv else None

        if "script_path" in kwargs:
            script_path_value = kwargs.pop("script_path")
            warnings.warn(
                "'script_path' argument is deprecated. Please use 'scripts' instead (accepts a Path or list of Paths).",
                DeprecationWarning,
                stacklevel=2,
            )
            if scripts is None:
                scripts = script_path_value
            else:
                logger.warning("'script_path' ignored because 'scripts' argument is also provided.")

        normalized_scripts = normalize_scripts(scripts)
        for script_path in normalized_scripts:
            if not script_path.exists():
                raise FileNotFoundError(f"R script path not found: {script_path}")

        if kwargs:
            raise TypeError(
                f"RFunctionCaller.__init__() received unexpected keyword arguments: {list(kwargs.keys())}"
            )

        self._namespaces: dict[str, Any] = {}
        self._namespace_roots: dict[str, Path] = {}
        self.scripts = normalized_scripts

        if packages is None:
            self.packages: list[str] = []
        elif isinstance(packages, str):
            self.packages = [packages]
        else:
            self.packages = packages

        self.headless = headless
        self.skip_renv_if_no_r = skip_renv_if_no_r

        self._r = None
        self.ro = None
        self.robjects = None
        self.pandas2ri = None
        self.localconverter = None
        self.IntVector = None
        self.FloatVector = None
        self.BoolVector = None
        self.StrVector = None
        self.ListVector = None
        self.NamedList = None

        self._renv_activated = False
        self._packages_loaded = False
        self._scripts_loaded = [False] * len(self.scripts)

    def _should_activate_renv(self) -> bool:
        if not self.path_to_renv:
            return False
        if os.environ.get("RPY_BRIDGE_SKIP_RENV") in {"1", "true", "TRUE"}:
            logger.info("[rpy-bridge] Skipping renv activation: RPY_BRIDGE_SKIP_RENV set")
            return False
        if CI_TESTING and R_HOME is None and self.skip_renv_if_no_r:
            logger.info("[rpy-bridge] Skipping renv activation in CI: R_HOME not detected")
            return False
        if R_HOME is None:
            raise RuntimeError(
                "R_HOME not detected; cannot activate renv. Install R or set R_HOME."
            )
        return True

    def _ensure_headless_env(self) -> None:
        if not self.headless:
            return
        defaults = {
            "R_DEFAULT_DEVICE": "png",
            "R_INTERACTIVE": "false",
            "R_GUI_APP_VERSION": "0",
            "RSTUDIO": "0",
        }
        for key, val in defaults.items():
            os.environ.setdefault(key, val)

    def _ensure_r_loaded(self) -> None:
        self._ensure_headless_env()

        if self.robjects is None:
            rpy2_dict = ensure_rpy2()
            self._RPY2 = rpy2_dict
            self._r = rpy2_dict["ro"]
            self.ro = rpy2_dict["robjects"]
            self.robjects = rpy2_dict["robjects"]
            self.pandas2ri = rpy2_dict["pandas2ri"]
            self.localconverter = rpy2_dict["localconverter"]
            self.IntVector = rpy2_dict["IntVector"]
            self.FloatVector = rpy2_dict["FloatVector"]
            self.BoolVector = rpy2_dict["BoolVector"]
            self.StrVector = rpy2_dict["StrVector"]
            self.ListVector = rpy2_dict["ListVector"]
            self.NamedList = rpy2_dict["NamedList"]

        if not self._renv_activated and self._should_activate_renv():
            try:
                activate_renv(self.path_to_renv)
                self._renv_activated = True
                logger.info(
                    f"[rpy-bridge.RFunctionCaller] renv activated for project: {self.path_to_renv}"
                )
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to activate renv at {self.path_to_renv}: {exc}"
                ) from exc

        r = self.robjects.r
        try:
            r('options(this.path.gui = "httpd")')
            r("options(this.path.verbose = FALSE)")
            r(
                """
                if (requireNamespace("this.path", quietly = TRUE)) {
                  try({
                    assignInNamespace(".gui_path", function(...) "httpd", ns = "this.path")
                  }, silent = TRUE)
                }
                """
            )
        except Exception:
            pass

        self.ensure_r_package("withr")

        if not hasattr(self, "_namespaces"):
            self._namespaces = {}

        for idx, script_entry in enumerate(self.scripts):
            if self._scripts_loaded[idx]:
                continue

            script_entry = script_entry.resolve()

            if script_entry.is_file():
                r_files = [script_entry]
            elif script_entry.is_dir():
                r_files = sorted(script_entry.glob("*.R"))
                if not r_files:
                    logger.warning(f"No .R files found in directory: {script_entry}")
                    self._scripts_loaded[idx] = True
                    continue
            else:
                raise ValueError(f"Invalid script path: {script_entry}")

            for script_path in r_files:
                ns_name = script_path.stem
                logger.opt(depth=2).info(
                    "[rpy-bridge.RFunctionCaller] Loading R script '{}' as namespace '{}'",
                    script_path.name,
                    ns_name,
                )

                r("env <- new.env(parent=globalenv())")
                r(f'script_path <- "{script_path.as_posix()}"')

                script_root = find_project_root(self.path_to_renv, [script_path])
                if script_root is None:
                    script_root = script_path.parent.resolve()
                script_root_arg = f'"{script_root.as_posix()}"'

                r(
                    f"""
                    withr::with_dir(
                        {script_root_arg},
                        sys.source(script_path, envir=env, chdir = TRUE)
                    )
                    """
                )

                env_obj = r("env")
                self._namespaces[ns_name] = {
                    name: env_obj[name] for name in env_obj.keys() if callable(env_obj[name])
                }
                self._namespace_roots[ns_name] = script_root

                logger.info(
                    f"[rpy-bridge.RFunctionCaller] Registered {len(self._namespaces[ns_name])} functions in namespace '{ns_name}'"
                )

            self._scripts_loaded[idx] = True

    def __getattr__(self, name: str):
        if "_namespaces" in self.__dict__ and name in self._namespaces:
            ns_env = self._namespaces[name]
            return NamespaceWrapper(ns_env)
        raise AttributeError(f"'RFunctionCaller' object has no attribute '{name}'")

    def _clean_scalar(self, x):
        robjects = self.robjects

        if x is None:
            return None
        if x in (
            getattr(robjects, "NA_Real", None),
            getattr(robjects, "NA_Integer", None),
            getattr(robjects, "NA_Logical", None),
        ):
            return None
        if x is getattr(robjects, "NA_Character", None):
            return None
        if isinstance(x, float) and np.isnan(x):
            return None
        return x

    def list_namespaces(self) -> list[str]:
        self._ensure_r_loaded()
        return list(self._namespaces.keys())

    def list_namespace_functions(self, namespace: str) -> list[str]:
        self._ensure_r_loaded()
        if namespace not in self._namespaces:
            raise ValueError(f"Namespace '{namespace}' not found")
        return [k for k, v in self._namespaces[namespace].items() if callable(v)]

    def _get_package_functions(self, pkg: str) -> list[str]:
        r = self.robjects.r
        try:
            all_objs = list(r[f'ls("package:{pkg}")'])
            funcs = [
                name
                for name in all_objs
                if r(f'is.function(get("{name}", envir=asNamespace("{pkg}")))')[0]
            ]
            return funcs
        except Exception:
            logger.warning(f"Failed to list functions for package '{pkg}'")
            return []

    def list_all_functions(self, include_packages: bool = False) -> dict[str, list[str]]:
        self._ensure_r_loaded()
        all_funcs = {}

        for ns_name, ns_env in self._namespaces.items():
            funcs = [name for name, val in ns_env.items() if callable(val)]
            all_funcs[ns_name] = funcs

        if include_packages:
            r = self.robjects.r
            try:
                pkgs = r("loadedNamespaces()")
                for pkg in pkgs:
                    funcs = self._get_package_functions(pkg)
                    if not funcs:
                        funcs = [
                            "[See official documentation for functions, datasets, and objects]"
                        ]
                    all_funcs[pkg] = funcs
            except Exception:
                pass

        return all_funcs

    def print_function_tree(self, include_packages: bool = False, max_display: int = 10):
        all_funcs = self.list_all_functions(include_packages=include_packages)

        for ns_name, funcs in all_funcs.items():
            if not funcs:
                continue
            print(f"{ns_name}/")
            for func in sorted(funcs)[:max_display]:
                print(f"  {func}")
            if len(funcs) > max_display:
                print("  ...")

    def _py2r(self, obj):
        self._ensure_r_loaded()
        robjects = self.robjects
        pandas2ri = self.pandas2ri
        FloatVector = self.FloatVector
        BoolVector = self.BoolVector
        StrVector = self.StrVector
        ListVector = self.ListVector
        localconverter = self.localconverter

        r_types = (
            robjects.vectors.IntVector,
            robjects.vectors.FloatVector,
            robjects.vectors.BoolVector,
            robjects.vectors.StrVector,
            robjects.vectors.ListVector,
            robjects.DataFrame,
        )
        if isinstance(obj, r_types):
            return obj

        def is_na(val):
            return val is None or val is pd.NA or (isinstance(val, float) and pd.isna(val))

        with localconverter(robjects.default_converter + pandas2ri.converter):
            if is_na(obj):
                return robjects.NULL
            if isinstance(obj, pd.DataFrame):
                return pandas2ri.py2rpy(obj)
            if isinstance(obj, pd.Series):
                return self._py2r(obj.tolist())
            if isinstance(obj, (int, float, bool, str)):
                return obj
            if isinstance(obj, list):
                if len(obj) == 0:
                    return FloatVector([])

                types = set(type(x) for x in obj if not is_na(x))
                if types <= {int, float}:
                    return FloatVector([robjects.NA_Real if is_na(x) else float(x) for x in obj])
                if types <= {bool}:
                    return BoolVector([robjects.NA_Logical if is_na(x) else x for x in obj])
                if types <= {str}:
                    return StrVector([robjects.NA_Character if is_na(x) else x for x in obj])
                return ListVector({str(i): self._py2r(v) for i, v in enumerate(obj)})
            if isinstance(obj, dict):
                return ListVector({k: self._py2r(v) for k, v in obj.items()})
            raise NotImplementedError(f"Cannot convert Python object to R: {type(obj)}")

    def _r2py(self, obj, top_level: bool = True):
        robjects = self.robjects
        NamedList = self.NamedList
        ListVector = self.ListVector
        StrVector = self.StrVector
        IntVector = self.IntVector
        FloatVector = self.FloatVector
        BoolVector = self.BoolVector
        NULLType = self._RPY2["NULLType"]
        localconverter = self.localconverter
        pandas2ri = self.pandas2ri

        if isinstance(obj, NULLType):
            return None

        if isinstance(obj, robjects.DataFrame):
            with localconverter(robjects.default_converter + pandas2ri.converter):
                df = robjects.conversion.rpy2py(obj)
            df = postprocess_r_dataframe(df)
            return clean_r_missing(df, caller=self)

        if isinstance(obj, (NamedList, ListVector)):
            py_obj = r_namedlist_to_dict(obj, caller=self, top_level=top_level)
            if isinstance(py_obj, list) and len(py_obj) == 1 and top_level:
                return py_obj[0]
            return py_obj

        if isinstance(obj, (StrVector, IntVector, FloatVector, BoolVector)):
            py_list = [self._clean_scalar(v) for v in obj]
            if len(py_list) == 1 and top_level:
                return py_list[0]
            return py_list

        return self._clean_scalar(obj)

    def ensure_r_package(self, pkg: str):
        r = self.robjects.r
        try:
            r(f'suppressMessages(library("{pkg}", character.only=TRUE))')
        except Exception:
            logger.info(f"[rpy-bridge.RFunctionCaller] Package '{pkg}' not found.")
            logger.warning(f"[rpy-bridge.RFunctionCaller] Installing missing R package: {pkg}")
            r(f'install.packages("{pkg}", repos="https://cloud.r-project.org")')
            r(f'suppressMessages(library("{pkg}", character.only=TRUE))')

    def call(self, func_name: str, *args, **kwargs):
        self._ensure_r_loaded()

        func = None
        source_info = None
        namespace_root = None

        if "::" in func_name:
            ns_name, fname = func_name.split("::", 1)
            if ns_name in self._namespaces:
                ns_env = self._namespaces[ns_name]
                if fname in ns_env:
                    func = ns_env[fname]
                    source_info = f"script namespace '{ns_name}'"
                    namespace_root = self._namespace_roots.get(ns_name)
                else:
                    raise ValueError(
                        f"Function '{fname}' not found in R script namespace '{ns_name}'"
                    )
            else:
                try:
                    func = self.robjects.r(f"{ns_name}::{fname}")
                    source_info = f"R package '{ns_name}'"
                except Exception as exc:
                    raise RuntimeError(
                        f"Failed to resolve R function '{func_name}': {exc}"
                    ) from exc

        else:
            for ns_name, ns_env in self._namespaces.items():
                if func_name in ns_env:
                    func = ns_env[func_name]
                    source_info = f"script namespace '{ns_name}'"
                    namespace_root = self._namespace_roots.get(ns_name)
                    break

            if func is None:
                try:
                    func = self.robjects.globalenv[func_name]
                    source_info = "global environment"
                except KeyError:
                    pass

            if func is None:
                try:
                    func = self.robjects.r[func_name]
                    source_info = "base R / loaded package"
                except KeyError:
                    raise ValueError(
                        f"R function '{func_name}' not found in any namespace, global env, or base R."
                    )

        r_args = [self._py2r(a) for a in args]
        r_kwargs = {k: self._py2r(v) for k, v in kwargs.items()}

        try:
            if source_info and source_info.startswith("script namespace") and namespace_root:
                r = self.robjects.r
                try:
                    r(f'old_wd <- getwd(); setwd("{namespace_root.as_posix()}")')
                    result = func(*r_args, **r_kwargs)
                finally:
                    try:
                        r("setwd(old_wd)")
                    except Exception:
                        pass
            else:
                result = func(*r_args, **r_kwargs)
        except Exception as exc:
            raise RuntimeError(
                f"Error calling R function '{func_name}' from {source_info}: {exc}"
            ) from exc

        log_r_call(func_name, source_info)

        return self._r2py(result)


__all__ = ["RFunctionCaller", "NamespaceWrapper"]
