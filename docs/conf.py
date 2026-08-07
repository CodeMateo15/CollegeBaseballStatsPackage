# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ncaa_bbStats'
copyright = '2025, Mateo Biggs'
author = 'Mateo Biggs'

# Read from the installed package rather than hardcoding, which drifted: this
# said 1.0.0 while pyproject.toml said 1.1.0.
try:
    from importlib.metadata import version as _version

    release = _version('ncaa_bbStats')
except Exception:  # not installed, e.g. a bare `sphinx-build` in a checkout
    release = '0.0.0+unknown'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx_rtd_theme',
    'sphinx.ext.autosectionlabel',
    'sphinx_copybutton',
    'myst_parser',
]

# myst_parser lets docs/data_provenance.rst include the root DATA_PROVENANCE.md
# so the provenance record has exactly one source of truth.
source_suffix = {'.rst': 'restructuredtext', '.md': 'markdown'}

# Namespace section labels by document. Without this, every page's "See Also",
# "Functions", and "Usage" heading collides with every other page's, producing a
# duplicate-label warning per heading and making :ref: targets ambiguous.
autosectionlabel_prefix_document = True

# data_provenance.rst includes DATA_PROVENANCE.md from line 1 onward, so the
# fragment starts at H2 by design -- the page title supplies the H1. That is
# what myst.header flags, and it is expected here.
suppress_warnings = ['myst.header']

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# 'display_version' was removed in sphinx_rtd_theme 3.x and warns if passed.
html_theme_options = {
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
    # Toc options
    'sticky_navigation': True,
    'titles_only': False
}
