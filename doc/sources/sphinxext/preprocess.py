'''
Extension for enhancing sphinx documentation generation for cython module
'''

def is_cython_extension(what, obj):
    # try to check if the first line of the doc is a signature
    doc = obj.__doc__
    if not doc:
        return False
    doc = doc.split('\n')
    if not len(doc):
        return False
    doc = doc[0]
    if not '(' in doc or doc[-1] != ')':
        return False

    # check more if it's an extension
    if what == 'attribute' and hasattr(obj, '__objclass__') and \
       hasattr(obj.__objclass__, '__pyx_vtable__'):
        return True
    if what == 'class' and hasattr(obj, '__pyx_vtable__'):
        return True

def callback_docstring(app, what, name, obj, options, lines):
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

    elif is_cython_extension(what, obj):
        lines.pop(0)
        for idx in xrange(len(lines)):
            line = lines[idx]
            if line.startswith('    '):
                lines[idx] = line[4:]
        print what, name, lines
        return
        if what == 'class':
            doc = '\n'.join(lines)
            del lines[:]
            lines.extend([doc])

def callback_signature(app, what, name, obj, options, signature,
                       return_annotation):
    if is_cython_extension(what, obj):
        try:
            doc = obj.__doc__.split('\n').pop(0)
            doc = '(%s' % doc.split('(')[1]
            doc = doc.replace('(self, ', '(')
            doc = doc.replace('(self)', '( )')
            return (doc, None)
        except IndexError:
            pass

def setup(app):
    app.connect('autodoc-process-docstring', callback_docstring)
    app.connect('autodoc-process-signature', callback_signature)

