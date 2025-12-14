"""
R–Python Integration Utility

Provides tools to load R scripts, activate renv environments, and call R functions
directly from Python, with automatic conversion between R and Python data types.

----------
Requirements
----------
- R must be installed and accessible in your system environment.
- Ensure compatibility with your R project's renv setup (or any other R environment you use).

Features
----------
- Lazy loading of rpy2 and R runtime.
- Activation of renv environments for isolated R project dependencies.
- Support for sourcing individual R scripts or directories of scripts.
- Namespace-based access to R functions.
- Automatic conversion between R vectors, data frames, and Python types (pandas, lists, scalars).
- Utilities for cleaning and aligning data frames between R and Python.
"""

# ruff: noqa: E402
# %%
# Import libraries
import importlib.util
import os
import subprocess
import sys
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, Union

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", message="Environment variable .* redefined by R")


if TYPE_CHECKING:
    import logging as logging_module

    from loguru import Logger as LoguruLogger

    LoggerType = Union[LoguruLogger, logging_module.Logger]

else:
    LoggerType = None  # runtime doesn’t need the type object

import logging

try:
    from loguru import logger as loguru_logger  # type: ignore

    logger = loguru_logger
except ImportError:
    logging.basicConfig()
    logger = logging.getLogger("rpy-bridge")


# ---------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------
def _normalize_scripts(
    scripts: Union[str, Path, Iterable[Union[str, Path]], None],
) -> list[Path]:
    if scripts is None:
        return []
    if isinstance(scripts, (str, Path)):
        return [Path(scripts).resolve()]
    try:
        return [Path(s).resolve() for s in scripts]
    except TypeError:
        raise TypeError(
            f"Invalid type for 'scripts': {type(scripts)}. Must be str, Path, or list/iterable thereof."
        )


# ---------------------------------------------------------------------
# R detection and rpy2 installation
# ---------------------------------------------------------------------
def ensure_rpy2_available() -> None:
    """
    Ensure rpy2 is importable.
    Do NOT attempt to install dynamically; fail with clear instructions instead.
    """
    if importlib.util.find_spec("rpy2") is None:
        raise RuntimeError(
            "\n[Error] rpy2 is not installed. Please install it in your Python environment:\n"
            "  pip install rpy2\n\n"
            "Make sure your Python environment can access your system R installation.\n"
            "On macOS with Homebrew: brew install r\n"
            "On Linux: apt install r-base  (Debian/Ubuntu) or yum install R (CentOS/RHEL)\n"
            "On Windows: install R from https://cran.r-project.org\n"
        )


def find_r_home() -> str | None:
    """
    Detect system R installation.
    """
    try:
        r_home = subprocess.check_output(
            ["R", "--vanilla", "--slave", "-e", "cat(R.home())"],
            stderr=subprocess.PIPE,
            text=True,
        ).strip()
        if r_home.endswith(">"):  # sometimes R console prints >
            r_home = r_home[:-1].strip()
        return r_home
    except FileNotFoundError:
        # fallback paths (Linux, macOS Homebrew, Windows)
        possible_paths = [
            "/usr/lib/R",
            "/usr/local/lib/R",
            "/opt/homebrew/Cellar/r/4.5.2/lib/R",  # macOS Homebrew
            "C:\\Program Files\\R\\R-4.5.2",  # Windows
        ]
        for p in possible_paths:
            if os.path.exists(p):
                return p
    return None


# Determine if we're running in CI / testing
CI_TESTING = (
    os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("TESTING") == "1"
)

R_HOME = os.environ.get("R_HOME")
if not R_HOME:
    R_HOME = find_r_home()
    if not R_HOME:
        if CI_TESTING:
            logger.warning(
                "R not found; skipping all R-dependent setup in CI/testing environment."
            )
            R_HOME = None  # Explicitly None to signal "no R available"
        else:
            raise RuntimeError("R not found. Please install R or add it to PATH.")
    else:
        os.environ["R_HOME"] = R_HOME

logger.info(
    f"R_HOME = {R_HOME if R_HOME else 'not detected; R-dependent code skipped'}"
)

# Only configure platform-specific library paths if R is available
if R_HOME:
    if sys.platform == "darwin":
        lib_path = os.path.join(R_HOME, "lib")
        if lib_path not in os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", ""):
            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = (
                f"{lib_path}:{os.environ.get('DYLD_FALLBACK_LIBRARY_PATH','')}"
            )

    elif sys.platform.startswith("linux"):
        lib_path = os.path.join(R_HOME, "lib")
        ld_path = os.environ.get("LD_LIBRARY_PATH", "")
        if lib_path not in ld_path.split(":"):
            os.environ["LD_LIBRARY_PATH"] = f"{lib_path}:{ld_path}"

    elif sys.platform.startswith("win"):
        bin_path = os.path.join(R_HOME, "bin", "x64")
        path_env = os.environ.get("PATH", "")
        if bin_path not in path_env.split(os.pathsep):
            os.environ["PATH"] = f"{bin_path}{os.pathsep}{path_env}"


# ---------------------------------------------------------------------
# Lazy rpy2 import machinery
# ---------------------------------------------------------------------
_RPY2: dict | None = None


def _require_rpy2(raise_on_missing: bool = True) -> dict | None:
    global _RPY2
    if _RPY2 is not None:
        return _RPY2

    try:
        import rpy2.robjects as ro
        from rpy2 import robjects
        from rpy2.rinterface_lib.sexp import NULLType
        from rpy2.rlike.container import NamedList
        from rpy2.robjects import pandas2ri
        from rpy2.robjects.conversion import localconverter
        from rpy2.robjects.vectors import (
            BoolVector,
            FloatVector,
            IntVector,
            ListVector,
            StrVector,
        )

        _RPY2 = {
            "ro": ro,
            "robjects": robjects,
            "pandas2ri": pandas2ri,
            "localconverter": localconverter,
            "BoolVector": BoolVector,
            "FloatVector": FloatVector,
            "IntVector": IntVector,
            "ListVector": ListVector,
            "StrVector": StrVector,
            "NULLType": NULLType,
            "NamedList": NamedList,
        }
        return _RPY2

    except ImportError as e:
        if raise_on_missing:
            raise RuntimeError(
                "R support requires optional dependency `rpy2`. Install with: pip install rpy-bridge[r]"
            ) from e
        return None


def _ensure_rpy2() -> dict:
    global _RPY2
    if _RPY2 is None:
        _RPY2 = _require_rpy2()
    assert _RPY2 is not None, "_require_rpy2() returned None"
    return _RPY2


# ---------------------------------------------------------------------
# Activate renv
# ---------------------------------------------------------------------
def activate_renv(path_to_renv: Path) -> None:
    r = _ensure_rpy2()
    robjects = r["robjects"]

    path_to_renv = path_to_renv.resolve()
    if path_to_renv.name == "renv" and (path_to_renv / "activate.R").exists():
        renv_dir = path_to_renv
        project_dir = path_to_renv.parent
    else:
        renv_dir = path_to_renv / "renv"
        project_dir = path_to_renv

    renv_activate = renv_dir / "activate.R"
    renv_lock = project_dir / "renv.lock"

    if not renv_activate.exists() or not renv_lock.exists():
        raise FileNotFoundError(f"[Error] renv environment incomplete: {path_to_renv}")

    renviron_file = project_dir / ".Renviron"
    if renviron_file.is_file():
        os.environ["R_ENVIRON_USER"] = str(renviron_file)
        logger.info(f"R_ENVIRON_USER set to: {renviron_file}")

    rprofile_file = project_dir / ".Rprofile"
    if rprofile_file.is_file():
        robjects.r(f'source("{rprofile_file.as_posix()}")')
        logger.info(f".Rprofile sourced: {rprofile_file}")

    try:
        robjects.r("suppressMessages(library(renv))")
    except Exception:
        logger.info("Installing renv package in project library...")
        robjects.r(
            f'install.packages("renv", repos="https://cloud.r-project.org", lib="{renv_dir / "library"}")'
        )
        robjects.r("library(renv)")

    robjects.r(f'renv::load("{project_dir.as_posix()}")')
    logger.info(f"renv environment loaded for project: {project_dir}")


# ---------------------------------------------------------------------
# NamespaceWrapper
# ---------------------------------------------------------------------
class NamespaceWrapper:
    """
    Wraps an R script namespace for Python attribute access.
    """

    def __init__(self, env):
        self._env = env

    def __getattr__(self, func_name):
        if func_name in self._env:
            return self._env[func_name]
        raise AttributeError(f"Function '{func_name}' not found in R namespace")

    def list_functions(self):
        """
        Return a list of callable functions in this namespace.
        """
        return [k for k, v in self._env.items() if callable(v)]


# ---------------------------------------------------------------------
# RFunctionCaller
# ---------------------------------------------------------------------
class RFunctionCaller:
    """
    Utility to load and call R functions from scripts, lazily loading rpy2 and activating renv.

    Supports:
    - Single or multiple R scripts
    - R script directories (sources all `.R` files inside)
    - Base R functions
    - Functions in loaded packages
    - Automatic conversion of Python types to R objects

    Args:
        scripts:
            Path or list of Paths.
            Each path may be:
            - an R script (.R file)
            - a directory containing R scripts (all *.R files are sourced)
            - scripts in subdirectories are not automatically sourced

    """

    def __init__(
        self,
        path_to_renv: Path | None = None,
        scripts: str | Path | list[str | Path] | None = None,
        packages: str | list[str] | None = None,
        **kwargs,  # catch unexpected keywords
    ):
        # --- Handle deprecated 'script_path' ---
        if "script_path" in kwargs:
            script_path_value = kwargs.pop("script_path")
            warnings.warn(
                "'script_path' argument is deprecated. "
                "Please use 'scripts' instead (accepts a Path or list of Paths).",
                DeprecationWarning,
                stacklevel=2,
            )
            if scripts is None:
                scripts = script_path_value
            else:
                # Both provided → prioritize scripts and ignore script_path
                logger.warning(
                    "'script_path' ignored because 'scripts' argument is also provided."
                )

        self.scripts = _normalize_scripts(scripts)

        # --- Check all scripts exist immediately ---
        for script_path in self.scripts:
            if not script_path.exists():
                raise FileNotFoundError(f"R script path not found: {script_path}")

        # Raise error if other unexpected kwargs remain
        if kwargs:
            raise TypeError(
                f"RFunctionCaller.__init__() received unexpected keyword arguments: {list(kwargs.keys())}"
            )

        self.path_to_renv = path_to_renv.resolve() if path_to_renv else None
        self._namespaces: dict[str, Any] = {}

        # Normalize scripts to a list
        if scripts is None:
            self.scripts: list[Path] = []
        elif isinstance(scripts, Path):
            self.scripts = [scripts.resolve()]
        else:
            self.scripts = [s.resolve() for s in scripts]

        # Normalize packages to a list
        if packages is None:
            self.packages: list[str] = []
        elif isinstance(packages, str):
            self.packages = [packages]
        else:
            self.packages = packages

        # Lazy-loaded attributes
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

        # Internal state
        self._renv_activated = False
        self._packages_loaded = False
        self._scripts_loaded = [False] * len(self.scripts)

    # -----------------------------------------------------------------
    # Internal: lazy R loading
    # -----------------------------------------------------------------
    def _ensure_r_loaded(self) -> None:
        """
        Ensure R runtime is initialized and all configured R scripts
        are sourced exactly once, in isolated environments.
        """
        if self.robjects is None:
            rpy2_dict = _ensure_rpy2()
            self._RPY2 = rpy2_dict  # cache in instance
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

        r = self.robjects.r

        # Ensure required R package
        self.ensure_r_package("withr")

        if not hasattr(self, "_namespaces"):
            self._namespaces: dict[str, dict[str, Any]] = {}

        # --- Iterate over scripts ---
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
                logger.info(
                    f"Loading R script '{script_path.name}' as namespace '{ns_name}'"
                )

                r("env <- new.env(parent=globalenv())")
                r(f'script_path <- "{script_path.as_posix()}"')

                r(
                    """
                    withr::with_dir(
                        dirname(script_path),
                        sys.source(basename(script_path), envir=env)
                    )
                    """
                )

                env_obj = r("env")
                self._namespaces[ns_name] = {
                    name: env_obj[name]
                    for name in env_obj.keys()
                    if callable(env_obj[name])
                }

                logger.info(
                    f"Registered {len(self._namespaces[ns_name])} functions in namespace '{ns_name}'"
                )

            self._scripts_loaded[idx] = True

    # -----------------------------------------------------------------
    # Autocomplete-friendly attribute access for script namespaces
    # -----------------------------------------------------------------
    def __getattr__(self, name: str):
        if "_namespaces" in self.__dict__ and name in self._namespaces:
            ns_env = self._namespaces[name]
            return NamespaceWrapper(ns_env)
        raise AttributeError(f"'RFunctionCaller' object has no attribute '{name}'")

    def _clean_scalar(self, x):
        """
        Clean R-style missing values to pandas/NumPy equivalents.
        Called inside _r2py on each vector element; atomic/scalar only.
        """
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
        """
        Return all loaded R script namespaces.
        """
        self._ensure_r_loaded()
        return list(self._namespaces.keys())

    def list_namespace_functions(self, namespace: str) -> list[str]:
        """
        Return all callable functions in a specific namespace.
        """
        self._ensure_r_loaded()
        if namespace not in self._namespaces:
            raise ValueError(f"Namespace '{namespace}' not found")
        return [k for k, v in self._namespaces[namespace].items() if callable(v)]

    def _get_package_functions(self, pkg: str) -> list[str]:
        """
        Return a list of callable functions from a loaded R package.
        """
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

    def list_all_functions(
        self, include_packages: bool = False
    ) -> dict[str, list[str]]:
        """
        Return all callable R functions grouped by script namespace and package.
        """
        self._ensure_r_loaded()
        all_funcs = {}

        # --- Script namespaces ---
        for ns_name, ns_env in self._namespaces.items():
            funcs = [name for name, val in ns_env.items() if callable(val)]
            all_funcs[ns_name] = funcs

        # --- Loaded R packages ---
        if include_packages:
            r = self.robjects.r
            try:
                pkgs = r("loadedNamespaces()")
                for pkg in pkgs:
                    funcs = self._get_package_functions(pkg)
                    if not funcs:
                        # Add a placeholder note
                        funcs = [
                            "[See official documentation for functions, datasets, and objects]"
                        ]
                    all_funcs[pkg] = funcs
            except Exception:
                pass

        return all_funcs

    def print_function_tree(
        self, include_packages: bool = False, max_display: int = 10
    ):
        """
        Pretty-print all callable R functions in a tree-like structure.

        Args:
            include_packages: Include functions from loaded R packages.
            max_display: Maximum functions to show per namespace/package.
        """
        all_funcs = self.list_all_functions(include_packages=include_packages)

        for ns_name, funcs in all_funcs.items():
            if not funcs:
                continue
            print(f"{ns_name}/")
            for f in sorted(funcs)[:max_display]:
                print(f"  {f}")
            if len(funcs) > max_display:
                print("  ...")

    # -----------------------------------------------------------------
    # Python -> R conversion
    # -----------------------------------------------------------------
    def _py2r(self, obj):
        """
        Convert Python objects to R objects robustly.
        Handles scalars, None/pd.NA, lists, dicts, and pandas DataFrames.
        """
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

        def is_na(x):
            return x is None or x is pd.NA or (isinstance(x, float) and pd.isna(x))

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
                    return FloatVector(
                        [robjects.NA_Real if is_na(x) else float(x) for x in obj]
                    )
                if types <= {bool}:
                    return BoolVector(
                        [robjects.NA_Logical if is_na(x) else x for x in obj]
                    )
                if types <= {str}:
                    return StrVector(
                        [robjects.NA_Character if is_na(x) else x for x in obj]
                    )
                return ListVector({str(i): self._py2r(v) for i, v in enumerate(obj)})
            if isinstance(obj, dict):
                return ListVector({k: self._py2r(v) for k, v in obj.items()})
            raise NotImplementedError(f"Cannot convert Python object to R: {type(obj)}")

    # -----------------------------------------------------------------
    # R -> Python conversion
    # -----------------------------------------------------------------
    def _r2py(self, obj, top_level=True):
        robjects = self.robjects
        NamedList = self.NamedList
        ListVector = self.ListVector
        StrVector = self.StrVector
        IntVector = self.IntVector
        FloatVector = self.FloatVector
        BoolVector = self.BoolVector
        NULLType = self._RPY2["NULLType"]
        lc = self.localconverter
        pandas2ri = self.pandas2ri

        if isinstance(obj, NULLType):
            return None

        if isinstance(obj, robjects.DataFrame):
            with lc(robjects.default_converter + pandas2ri.converter):
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

    # -----------------------------------------------------------------
    # Public: ensure R package is available
    # -----------------------------------------------------------------
    def ensure_r_package(self, pkg: str):
        r = self.robjects.r
        try:
            r(f'suppressMessages(library("{pkg}", character.only=TRUE))')
        except Exception:
            logger.info(f"Package '{pkg}' not found.")
            logger.warning(f"Installing missing R package: {pkg}")
            r(f'install.packages("{pkg}", repos="https://cloud.r-project.org")')
            r(f'suppressMessages(library("{pkg}", character.only=TRUE))')

    # -----------------------------------------------------------------
    # Public: call an R function
    # -----------------------------------------------------------------
    def call(self, func_name: str, *args, **kwargs):
        self._ensure_r_loaded()

        func = None
        source_info = None

        if "::" in func_name:
            ns_name, fname = func_name.split("::", 1)
            if ns_name in self._namespaces:
                ns_env = self._namespaces[ns_name]
                if fname in ns_env:
                    func = ns_env[fname]
                    source_info = f"script namespace '{ns_name}'"
                else:
                    raise ValueError(
                        f"Function '{fname}' not found in R script namespace '{ns_name}'"
                    )
            else:
                try:
                    func = self.robjects.r(f"{ns_name}::{fname}")
                    source_info = f"R package '{ns_name}'"
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to resolve R function '{func_name}': {e}"
                    ) from e

        else:
            for ns_name, ns_env in self._namespaces.items():
                if func_name in ns_env:
                    func = ns_env[func_name]
                    source_info = f"script namespace '{ns_name}'"
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
            result = func(*r_args, **r_kwargs)
        except Exception as e:
            raise RuntimeError(
                f"Error calling R function '{func_name}' from {source_info}: {e}"
            ) from e

        logger.info(f"Called R function '{func_name}' from {source_info}")
        return self._r2py(result)


# %%
# ------------------------------
# Utility functions for R ↔ Python
# ------------------------------
def r_namedlist_to_dict(namedlist, caller: RFunctionCaller, top_level=False):
    r = _ensure_rpy2()
    NamedList = r["NamedList"]
    ListVector = r["ListVector"]

    if isinstance(namedlist, (NamedList, ListVector)):
        names = namedlist.names if not callable(namedlist.names) else namedlist.names()

        if names and all(str(i) == str(name) for i, name in enumerate(names)):
            out = []
            for v in namedlist:
                val = caller._r2py(v, top_level=False)
                out.append(val)
            return out

        result = {}
        for i, val in enumerate(namedlist):
            key = names[i] if names and i < len(names) else str(i)
            v_py = caller._r2py(val, top_level=False)
            result[str(key)] = v_py
        return result

    return caller._r2py(namedlist, top_level=top_level)


def clean_r_dataframe(r_df: pd.DataFrame) -> pd.DataFrame:
    for attr in [".groups", ".rows"]:
        try:
            del r_df.attrs[attr]
        except (KeyError, AttributeError):
            pass
    return r_df


def fix_string_nans(df: pd.DataFrame) -> pd.DataFrame:
    return df.replace(["nan", "NaN", "NA", "na", ""], pd.NA)


def normalize_single_df_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.replace(["", "nan", "NaN", "NA", "na"], pd.NA)
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_object_dtype(series):
            coerced = pd.to_numeric(series, errors="coerce")
            if coerced.notna().sum() >= series.notna().sum() * 0.5:
                df[col] = coerced
        if pd.api.types.is_integer_dtype(df[col]) and df[col].isna().any():
            df[col] = df[col].astype("float64")
    return df


def fix_r_dataframe_types(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_integer_dtype(series):
            df[col] = series.mask(series == -2147483648, pd.NA)
        if pd.api.types.is_numeric_dtype(series):
            values = series.dropna()
            if not values.empty and values.between(10000, 40000).all():
                try:
                    df[col] = pd.to_datetime("1970-01-01") + pd.to_timedelta(
                        series, unit="D"
                    )
                except Exception:
                    pass
        if pd.api.types.is_datetime64tz_dtype(series):
            df[col] = series.dt.tz_localize(None)
    return df


def postprocess_r_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = fix_r_dataframe_types(df)
    df = fix_string_nans(df)
    df = normalize_single_df_dtypes(df)
    if df.index.dtype == object:
        try:
            int_index = df.index.astype(int)
            if (int_index == np.arange(len(df)) + 1).all():
                df.index = pd.RangeIndex(start=0, stop=len(df))
        except Exception:
            pass
    return df


def clean_r_missing(obj, caller: RFunctionCaller):
    robjects = caller.robjects
    NA_MAP = {
        getattr(robjects, "NA_Real", None): np.nan,
        getattr(robjects, "NA_Integer", None): np.nan,
        getattr(robjects, "NA_Logical", None): np.nan,
        getattr(robjects, "NA_Character", None): pd.NA,
    }

    if isinstance(obj, pd.DataFrame):
        for col in obj.columns:
            obj[col] = obj[col].apply(lambda x: clean_r_missing(x, caller))
        return obj
    elif isinstance(obj, dict):
        return {k: clean_r_missing(v, caller) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_r_missing(v, caller) for v in obj]
    else:
        return NA_MAP.get(obj, obj)


# ---------------------------------------------------------------------
# DataFrame comparison utilities
# ---------------------------------------------------------------------
def normalize_dtypes(
    df1: pd.DataFrame, df2: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    for col in df1.columns.intersection(df2.columns):
        df1[col] = df1[col].replace("", pd.NA)
        df2[col] = df2[col].replace("", pd.NA)
        s1, s2 = df1[col], df2[col]
        dtype1, dtype2 = s1.dtype, s2.dtype
        if (
            pd.api.types.is_numeric_dtype(dtype1)
            and pd.api.types.is_object_dtype(dtype2)
        ) or (
            pd.api.types.is_object_dtype(dtype1)
            and pd.api.types.is_numeric_dtype(dtype2)
        ):
            try:
                df1[col] = pd.to_numeric(s1, errors="coerce")
                df2[col] = pd.to_numeric(s2, errors="coerce")
                continue
            except Exception:
                pass
        if pd.api.types.is_numeric_dtype(dtype1) and pd.api.types.is_numeric_dtype(
            dtype2
        ):
            df1[col] = df1[col].astype("float64")
            df2[col] = df2[col].astype("float64")
            continue
        if pd.api.types.is_object_dtype(dtype1) or pd.api.types.is_object_dtype(dtype2):
            df1[col] = df1[col].astype(str)
            df2[col] = df2[col].astype(str)
    return df1, df2


def align_numeric_dtypes(
    df1: pd.DataFrame, df2: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    for col in df1.columns.intersection(df2.columns):
        s1, s2 = df1[col].replace("", pd.NA), df2[col].replace("", pd.NA)
        try:
            s1_num = pd.to_numeric(s1, errors="coerce")
            s2_num = pd.to_numeric(s2, errors="coerce")
            if not s1_num.isna().all() or not s2_num.isna().all():
                df1[col] = s1_num.astype("float64")
                df2[col] = s2_num.astype("float64")
                continue
        except Exception:
            pass
        df1[col], df2[col] = s1, s2
    return df1, df2


def compare_r_py_dataframes(
    df1: pd.DataFrame, df2: pd.DataFrame, float_tol: float = 1e-8
) -> dict:
    results: dict[str, Any] = {
        "shape_mismatch": False,
        "columns_mismatch": False,
        "index_mismatch": False,
        "numeric_diffs": {},
        "non_numeric_diffs": {},
    }
    df2 = fix_r_dataframe_types(df2)
    df1 = fix_string_nans(df1)
    df2 = fix_string_nans(df2)
    df1, df2 = normalize_dtypes(df1.copy(), df2.copy())
    df1, df2 = align_numeric_dtypes(df1, df2)
    if df1.shape != df2.shape:
        results["shape_mismatch"] = True
        print(f"[Warning] Shape mismatch: df1 {df1.shape} vs df2 {df2.shape}")
    if set(df1.columns) != set(df2.columns):
        results["columns_mismatch"] = True
        print("[Warning] Column mismatch:")
        print(f"  df1: {df1.columns}")
        print(f"  df2: {df2.columns}")
        common_cols = df1.columns.intersection(df2.columns)
    else:
        common_cols = df1.columns
    df1_aligned, df2_aligned = df1.loc[:, common_cols], df2.loc[:, common_cols]
    for col in common_cols:
        col_py, col_r = df1_aligned[col], df2_aligned[col]
        if pd.api.types.is_numeric_dtype(col_py) and pd.api.types.is_numeric_dtype(
            col_r
        ):
            col_py, col_r = col_py.align(col_r)
            close = np.isclose(
                col_py.fillna(np.nan),
                col_r.fillna(np.nan),
                atol=float_tol,
                equal_nan=True,
            )
            if not close.all():
                results["numeric_diffs"][col] = pd.DataFrame(
                    {"df1": col_py[~close], "df2": col_r[~close]}
                )
        else:
            unequal = ~col_py.eq(col_r)
            both_na = col_py.isna() & col_r.isna()
            unequal = unequal & ~both_na
            if unequal.any():
                results["non_numeric_diffs"][col] = pd.DataFrame(
                    {"df1": col_py[unequal], "df2": col_r[unequal]}
                )
    return results
