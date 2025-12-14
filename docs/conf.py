import os
import sys

os.environ.setdefault("RPY2_CFFI_MODE", "ABI")


# Put the package src on sys.path so autodoc can import it
sys.path.insert(0, os.path.abspath("../src"))

project = "rpy-bridge"
author = "Victoria Cheung"
release = "0.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
]

# Avoid importing heavy dependencies (R/rpy2) during doc builds on RTD by mocking
autodoc_mock_imports = [
    "rpy2",
    "rpy2.robjects",
    "rpy2.rinterface_lib",
    "rpy2.rinterface",
    "numpy",
    "pandas",
    "loguru",
]

autosummary_generate = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# Show members for classes automatically
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "inherited-members": True,
}
