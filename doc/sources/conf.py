# -*- coding: utf-8 -*-
#
# Kivy documentation build configuration file, created by
# sphinx-quickstart on Wed Jan 21 22:37:12 2009.
#
# This file is execfile()d with the current directory set to its containing
# dir.
#
# The contents of this file are pickled, so don't put values in the namespace
# that aren't pickleable (module imports are okay, they're removed
# automatically).
#
# All configuration values have a default value; values that are commented out
# serve to show the default value.

import os
import sys

# If your extensions are in another directory, add it here. If the directory
# is relative to the documentation root, use os.path.abspath to make it
# absolute, like shown here.
sys.path.insert(0, os.path.abspath('sphinxext'))
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(base_dir))

# General configuration
# ---------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'autodoc', 'sphinx.ext.todo', 'preprocess', 'sphinx.ext.ifconfig',
    'sphinx.ext.viewcode', 'sphinx.ext.mathjax']

# Todo configuration
todo_include_todos = True

# XXX HACK mathieu: monkey patch the autodoc module, to give a better priority
# for ClassDocumenter, or the cython class will be documented as AttributeClass
import sphinx.ext.autodoc
sphinx.ext.autodoc.ClassDocumenter.priority = 10

# Add any paths that contain templates here, relative to this directory.
if os.environ.get('READTHEDOCS') == 'True':
    templates_path = ['_templates']
else:
    templates_path = ['.templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General substitutions.
project = 'Kivy'
copyright = '2010, The Kivy Authors'

# The default replacements for |version| and |release|, also used in various
# other places throughout the built documents.
#
os.environ['KIVY_DOC_INCLUDE'] = '1'
import kivy
print(kivy.__file__)

version = kivy.__version__
release = kivy.__version__
base = 'autobuild.py-done'
if not os.path.exists(os.path.join(os.path.dirname(base_dir), base)):
    import autobuild
import gallery

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ''
# Else, today_fmt is used as the format for a strftime call.
today_fmt = '%B %d, %Y'

# suppress exclusion warnings
exclude_patterns = ['gsoc201*']

# The reST default role (used for this markup: `text`) to use for all documents
# default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
# add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
# add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
# show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'kivy_pygments_theme.KivyStyle'


# Options for HTML output
# -----------------------

# The style sheet to use for HTML and HTML Help pages. A file of that name
# must exist either in Sphinx' static/ path, or in one of the custom paths
# given in html_static_path.
html_style = 'fresh.css'

# Check for theme (remove 'if' when switched to RTD)
if os.environ.get('READTHEDOCS') == 'True':
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
# html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
# html_short_title = None

# The name of an image file (within the static path) to place at the top of
# the sidebar.
html_logo = '.static/logo-kivy.png'

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
# html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['.static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
# html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
# html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
# html_additional_pages = {}

# If false, no module index is generated.
# html_use_modindex = True

# If false, no index is generated.
# html_use_index = True

# If true, the index is split into individual pages for each letter.
# html_split_index = False

# If true, the reST sources are included in the HTML build as _sources/<name>.
# html_copy_source = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
# html_use_opensearch = ''

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
# html_file_suffix = ''

# Output file base name for HTML help builder.
htmlhelp_basename = 'Kivydoc'


# Options for LaTeX output
# ------------------------

# The paper size ('letter' or 'a4').
# latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
# latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, document class [manual]).
latex_documents = [
  ('index', 'Kivy.tex', 'Kivy Documentation',
   'The Kivy Developers', 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
# latex_logo = None

latex_elements = {
    'fontpkg':      r'\usepackage{mathpazo}',
    'papersize':    'a4paper',
    'pointsize':    '10pt',
    'preamble':     r'\usepackage{kivystyle}'
}
latex_additional_files = ['kivystyle.sty',
                          '../../kivy/data/logo/kivy-icon-512.png']

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
latex_use_parts = True

# Additional stuff for the LaTeX preamble.
# latex_preamble = ''

# Documents to append as an appendix to all manuals.
# latex_appendices = []

# If false, no module index is generated.
# latex_use_modindex = True

from kivy import setupconfig

replacements = {
    'cython_install': 'Cython==' + setupconfig.CYTHON_MAX,
    'cython_note': (
        'This version of **Kivy requires at least Cython version {0}**, '
        'and has been tested through {1}. Later versions may work, '
        'but as they have not been tested there is no guarantee.'
    ).format(setupconfig.CYTHON_MIN, setupconfig.CYTHON_MAX)
}

if setupconfig.CYTHON_BAD:
    replacements['cython_note'] += (' **The following versions of Cython have '
                                    'known issues and cannot be used with Kivy'
                                    ': {0}**').format(setupconfig.CYTHON_BAD)

epilog = []

for key, value in replacements.items():
    rep = '.. |{0}| replace:: {1}'.format(key, value)
    epilog.append(rep)

rst_epilog = '\n'.join(epilog)
