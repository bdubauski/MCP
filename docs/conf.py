#!/usr/bin/env python3

import os

extensions = [
    'sphinx.ext.viewcode',
]

templates_path = []
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'mcp'
copyright = '2019, Virtustream'
author = 'Peter Howe'

version = os.environ[ 'VERSION' ]
release = '{0}-{1}'.format( os.environ[ 'VERSION' ], os.environ[ 'BUILD' ] )


language = None

exclude_patterns = []

pygments_style = 'sphinx'

todo_include_todos = False

html_theme = 'alabaster'

html_static_path = ['_static']

html_show_sourcelink = False

# Output file base name for HTML help builder.
htmlhelp_basename = 'mcpdoc'

latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '10pt'
}

latex_documents = [
    (master_doc, 'mcp.tex', 'MCP Documentation',
     'Peter Howe', 'manual'),
]
