'''
Kivy language
=============

Kivy language is a language dedicated for describing user interface and
interactions. You could compare this language to QML of Qt
(http://qt.nokia.com), but we are including new concept like the rules
definitions, templating and so on.

Overview
--------

The language permit you to create:

    Rule
        The rule is like CSS rules. You create a rule to match a specific class
        or widget in your tree. You can automatically create interactions or
        adding graphicals instructions to a specific widget (like all the
        widgets with the attribute cls=test).

    Root widget
        You can use the language to create your user interface. A kv file can
        contain only one root widget.

    Template
        This will be used to create part of your application, like the list
        content. If you want to design the look of an entry in a list (icon in
        the left, text in the right), you will use Template for that.

        For the moment, templating are not yet designed in the language, we are
        still working on it. Check the issue #17
        (https://github.com/tito/kivy/issues#issue/17)


Syntax of a kv file
-------------------

A kivy language file must be ended by the .kv extension.

The content of the file must always start with the kivy header, where `version`
must be replaced with the kivy language version you're using. For now, use
1.0::

    #:kivy `version`

    `content`

The `content` can contain rules, root widget and template::

    # syntax of a rule
    <Rule1,Rule2>:
        .. definitions ..

    <Rule3>:
        .. definitions ..

    # syntax for creating a root widget
    RootClassName:
        .. definitions ..

Whatever is it's an rule, root widget or template, the definition should look
like this::

    <ClassName>:
        prop1: value1
        prop2: value2

        canvas:
            CanvasInstruction1:
                canvasprop1: value1
            CanvasInstruction2:
                canvasprop2: value2

        AnotherClass:
            prop3: value1

`prop1` and `prop2` are the properties of `ClassName` and `prop3` is the
property of `AnotherClass`. If the property doesn't exist in the class, an
:class:`~kivy.properties.ObjectProperty` will be automatically created and added
to the instance.

`AnotherClass` will be created and added as a child of `ClassName` instance.

- The indentation is important, and must be 4 spaces. Tabs are not allowed.
- The value of a property must be single line. (we may change this in a future
version.)
- The `canvas` property is special: you can put graphics class inside it to
create your graphical representation of the current class.


Here is an example of a kv file that contain a root widget::

    #:kivy 1.0

    Button:
        text: 'Hello world'


Value expression and reserved keyword
-------------------------------------

The value is a python expression. This expression can be static or dynamic,
that's mean the value can use the values of other properties using reserved
keywords.

    self
        The keyword self reference the "current widget instance"::

            Button:
                text: 'My state is %s' % self.state

    root
        This keyword is available only in rules definition, and represent the
        root widget of the rule (the first instance of the rule)::

            <Widget>:
                custom: 'Hello world'
                Button:
                    text: root.custom

Also, if a class definition contain an id, you can use it as a keyword::

    <Widget>:
        Button:
            id: 'btn1'
        Button:
            text: 'The state of btn1 is %s' % btn1.state

Please note that the id will be not available in the Widget instance: the `id`
attribute will be not used.



Relation between values and properties
--------------------------------------

When you use kv language, we are doing magical stuff to automatically get things
work. You must know that :doc:`api-kivy.properties` implement the observer
pattern: you can bind your own function to be called when the value of a
property change.

Kv language detect properties in your `value`, and create callback to
automatically update the property from your expression.

Simple example of using a property::

    Button:
        text: str(self.state)

In this example, we are detecting `self.state` as a dynamic value. Since the
:data:`~kivy.uix.button.Button.state` of the button can change at every moment,
we are binding this value expression to the state property of the Button.
Everytime the button state changed, the text property will be updated.

Since the value is a python expression, you could do something more interesting
like::

    Button:
        text: 'Plop world' if self.state == 'normal' else 'Release me!'

The Button text change with the state of the button. By default, the button text
will be 'Plop world', and when the button is pressed, the text will change to
'Release me!'


Graphical instructions
----------------------

The graphical instructions is a special part of the kv language. This concern
the 'canvas' property definition::

    Widget:
        canvas:
            Color:
                rgb: (1, 1, 1)
            Rectangle:
                size: self.size
                pos: self.pos

All the classes added inside the canvas property are inherith from the
:class:`~kivy.graphics.Instruction` class. You cannot put any Widget class
inside the canvas property.

If you want to do theming, you'll have the same problem as CSS: you don't know
which rule have been executed before. For our case, the rule are executed in
processing order.

If you want to change of a Button is rendered, you can create your own kv, and
put something like this::

    <Button>
        canvas:
            Color:
                rgb: (1, 0, 0)
            Rectangle:
                pos: self.pos
                size: self.size
            Rectangle:
                pos: self.pos
                size: self.texture_size
                texture: self.texture

It will result a button with a red background, and the label texture in the
bottom left.... in addition to all the precedent rules.
You can clear all the previous instructions by using the `Clear` command::

    <Button>
        canvas:
            Clear
            Color:
                rgb: (1, 0, 0)
            Rectangle:
                pos: self.pos
                size: self.size
            Rectangle:
                pos: self.pos
                size: self.texture_size
                texture: self.texture

Then, only your rules will be taken.

'''

__all__ = ('Builder', 'BuilderBase', 'Parser')

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
    '''Create a Parser object to parse a Kivy file or Kivy content.
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
        num_lines = len(lines)
        lines = zip(range(num_lines), lines)
        self.sourcecode = lines[:]

        trace('Parser: parsing %d lines' % num_lines)

        # Ensure the version
        if self.filename:
            self.parse_version(lines[0])

        # Strip all comments
        self.strip_comments(lines)

        # Get object from the first level
        objects, remaining_lines = self.parse_level(0, lines)

        # After parsing, there should be no remaining lines
        # or there's an error we did not catch earlier.
        if remaining_lines:
            ln, content = remaining_lines[0]
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
           Comments need to be on a single line and not at the end of a line.
           I.e., a line's first non-whitespace character needs to be a #.
        '''
        for ln, line in lines[:]:
            stripped = line.strip()
            if stripped.startswith('#'):
                lines.remove((ln, line))
            if not stripped:
                lines.remove((ln, line))

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
                x = content.split(':', 1)
                if not len(x[0]):
                    raise ParserError(self, ln, 'Identifier missing')
                if len(x) == 2 and len(x[1]):
                    raise ParserError(self, ln,
                                        'Invalid data after declaration')
                objects.append((x[0], current_object))

            # Next level, is it a property or an object ?
            elif count == indent + 4:
                x = content.split(':', 1)
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
    kw = re.findall('([a-zA-Z_][a-zA-Z0-9_.]*\.[a-zA-Z0-9_.]+)', tmp)
    if not kw:
        # look like no reference, just pass it
        return eval(value, _eval_globals)

    # create an handler
    idmap = copy(idmap)

    c_value = compile(value, '<string>', 'eval')

    def call_fn(sender, _value):
        #trace('Builder: call_fn %s, key=%s, value=%s' % (element, key, value))
        e_value = eval(c_value, _eval_globals, idmap)
        #trace('Builder: call_fn => value=%s' % str(e_value))
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

    parents = {}

    def match(self, widget):
        parents = BuilderRuleName.parents
        cls = widget.__class__
        if not cls in parents:
            classes = []
            parent = [cls]
            while parent and len(parent):
                classes.append(parent[0].__name__.lower())
                if parent[0].__name__ == 'Widget':
                    break
                parent = parent[0].__bases__
            parents[cls] = classes
        return self.key in parents[cls]


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
        '''Insert a file into the Language Builder

        :parameters:
            `rulesonly`: bool, default to False
                If True, the Builder will raise an exception if you have a root
                widget inside the definition
        '''
        trace('Builder: load file %s' % filename)
        with open(filename, 'r') as fd:
            kwargs['filename'] = filename
            return self.load_string(fd.read(), **kwargs)

    def load_string(self, string, **kwargs):
        '''Insert a string into the Language Builder

        :parameters:
            `rulesonly`: bool, default to False
                If True, the Builder will raise an exception if you have a root
                widget inside the definition
        '''
        kwargs.setdefault('rulesonly', False)
        parser = Parser(content=string)
        root = self.build(parser.objects)
        if kwargs['rulesonly'] and root:
            filename = kwargs.get('rulesonly', '<string>')
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
                self.listset.append((ctx, ln, widget, key, value,
                                        copy(self.idmap)))

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
            self._push_ids()
            self.idmap['root'] = widget
            self.apply(widget)
            self._pop_ids()

    def build_handler(self, element, key, value, idmap, is_widget):
        if key.startswith('on_'):
            element.bind(**{key: curry(custom_callback, (
                element, key, value, idmap))})

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


#: Main instance of a :class:`BuilderBase`.
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
