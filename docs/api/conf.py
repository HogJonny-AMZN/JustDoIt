# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('../..'))  # Add repo root to PYTHONPATH

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'JustDoIt'
copyright = '2026, Jonny Galloway'
author = 'Jonny Galloway'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',           # Extract docstrings
    'sphinx.ext.napoleon',          # Parse ReST/NumPy/Google style docstrings
    'sphinx.ext.viewcode',          # Add [source] links
    'sphinx.ext.intersphinx',       # Link to Python docs
    'sphinx_autodoc_typehints',     # Render type hints
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for autodoc -----------------------------------------------------

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'private-members': False,
    'special-members': '__init__',
    'inherited-members': False,
    'show-inheritance': True,
}

# Mock optional dependencies to avoid import errors during doc build
autodoc_mock_imports = ['PIL', 'numpy', 'sounddevice']

# -- Options for Napoleon ----------------------------------------------------

napoleon_google_docstring = False
napoleon_numpy_docstring = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_include_init_with_doc = True

# -- Options for intersphinx -------------------------------------------------

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'PIL': ('https://pillow.readthedocs.io/en/stable/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
