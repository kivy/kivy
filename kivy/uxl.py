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

__all__ = ('Uxl', 'UxlParser')

import re
from copy import copy
from kivy.factory import Factory
from kivy.logger import Logger

trace = Logger.trace

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

        trace('UxlParser: parse %d lines' % len(lines))

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
        trace('UxlParser: uxl version is %s' % version)

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
        trace('UxlParser: load external <%s>' % filename)
        with open(filename, 'r') as fd:
            return fd.read()

def create_handler(element, key, value, idmap):

    # first, remove all the string from the value
    tmp = re.sub('([\'"][^\'"]*[\'"])', '', value)

    # detect key.value inside value
    kw = re.findall('([a-zA-Z0-9_.]+\.[a-zA-Z0-9_.]+)', tmp)
    if not kw:
        # look like no reference, just pass it
        return eval(value)

    # create an handler
    idmap = copy(idmap)
    def call_fn(sender, _value):
        trace('Uxl: call_fn %s, key=%s, value=%s' % (element, key, value))
        trace('Uxl: call_fn => value=%s' % str(eval(value, {}, idmap)))
        setattr(element, key, eval(value, {}, idmap))

    # bind every key.value
    for x in kw:
        k = x.split('.')
        if len(k) != 2:
            continue
        f = idmap[k[0]]
        f.bind(**{k[1]: call_fn})

    return eval(value, {}, idmap)

    # is the value is a string, numeric, tuple, list ?
    if value[0] in ['(', '[', '"', '\'', '-'] + range(9):
        value = eval(value, {}, self.idmap)
    # must be an object.property
    else:
        value = value.split('.', 2)
        if len(value) != 2:
            raise UxlError(ctx, ln, 'Reference format should '
                           'be <id>.<property>')
        # bind
        m = self.idmap[value[0]]
        kw = { value[1]: create_handler(element, key) }
        m.bind(**kw)
        trace('Uxl: bind %s.%s to %s.%s' % (
            m, value[1], element, key))
        value = getattr(self.idmap[value[0]], value[1])
    trace('Uxl: set %s=%s for %s' % (key, value, element))

    return call_fn

class UxlRule(object):
    def __init__(self, key):
        self.key = key.lower()

    def match(self, widget):
        raise NotImplemented()

    def __repr__(self):
        return '<%s key=%s>' % (self.__class__.__name__, self.key)

class UxlRuleId(UxlRule):
    def match(self, widget):
        return widget.id.lower() == self.key

class UxlRuleClass(UxlRule):
    def match(self, widget):
        return self.key in widget.cls

class UxlRuleName(UxlRule):
    def match(self, widget):
        return widget.__class__.__name__.lower() == self.key

class UxlBase(object):
    '''Uxl object are able to load Uxl file or string, return the root object of
    the file, and inject rules in the rules database.
    '''
    def __init__(self):
        super(UxlBase, self).__init__()
        self.rules = []
        self.idmap = {}
        self.idmaps = []

    def add_rule(self, rule, defs):
        trace('Uxl: add rule %s' % str(rule))
        self.rules.append((rule, defs))

    def load_file(self, filename, **kwargs):
        trace('Uxl: load file %s' % filename)
        with open(filename, 'r') as fd:
            return self.load_string(fd.read(), **kwargs)

    def load_string(self, string, rulesonly=False):
        parser = UxlParser(content=string)
        root = self.build(parser.objects)
        if rulesonly and root:
            raise Exception('The file <%s> contain also non-rules '
                            'directives' % filename)

    def match(self, widget):
        '''Return the list of the rules matching the widget
        '''
        matches = []
        for rule, defs in self.rules:
            if rule.match(widget):
                matches.append(defs)
        return matches

    def apply(self, widget):
        '''Apply all the Uxl rules matching the widget on the widget.
        '''
        matches = self.match(widget)
        trace('Uxl: Found %d matches for %s' % (len(matches), widget))
        if not matches:
            return
        self._push_ids()
        have_root = 'root' in self.idmap
        if not have_root:
            self.idmap['root'] = widget
        for defs in matches:
            self.build_item(widget, defs, is_instance=True)
        if not have_root:
            del self.idmap['root']
        self._pop_ids()


    #
    # Private
    #

    def _push_ids(self):
        self.idmaps.append(self.idmap)
        self.idmap = copy(self.idmap)

    def _pop_ids(self):
        self.idmap = self.idmaps.pop()

    def build(self, objects):
        root = None
        for item, params in objects:
            if item.startswith('<'):
                self.build_rule(item, params)
            else:
                if root is not None:
                    raise UxlError(params['__ctx__'], params['__line__'],
                                   'Only one root object is allowed')
                root = self.build_item(item, params)
        return root

    def build_item(self, item, params, is_instance=False):
        self._push_ids()

        if is_instance is False:
            trace('Uxl: build item %s' % item)
            if item.startswith('<'):
                raise UxlError(params['__ctx__'], params['__line__'],
                               'Rules are not accepted inside Widget')
            widget = Factory.get(item)()
        else:
            widget = item
        self.idmap['self'] = widget

        # first loop, do attributes
        for key, value in params.iteritems():
            if key in ('__line__', '__ctx__'):
                continue
            value, ln, ctx = value
            if key == 'children':
                children = []
                for citem, cparams, in value:
                    child = self.build_item(citem, cparams)
                    children.append(child)
                widget.children = children
            elif key == 'canvas':
                pass
            else:
                try:
                    value = create_handler(widget, key, value, self.idmap)
                    trace('Uxl: set %s=%s for %s' % (key, value, widget))
                    setattr(widget, key, value)
                except Exception, e:
                    m = UxlError(ctx, ln, str(e))
                    print m
                    raise

        # second loop, only for canvas
        for key, value in params.iteritems():
            if key != 'canvas':
                continue
            value, ln, ctx = value
            with widget.canvas:
                self.build_canvas(item, value)

        self._pop_ids()
        return widget

    def build_canvas(self, item, elements):
        trace('Uxl: build canvas for %s' % item)
        for name, params in elements:
            element = Factory.get(name)()
            for key, value in params.iteritems():
                if key in ('__line__', '__ctx__'):
                    continue
                value, ln, ctx = value
                try:
                    value = create_handler(element, key, value, self.idmap)
                    trace('Uxl: set %s=%s for %s' % (key, value, element))
                    setattr(element, key, value)
                except Exception, e:
                    m = UxlError(ctx, ln, str(e))
                    print m.message
                    raise

    def build_rule(self, item, params):
        trace('Uxl: build rule for %s' % item)
        if item[0] != '<' or item[-1] != '>':
            raise UxlError(params['__ctx__'], params['__line__'],
                           'Invalid rule (must be inside <>)')
        rules = item[1:-1].split(',')
        for rule in rules:
            if not len(rule):
                raise UxlError(params['__ctx__'], params['__line__'],
                               'Empty rule detected')
            crule = None
            if rule[0] == '.':
                crule = UxlRuleClass(rule[1:])
            elif rule[0] == '#':
                crule = UxlRuleId(rule[1:])
            else:
                crule = UxlRuleName(rule)
            self.add_rule(crule, params)


#: Rules instance, can be use for asking if we are matching a rule or not
Uxl = UxlBase()
Uxl.load_file('kivy/data/style.uxl', rulesonly=True)

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
