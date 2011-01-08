'''
Kivy language
=============

One level = 4 spaces. No more, no less. Tab not allowed.

Example of Kivy files ::

    #:kivy 1.0

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

__all__ = ('Builder', 'Parser')

import re
from os.path import join
from copy import copy
from kivy.factory import Factory
from kivy.logger import Logger
from kivy.utils import OrderedDict, curry
from kivy import kivy_data_dir

trace = Logger.trace

class ParserError(Exception):
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

        message = 'Parser: File "%s", line %d:\n%s\n%s' % (
            self.filename, self.line, sc, message)
        super(ParserError, self).__init__(message)


class Parser(object):
    '''Create an Parser object to parse a Kivy file or Kivy content.
    '''

    CLASS_RANGE = range(ord('A'), ord('Z') + 1)

    def __init__(self, **kwargs):
        super(Parser, self).__init__()
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
        '''Parse the content of a Parser file, and return a list
        of root objects.
        '''
        # Read and parse the lines of the file
        lines = content.splitlines()
        if not lines:
            return
        lines = zip(range(len(lines)), lines)
        self.sourcecode = lines[:]

        trace('Parser: parse %d lines' % len(lines))

        # Ensure the version
        if self.filename:
            self.parse_version(lines[0])

        # Strip all comments
        self.strip_comments(lines)

        # Get object from the first level
        objects, lines = self.parse_level(0, lines)

        if len(lines):
            ln, content = lines[0]
            raise ParserError(self, ln, 'Invalid data (not parsed)')

        self.objects = objects


    def parse_version(self, line):
        '''Parse the version line.
        The version line is always #:kivy <version>
        '''

        ln, content = line

        if not content.startswith('#:kivy '):
            raise ParserError(self, ln,
                           'Invalid doctype, must start with '
                           '#:kivy <version>')

        version = content[6:].strip()
        if version != '1.0':
            raise ParserError(self, ln, 'Only Kivy 1.0 are supported'
                          ' (<%s> found)' % version)
        trace('Parser: Kivy version is %s' % version)

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
                raise ParserError(self, ln,
                               'Invalid indentation, must be a multiple of 4')
            content = content.strip()

            # Level finished
            if count < indent:
                return objects, lines[i-1:]

            # Current level, create an object
            elif count == indent:
                current_object = OrderedDict()
                current_object['__line__'] = ln
                current_object['__ctx__'] = self
                current_property = None
                x = content.split(':', 2)
                if not len(x[0]):
                    raise ParserError(self, ln, 'Identifier missing')
                if len(x) == 2 and len(x[1]):
                    raise ParserError(self, ln, 'Invalid data after declaration')
                objects.append((x[0], current_object))

            # Next level, is it a property or an object ?
            elif count == indent + 4:
                x = content.split(':', 2)
                if not len(x[0]):
                    raise ParserError(self, ln, 'Identifier missing')

                # It's a class, add to the current object as a children
                current_property = None
                name = x[0]
                if ord(name[0]) in Parser.CLASS_RANGE or name[0] == '+':
                    _objects, _lines = self.parse_level(level + 1, lines[i:])
                    current_object['children'] = (_objects, ln, self)
                    lines = _lines
                    i = 0

                # It's a property
                else:
                    if len(x) == 1:
                        raise ParserError(self, ln, 'Syntax error')
                    value = x[1].strip()
                    if len(value):
                        current_object[name] = (value, ln, self)
                    else:
                        current_property = name

            # Two more level ?
            elif count == indent + 8:
                if current_property not in ('canvas', 'canvas.after',
                                            'canvas.before'):
                    raise ParserError(self, ln,
                                   'Invalid indentation, only allowed '
                                   'for canvas')
                _objects, _lines = self.parse_level(level + 2, lines[i:])
                current_object[current_property] = (_objects, ln, self)
                current_property = None
                lines = _lines
                i = 0

            # Too much indent, invalid
            else:
                raise ParserError(self, ln,
                               'Invalid indentation (too much level)')

            # Check the next line
            i += 1

        return objects, []

    def load_resource(self, filename):
        '''Load an external resource
        '''
        trace('Parser: load external <%s>' % filename)
        with open(filename, 'r') as fd:
            return fd.read()

#
# Utilities for eval()
#
_eval_globals = {}
def _eval_center(boxsize, center):
    return center[0] - boxsize[0] / 2., center[1] - boxsize[1] / 2.
_eval_globals['center'] = _eval_center

def custom_callback(*largs, **kwargs):
    element, key, value, idmap = largs[0]
    locals().update(idmap)
    exec value

def create_handler(element, key, value, idmap):

    # first, remove all the string from the value
    tmp = re.sub('([\'"][^\'"]*[\'"])', '', value)

    # detect key.value inside value
    kw = re.findall('([a-zA-Z0-9_.]+\.[a-zA-Z0-9_.]+)', tmp)
    if not kw:
        # look like no reference, just pass it
        return eval(value, _eval_globals)

    # create an handler
    idmap = copy(idmap)
    def call_fn(sender, _value):
        trace('Builder: call_fn %s, key=%s, value=%s' % (element, key, value))
        e_value = eval(value, _eval_globals, idmap)
        trace('Builder: call_fn => value=%s' % str(e_value))
        setattr(element, key, e_value)

    # bind every key.value
    for x in kw:
        k = x.split('.')
        if len(k) != 2:
            continue
        f = idmap[k[0]]
        f.bind(**{k[1]: call_fn})

    return eval(value, _eval_globals, idmap)

class BuilderRule(object):
    def __init__(self, key):
        self.key = key.lower()

    def match(self, widget):
        raise NotImplemented()

    def __repr__(self):
        return '<%s key=%s>' % (self.__class__.__name__, self.key)

class BuilderRuleId(BuilderRule):
    def match(self, widget):
        return widget.id.lower() == self.key

class BuilderRuleClass(BuilderRule):
    def match(self, widget):
        return self.key in widget.cls

class BuilderRuleName(BuilderRule):
    def match(self, widget):
        return widget.__class__.__name__.lower() == self.key

class BuilderBase(object):
    '''Kv object are able to load Kv file or string, return the root object of
    the file, and inject rules in the rules database.
    '''
    def __init__(self):
        super(BuilderBase, self).__init__()
        self.rules = []
        self.idmap = {}
        self.gidmap = {}
        self.idmaps = []

        # List of all the setattr needed to be done after creating the tree
        self.listset = []
        # List of all widget created during the tree, and then apply the style
        # for each of them.
        self.listwidget = []

    def add_rule(self, rule, defs):
        trace('Builder: add rule %s' % str(rule))
        self.rules.append((rule, defs))

    def load_file(self, filename, **kwargs):
        trace('Builder: load file %s' % filename)
        with open(filename, 'r') as fd:
            return self.load_string(fd.read(), **kwargs)

    def load_string(self, string, rulesonly=False):
        parser = Parser(content=string)
        root = self.build(parser.objects)
        if rulesonly and root:
            raise Exception('The file <%s> contain also non-rules '
                            'directives' % filename)
        return root

    def match(self, widget):
        '''Return the list of the rules matching the widget
        '''
        matches = []
        for rule, defs in self.rules:
            if rule.match(widget):
                matches.append(defs)
        return matches

    def apply(self, widget):
        '''Apply all the Kivy rules matching the widget on the widget.
        '''
        matches = self.match(widget)
        trace('Builder: Found %d matches for %s' % (len(matches), widget))
        if not matches:
            return
        #self._push_ids()
        have_root = 'root' in self.idmap
        if not have_root:
            self.idmap['root'] = widget
        for defs in matches:
            self.build_item(widget, defs, is_template=True)
        if not have_root:
            del self.idmap['root']
        #self._pop_ids()


    #
    # Private
    #

    def _push_ids(self):
        self.idmaps.append(self.idmap)
        self.idmap = copy(self.idmap)

    def _pop_ids(self):
        self.idmap = self.idmaps.pop()

    def build(self, objects):
        self.idmap = {}
        root = None
        for item, params in objects:
            if item.startswith('<'):
                self.build_rule(item, params)
            else:
                if root is not None:
                    raise ParserError(params['__ctx__'], params['__line__'],
                                   'Only one root object is allowed')
                root = self.build_item(item, params)
                self.build_attributes()
                self.apply(root)
        return root

    def _iterate(self, params):
        for key, value in params.iteritems():
            if key in ('__line__', '__ctx__'):
                continue
            yield key, value

    def build_item(self, item, params, is_template=False):
        self._push_ids()

        if is_template is False:
            trace('Builder: build item %s' % item)
            if item.startswith('<'):
                raise ParserError(params['__ctx__'], params['__line__'],
                               'Rules are not accepted inside Widget')
            no_apply = False
            if item.startswith('+'):
                item = item[1:]
                no_apply = True
            widget = Factory.get(item)(__no_builder=True)
            if not no_apply:
                self.listwidget.append(widget)
        else:
            widget = item
        self.idmap['self'] = widget

        # first loop, create unknown attribute
        for key, value in self._iterate(params):
            value, ln, ctx = value
            if hasattr(widget, key):
                continue
            widget.create_property(key)

        # second loop, create the tree + canvas
        for key, value in self._iterate(params):
            value, ln, ctx = value
            if key == 'children':
                for citem, cparams, in value:
                    child = self.build_item(citem, cparams)
                    widget.add_widget(child)
            elif key == 'canvas':
                with widget.canvas:
                    self.build_canvas(widget.canvas, item, value)
            elif key == 'canvas.before':
                with widget.canvas.before:
                    self.build_canvas(widget.canvas.before, item, value)
            elif key == 'canvas.after':
                with widget.canvas.after:
                    self.build_canvas(widget.canvas.after, item, value)
            elif key == 'id':
                self.gidmap[value] = widget
            else:
                self.listset.append((ctx, ln, widget, key, value, copy(self.idmap)))

        self._pop_ids()
        if is_template:
            self.build_attributes()
        return widget

    def build_attributes(self):
        # third loop, assign all attributes
        for x in self.listset:
            ctx, ln, widget, key, value, idmap = x
            try:
                idmap.update(self.gidmap)
                self.build_handler(widget, key, value, idmap, True)
            except Exception, e:
                m = ParserError(ctx, ln, str(e))
                print m
                raise
        self.listset = []
        self.gidmap = {}

        # last loop, apply style
        listwidget = self.listwidget[:]
        self.listwidget = []
        for widget in listwidget:
            self.apply(widget)

    def build_handler(self, element, key, value, idmap, is_widget):
        if key.startswith('on_'):
            element.bind(**{key:curry(custom_callback, (element, key, value, idmap))})

        else:
            value = create_handler(element, key, value, idmap)
            trace('Builder: set %s=%s for %s' % (key, value, element))
            if is_widget and not hasattr(element, key):
                    element.create_property(key)
            setattr(element, key, value)

    def build_canvas(self, canvas, item, elements):
        trace('Builder: build canvas for %s' % item)
        for name, params in elements:
            if name == 'Clear':
                canvas.clear()
                continue
            element = Factory.get(name)()
            for key, value in params.iteritems():
                if key in ('__line__', '__ctx__'):
                    continue
                value, ln, ctx = value
                try:
                    self.build_handler(element, key, value, self.idmap, False)
                except Exception, e:
                    m = ParserError(ctx, ln, str(e))
                    print m.message
                    raise

    def build_rule(self, item, params):
        trace('Builder: build rule for %s' % item)
        if item[0] != '<' or item[-1] != '>':
            raise ParserError(params['__ctx__'], params['__line__'],
                           'Invalid rule (must be inside <>)')
        rules = item[1:-1].split(',')
        for rule in rules:
            if not len(rule):
                raise ParserError(params['__ctx__'], params['__line__'],
                               'Empty rule detected')
            crule = None
            if rule[0] == '.':
                crule = BuilderRuleClass(rule[1:])
            elif rule[0] == '#':
                crule = BuilderRuleId(rule[1:])
            else:
                crule = BuilderRuleName(rule)
            self.add_rule(crule, params)


#: Rules instance, can be use for asking if we are matching a rule or not
Builder = BuilderBase()
Builder.load_file(join(kivy_data_dir, 'style.kv'), rulesonly=True)

if __name__ == '__main__':
    content = '''#:Kv 1.0

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

    Builder.load(content=content)
