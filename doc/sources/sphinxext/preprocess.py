'''
Extension for enhancing sphinx documentation generation for cython module
'''

import re
import types
import sys
from os.path import dirname, join
from sphinx.ext.autodoc import MethodDocumenter

class CythonMethodDocumenter(MethodDocumenter):
    # XXX i don't understand the impact of having a priority more than the
    # attribute or instance method but the things is, if it's a cython module,
    # the attribute will be prefer over method.
    priority = 12

def is_cython_extension(what, obj):
    # try to check if the first line of the doc is a signature
    doc = obj.__doc__
    if not doc:
        return False
    doc = doc.split('\n')
    if not len(doc):
        return False
    doc = doc[0]

    # test for cython cpdef
    if what in ('attribute', 'method') and hasattr(obj, '__objclass__'):
        if not re.match('^([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)', doc):
            return False
        return True
    # test for cython class
    if what == 'class' and hasattr(obj, '__pyx_vtable__'):
        if not re.match('^([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)', doc):
            return False
        return True
    # test for python method in cython class
    if what in ('method', 'function') and obj.__class__ == types.BuiltinFunctionType:
        if not re.match('^([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)', doc):
            return False
        return True

def callback_docstring(app, what, name, obj, options, lines):
    if what == 'module':
        # remove empty lines
        while len(lines):
            line = lines[0].strip()
            if not line.startswith('.. _') and line != '':
                break
            lines.pop(0)

        # if we still have lines, remove the title
        if len(lines):
            lines.pop(0)

        # if the title is followed by a separator, remove it.
        if len(lines) and lines[0].startswith('=='):
            lines.pop(0)

    elif is_cython_extension(what, obj) and lines:
        if what == 'class':
            lines.pop(0)
        line = lines.pop(0)

        # trick to realign the first line to the second one.
        # FIXME: fail if we finishing with::
        line_with_text = [x for x in lines if len(x.strip())]
        if len(line_with_text) and line is not None and len(lines):
            l = len(line_with_text[0]) - len(line_with_text[0].lstrip())
        else:
            l = 0
        lines.insert(0, ' ' * l + line)

        # calculate the minimum space available
        min_space = 999
        for line in lines:
            if not line.strip():
                continue
            min_space = min(min_space, len(line) - len(line.lstrip()))

        # remove that kind of space now.
        if min_space > 0:
            spaces = ' ' * min_space
            for idx, line in enumerate(lines):
                if not line.strip():
                    continue
                if not line.startswith(spaces):
                    continue
                lines[idx] = line[min_space:]

def callback_signature(app, what, name, obj, options, signature,
                       return_annotation):
    # remove the first 'self' argument, because python autodoc don't
    # add it for python method class. So do the same for cython class.
    if is_cython_extension(what, obj):
        try:
            doc = obj.__doc__.split('\n').pop(0)
            doc = '(%s' % doc.split('(')[1]
            doc = doc.replace('(self, ', '(')
            doc = doc.replace('(self)', '( )')
            return (doc, None)
        except AttributeError:
            pass
        except IndexError:
            pass

def setup(app):
    import kivy
    sys.path += [join(dirname(kivy.__file__), 'extras')]
    from highlight import KivyLexer

    app.add_lexer('kv', KivyLexer())
    app.add_autodocumenter(CythonMethodDocumenter)
    app.connect('autodoc-process-docstring', callback_docstring)
    app.connect('autodoc-process-signature', callback_signature)
