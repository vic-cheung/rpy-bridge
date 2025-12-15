from __future__ import annotations

import os
import sys

os.environ.setdefault("RPY2_CFFI_MODE", "ABI")

sys.path.insert(0, os.path.abspath("../src"))

project = "rpy-bridge"
author = "Victoria Cheung"
release = "0.5.0"

html_title = "rpy-bridge: Python-to-R orchestrator (renv, headless, robust conversions)"
html_short_title = "rpy-bridge orchestrator"
html_baseurl = "https://rpy-bridge.readthedocs.io/en/stable/"
html_theme_options = {
    "display_version": True,
    "analytics_id": "",
}

html_meta = {
    "description": (
        "rpy-bridge: Python-controlled R execution orchestrator with renv activation, "
        "project-root inference, headless-safe startup, and robust Python↔R conversions. "
        "Not a thin rpy2 wrapper—built for reproducible R from Python."
    ),
}

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx_sitemap",
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
