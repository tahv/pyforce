"""Configuration file for the Sphinx documentation builder.

Documentation:
    https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

import importlib.metadata
import sys
from pathlib import Path

PROJECT_ROOT_DIR = Path(__file__).parents[1].resolve()
SRC_DIR = (PROJECT_ROOT_DIR / "src").resolve()
sys.path.append(str(SRC_DIR))

# -- Project information -----------------------------------------------------

project = "Pyforce"
author = "Thibaud Gambier"
copyright = f"2024, {author}"  # noqa: A001
release = importlib.metadata.version("pyforce-p4")
version = ".".join(release.split(".", 2)[0:2])

# -- General configuration ---------------------------------------------------

# fmt: off
extensions = [
    "myst_parser",                     # markdown
    "sphinx.ext.autodoc",              # docstring
    "sphinxcontrib.autodoc_pydantic",  # docstring / pydantic compatibility
    "sphinx.ext.napoleon",             # google style docstring
    "sphinx.ext.intersphinx",          # cross-projects references
    "enum_tools.autoenum",
]
# fmt: on

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
maximum_signature_line_length = 80
default_role = "any"

# -- Extensions configuration ------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

autodoc_pydantic_model_show_json = False
autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_model_show_validator_summary = False
autodoc_pydantic_model_show_field_summary = False
autodoc_pydantic_field_show_constraints = False
autodoc_pydantic_field_list_validators = False

autodoc_pydantic_field_show_default = False
autodoc_pydantic_field_show_required = False

autodoc_class_signature = "separated"
autodoc_default_options = {
    "exclude-members": "__new__",
}

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
# html_static_path = ["_static"]
html_title = "Pyforce"
