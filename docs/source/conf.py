# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PyPSA-AU'
copyright = '2025, Arthur Bond'
author = 'Arthur Bond'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["myst_parser",]
myst_heading_anchors = 3

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_book_theme'
html_static_path = ['_static']

html_short_title = "PyPSA-AU"

html_theme_options = {
    "repository_url": "https://github.com/ArthurBond/pypsa-au",
    "use_repository_button": True,
    "show_navbar_depth": 1,
}

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = "./_static/pypsa-logo.png"