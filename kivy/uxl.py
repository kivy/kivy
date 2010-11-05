'''
Implement the grammar of Uxl language

One level = 4 spaces. No more, no less. Tab not allowed.

Example of Uxl files ::

    #:uxl 1.0

    ColorScheme:
        id: cs
        backgroundcolor: #927836

    Layout:
        pos: 100, 100
        size: 867, 567

        canvas:
            Color:
                rgb: cs.backgroundcolor
            Rectangle:
                pos: self.pos
                size: self.size
'''

from kivy.factory import Factory

class UxlError(Exception):
    def __init__(self, context, line, message):
        self.filename = context.filename or '<inline>'
        self.line = line
        sourcecode = context.sourcecode
        sc_start = max(0, line - 3)
        sc_stop = min(len(sourcecode), line + 3)
        sc = ['...']
        sc += ['   %4d:%s' % x for x in sourcecode[sc_start:line]]
        sc += ['>> %4d:%s' % (line, sourcecode[line][1])]
        sc += ['   %4d:%s' % x for x in sourcecode[line+1:sc_stop]]
        sc += ['...']
        sc = '\n'.join(sc)

        message = 'Uxl: File "%s", line %d:\n%s\n%s' % (
            self.filename, self.line, sc, message)
        super(UxlError, self).__init__(message)


class UxlParser(object):
    '''Create an UxlParser object to parse a Uxl file or Uxl content.
    '''

    CLASS_RANGE = range(ord('A'), ord('Z') + 1)

    def __init__(self, **kwargs):
        super(UxlParser, self).__init__()
        self.sourcecode = []
        self.objects = []
        content = kwargs.get('content', None)
        self.filename = filename = kwargs.get('filename', None)
        if filename:
            content = self.load_resource(filename)
        if content is None:
            raise ValueError('No content passed. Use filename or '
                             'content attribute')
        self.parse(content)


    def parse(self, content):
        '''Parse the content of a UxlParser file, and return a list
        of root objects.
        '''
        # Read and parse the lines of the file
        lines = content.split('\n')
        if not lines:
            return
        lines = zip(range(len(lines)), lines)
        self.sourcecode = lines[:]

        # Ensure the version
        if self.filename:
            self.parse_version(lines[0])

        # Strip all comments
        self.strip_comments(lines)

        # Get object from the first level
        objects, lines = self.parse_level(0, lines)

        if len(lines):
            ln, content = lines[0]
            raise UxlError(self, ln, 'Invalid data (not parsed)')

        self.objects = objects


    def parse_version(self, line):
        '''Parse the version line.
        The version line is always #:uxl <version>
        '''

        ln, content = line

        if not content.startswith('#:uxl '):
            raise UxlError(self, ln,
                           'Invalid doctype, must start with '
                           '#:uxl <version>')

        version = content[6:].strip()
        if version != '1.0':
            raise UxlError(self, ln, 'Only Uxl 1.0 are supported'
                          ' (<%s> found)' % version)

    def strip_comments(self, lines):
        '''Remove all comments from lines inplace.
        '''
        for x in lines[:]:
            if x[1].startswith('#'):
                lines.remove(x)
            if not len(x[1]):
                lines.remove(x)

    def parse_level(self, level, lines):
        '''Parse the current level (level * 4) indentation
        '''
        indent = 4 * level
        objects = []

        current_object = None
        current_property = None
        i = 0
        while i < len(lines):
            line = lines[i]
            ln, content = line

            # Get the number of space
            tmp = content.lstrip(' \t')

            # Replace any tab with 4 spaces
            tmp = content[:len(content)-len(tmp)]
            tmp = tmp.replace('\t', '    ')
            count = len(tmp)

            if count % 4 != 0:
                raise UxlError(self, ln,
                               'Invalid indentation, must be a multiple of 4')
            content = content.strip()

            # Level finished
            if count < indent:
                return objects, lines[i-1:]

            # Current level, create an object
            elif count == indent:
                current_object = {'__line__': ln, '__ctx__': self}
                current_property = None
                x = content.split(':', 2)
                if not len(x[0]):
                    raise UxlError(self, ln, 'Identifier missing')
                if len(x) == 2 and len(x[1]):
                    raise UxlError(self, ln, 'Invalid data after declaration')
                objects.append((x[0], current_object))

            # Next level, is it a property or an object ?
            elif count == indent + 4:
                x = content.split(':', 2)
                if not len(x[0]):
                    raise UxlError(self, ln, 'Identifier missing')

                # It's a class, add to the current object as a children
                current_property = None
                name = x[0]
                if ord(name[0]) in UxlParser.CLASS_RANGE:
                    _objects, _lines = self.parse_level(level + 1, lines[i:])
                    current_object['children'] = (_objects, ln, self)
                    lines = _lines
                    i = 0

                # It's a property
                else:
                    if name == 'children':
                        raise UxlError(self, ln,
                                       '<children> usage is forbidden')

                    if len(x) == 1:
                        raise UxlError(self, ln, 'Syntax error')
                    value = x[1].strip()
                    if len(value):
                        current_object[name] = (value, ln, self)
                    else:
                        current_property = name

            # Two more level ?
            elif count == indent + 8:
                if current_property not in ('canvas', ):
                    raise UxlError(self, ln,
                                   'Invalid indentation, only allowed '
                                   'for canvas')
                _objects, _lines = self.parse_level(level + 2, lines[i:])
                current_object[current_property] = (_objects, ln, self)
                current_property = None
                lines = _lines
                i = 0

            # Too much indent, invalid
            else:
                raise UxlError(self, ln,
                               'Invalid indentation (too much level)')

            # Check the next line
            i += 1

        return objects, []

    def load_resource(self, filename):
        '''Load an external resource
        '''
        with open(filename, 'r') as fd:
            return fd.read()

def create_handler(element, key):
    def call_fn(sender, value):
        setattr(element, key, value)
    return call_fn


class UxlBuilder(object):
    def __init__(self, **kwargs):
        super(UxlBuilder, self).__init__()
        self.idmap = {}
        self.root = None
        self.rules = []
        self.parser = UxlParser(**kwargs)
        self.build(self.parser.objects)

    def build(self, objects):
        for item, params in objects:
            if item.startswith('<'):
                self.build_rule(item, params)
            else:
                if self.root is not None:
                    raise UxlError(params['__ctx__'], params['__line__'],
                                   'Only one root object is allowed')
                self.root = self.build_item(item, params)

    def build_item(self, item, params):
        if item.startswith('<'):
            raise UxlError(params['__ctx__'], params['__line__'],
                           'Rules are not accepted inside Widget')
        widget = Factory.get(item)()
        self.idmap['self'] = widget
        for key, value in params.iteritems():
            if key in ('__line__', '__ctx__'):
                continue
            value, ln, ctx = value
            if key == 'canvas':
                with widget.canvas:
                    self.build_canvas(item, value)
            elif key == 'children':
                children = []
                for citem, cparams, in value:
                    child = self.build_item(citem, cparams)
                    children.append(child)
                widget.children = children
            else:
                try:
                    value = eval(value)
                    setattr(widget, key, value)
                except Exception, e:
                    raise UxlError(ctx, ln, str(e))
        return widget

    def build_canvas(self, item, elements):
        for name, params in elements:
            element = Factory.get(name)()
            for key, value in params.iteritems():
                if key in ('__line__', '__ctx__'):
                    continue
                value, ln, ctx = value
                try:
                    # is the value is a string, numeric, tuple, list ?
                    if value[0] in ('(', '[', '"', '\''):
                        value = eval(value)
                    # must be an object.property
                    else:
                        value = value.split('.')
                        if len(value) != 2:
                            raise UxlError(ctx, ln, 'Reference format should '
                                           'be <id>.<property>')
                        # bind
                        m = self.idmap[value[0]]
                        kw = { value[1]: create_handler(element, key) }
                        m.bind(**kw)
                        value = getattr(self.idmap[value[0]], value[1])
                    setattr(element, key, value)
                except Exception, e:
                    raise
                    raise UxlError(ctx, ln, str(e))
            print element

    def build_rule(self, item, params):
        pass


# XXX FIXME move this into graphics
Factory.register('Rectangle', module='kivy.graphics')
Factory.register('Color', module='kivy.graphics')


if __name__ == '__main__':
    uxl_content = '''#:uxl 1.0

ColorScheme:
    id: cs
    backgroundcolor: #927836

Layout:
    pos: 100, 100
    size: 867, 567

    canvas:
        Color:
            rgb: cs.backgroundcolor
        Rectangle:
            pos: self.pos
            size: self.size
'''

    Uxl(content=uxl_content)
