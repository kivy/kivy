#
# Little hack to remove the first line of each module
#

def callback(app, what, name, obj, options, lines):
    if what == 'module':
        # remove empty lines
        while len(lines) and lines[0].strip() == '':
            lines.pop(0)

        # if we still have lines, remove the title
        if len(lines):
            lines.pop(0)

        # if the title is followed by a separator, remove it.
        if len(lines) and lines[0].startswith('=='):
            lines.pop(0)

def setup(app):
    app.connect('autodoc-process-docstring', callback)

