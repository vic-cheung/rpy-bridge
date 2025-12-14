from __future__ import annotations

import os
import sys

os.environ.setdefault("RPY2_CFFI_MODE", "ABI")

sys.path.insert(0, os.path.abspath("../src"))

project = "rpy-bridge"
author = "Victoria Cheung"
release = "0.3.5"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
]

autodoc_mock_imports = [
    "rpy2",
    "rpy2.robjects",
    "rpy2.rinterface_lib",
    "rpy2.rinterface",
    "loguru",
]

autodoc_typehints = "description"
autosummary_generate = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "inherited-members": True,
}
