'''
Kivy Language
=============

The Kivy language is a language dedicated to describing user interface and
interactions. You could compare this language to Qt's QML
(http://qt.nokia.com), but we included new concepts such as rule definitions
(which are somewhat akin to what you may know from CSS), templating and so on.


Overview
--------

The language consists of several constructs that you can use:

    Rules
        A rule is similar to a CSS rule. A rule applies to specific widgets (or
        classes thereof) in your widget tree and modifies them in a certain way.
        You can use rules to specify interactive behaviour or use them to add
        graphical representations of the widgets they apply to.
        You can target a specific class of widgets (similar to CSS' concept of a
        *class*) by using the ``cls`` attribute (e.g. ``cls=MyTestWidget``).

    A Root Widget
        You can use the language to create your entire user interface.
        A kv file must contain only one root widget at most.

    Templates
        .. versionadded:: 1.0.5

        Templates will be used to populate parts of your application, such as a
        list's content. If you want to design the look of an entry in a list
        (icon on the left, text on the right), you will use a template for that.

        For the moment, templating is not yet designed in the language; we are
        working on it. We track the progress of the implementation in issue #17
        (https://github.com/tito/kivy/issues#issue/17).


Syntax of a kv File
-------------------

A Kivy language file must have ``.kv`` as filename extension.

The content of the file must always start with the Kivy header, where `version`
must be replaced with the Kivy language version you're using. For now, use
1.0::

    #:kivy `version`

    `content`

The `content` can contain rule definitions, a root widget and templates::

    # Syntax of a rule definition. Note that several Rules can share the same
    # definition (as in CSS). Note the braces; They are part of the definition.
    <Rule1,Rule2>:
        .. definitions ..

    <Rule3>:
        .. definitions ..

    # Syntax for creating a root widget
    RootClassName:
        .. definitions ..

    # Syntax for create a template
    [TemplateName@BaseClass1,BaseClass2]:
        .. definitions ..

Regardless of whether it's a rule, root widget or template you're defining,
the definition should look like this::

    # With the braces it's a rule; Without them it's a root widget.
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

Here `prop1` and `prop2` are the properties of `ClassName` and `prop3` is the
property of `AnotherClass`. If the widget doesn't have a property with the given
name, an :class:`~kivy.properties.ObjectProperty` will be automatically created
and added to the instance.

`AnotherClass` will be created and added as a child of the `ClassName` instance.

- The indentation is important, and must be 4 spaces. Tabs are not allowed.
- The value of a property must be given on a single line (for now at least).
- The `canvas` property is special: You can put graphics instructions in it
  to create a graphical representation of the current class.


Here is a simple example of a kv file that contains a root widget::

    #:kivy 1.0

    Button:
        text: 'Hello world'


Value Expressions and Reserved Keywords
---------------------------------------

When you specify a property's value, the value is evaluated as a python
expression. This expression can be static or dynamic, which means that
the value can use the values of other properties using reserved keywords.

    self
        The keyword self references the "current widget instance"::

            Button:
                text: 'My state is %s' % self.state

    root
        This keyword is available only in rule definitions, and represents the
        root widget of the rule (the first instance of the rule)::

            <Widget>:
                custom: 'Hello world'
                Button:
                    text: root.custom

Furthermore, if a class definition contains an id, you can use it as a keyword::

    <Widget>:
        Button:
            id: 'btn1'
        Button:
            text: 'The state of the other button is %s' % btn1.state

Please note that the `id` will not be available in the widget instance; The `id`
attribute will be not used.


Relation Between Values and Properties
--------------------------------------

When you use the Kivy language, you might notice that we do some work behind the
scenes to automatically make things work properly. You should know that
:doc:`api-kivy.properties` implement the *observer* software design pattern:
That means that you can bind your own function to be called when the value of a
property changes (i.e. you passively `observe` the property for potential
changes).

The Kivy language detects properties in your `value` expression and will create
create callbacks to automatically update the property via your expression when
changes occur.

Here's a simple example that demonstrates this behaviour::

    Button:
        text: str(self.state)

In this example, the parser detects that `self.state` is a dynamic value (a
property). The :data:`~kivy.uix.button.Button.state` property of the button
can change at any moment (when the user touches it).
We now want this button to display its own state as text, even as the state
changes. To do this, we use the state property of the Button and use it in the
value expression for the button's `text` property, which controls what text is
displayed on the button (We also convert the state to a string representation).
Now, whenever the button state changes, the text property will be updated
automatically.

Remember: The value is a python expression! That means that you can do something
more interesting like::

    Button:
        text: 'Plop world' if self.state == 'normal' else 'Release me!'

The Button text changes with the state of the button. By default, the button
text will be 'Plop world', but when the button is being pressed, the text will
change to 'Release me!'.


Graphical Instructions
----------------------

The graphical instructions are a special part of the Kivy language. This
concerns the 'canvas' property definition::

    Widget:
        canvas:
            Color:
                rgb: (1, 1, 1)
            Rectangle:
                size: self.size
                pos: self.pos

All the classes added inside the canvas property must be derived from the
:class:`~kivy.graphics.Instruction` class. You cannot put any Widget class
inside the canvas property (as that would not make sense because a widget is not
a graphics instruction).

If you want to do theming, you'll have the same question as in CSS: You don't
know which rules have been executed before. In our case, the rules are executed
in processing order (i.e. top-down).

If you want to change how Buttons are rendered, you can create your own kv file
and put something like this::

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

This will result in buttons having a red background, with the label in the
bottom left, in addition to all the preceding rules.
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

Then, only your rules that follow the `Clear` command will be taken into
consideration.


.. _template_usage:

Templates
---------

.. versionadded:: 1.0.5

Syntax of template
~~~~~~~~~~~~~~~~~~

Using a template in Kivy require 2 things :

    #. a context to pass for the context (will be ctx inside template)
    #. a kv definition of the template

Syntax of a template::

    # With only one base class
    [ClassName@BaseClass]:
        .. definitions ..

    # With more than one base class
    [ClassName@BaseClass1,BaseClass2]:
        .. definitions ..

For example, for a list, you'll need to create a entry with a image on the left,
and a label on the right. You can create a template for making that definition
more easy to use.
So, we'll create a template that require 2 entry in the context: a image
filename and a title ::

    [IconItem@BoxLayout]:
        Image:
            source: ctx.image
        Label:
            text: ctx.title

Then in Python, you can create instanciate the template with ::

    from kivy.lang import Builder

    # create a template with hello world + an image
    icon1 = Builder.template('IconItem', {
        'title': 'Hello world',
        'image': 'myimage.png'})

    # create a second template with another information
    icon2 = Builder.template('IconItem', {
        'title': 'Another hello world',
        'image': 'myimage2.png'})
    # and use icon1 and icon2 as other widget.


Template example
~~~~~~~~~~~~~~~~

Most of time, when you are creating screen into kv lang, you have lot of
redefinition. In our example, we'll create a Toolbar, based on a BoxLayout, and
put many Image that will react to on_touch_down::

    <MyToolbar>:
        BoxLayout:
            Image:
                source: 'data/text.png'
                size: self.texture_size
                size_hint: None, None
                on_touch_down: self.collide_point(*args[1].pos) and\
 root.create_text()

            Image:
                source: 'data/image.png'
                size: self.texture_size
                size_hint: None, None
                on_touch_down: self.collide_point(*args[1].pos) and\
 root.create_image()

            Image:
                source: 'data/video.png'
                size: self.texture_size
                size_hint: None, None
                on_touch_down: self.collide_point(*args[1].pos) and\
 root.create_video()

We can see that the side and size_hint attribute are exactly the same.
More than that, the callback in on_touch_down and the image are changing.
Theses can be the variable part of the template that we can put into a context.
Let's try to create a template for the Image::

    [ToolbarButton@Image]:

        # This is the same as before
        source: 'data/%s.png' % ctx.image
        size: self.texture_size
        size_hint: None, None

        # Now, we are using the ctx for the variable part of the template
        on_touch_down: self.collide_point(*args[1].pos) and self.callback()

The template can be used directly in the MyToolbar rule::

    <MyToolbar>:
        BoxLayout:
            ToolbarButton:
                image: 'text'
                callback: root.create_text
            ToolbarButton:
                image: 'image'
                callback: root.create_image
            ToolbarButton:
                image: 'video'
                callback: root.create_video

That's all :)


Template limitations
~~~~~~~~~~~~~~~~~~~~

When you are creating a context:

    #. you cannot use references other than "root"::

        <MyRule>:
            Widget:
                id: mywidget
                value: 'bleh'
            Template:
                ctxkey: mywidget.value # << fail, this reference mywidget id

    #. all the dynamic part will be not understood::

        <MyRule>:
            Template:
                ctxkey: 'value 1' if root.prop1 else 'value2' # << even if
                # root.prop1 is a property, the context will not update the
                # context

Lang Directives
---------------

You can use directive to control part of the lang files. Directive is done with
a comment line starting with::

    #:<directivename> <options>

import <package>
~~~~~~~~~~~~~~~~

.. versionadded:: 1.0.5

Syntax::

    #:import <alias> <package>

You can import a package by writing::

    #:import os os

    <Rule>:
        Button:
            text: os.getcwd()

Or more complex::

    #:import ut kivy.utils

    <Rule>:
        canvas:
            Color:
                rgba: ut.get_random_color()
'''

__all__ = ('Builder', 'BuilderBase', 'Parser')

import re
import sys
from os.path import join
from copy import copy
from types import ClassType
from functools import partial
from kivy.factory import Factory
from kivy.logger import Logger
from kivy.utils import OrderedDict, QueryDict
from kivy import kivy_data_dir

trace = Logger.trace
global_idmap = {}


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
    '''Create a Parser object to parse a Kivy language file or Kivy content.
    '''

    CLASS_RANGE = range(ord('A'), ord('Z') + 1)

    def __init__(self, **kwargs):
        super(Parser, self).__init__()
        self.sourcecode = []
        self.objects = []
        self.directives = []
        content = kwargs.get('content', None)
        self.filename = filename = kwargs.get('filename', None)
        if filename:
            content = self.load_resource(filename)
        if content is None:
            raise ValueError('No content passed. Use filename or '
                             'content attribute.')
        self.parse(content)

    def execute_directives(self):
        for ln, cmd in self.directives:
            cmd = cmd.strip()
            Logger.trace('Parser: got directive <%s>' % cmd)
            if cmd.startswith('kivy '):
                # FIXME move the version checking here
                continue
            elif cmd.startswith('import '):
                package = cmd[7:].strip()
                l = package.split(' ')
                if len(l) != 2:
                    raise ParserError(self, ln, 'Invalid import syntax')
                alias, package = l
                try:
                    if package not in sys.modules:
                        mod = __import__(package)
                    else:
                        mod = sys.modules[package]
                    global_idmap[alias] = mod
                except ImportError:
                    Logger.exception('')
                    raise ParserError(self, ln, 'Unable to import package %r' %
                                     package)
            else:
                raise ParserError(self, ln, 'Unknown directive')

    def parse(self, content):
        '''Parse the contents of a Parser file and return a list
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

        # Execute directives
        self.execute_directives()

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
        The version line is always the first line, unindented and has the
        format: #:kivy <version>
        '''
        ln, content = line

        if not content.startswith('#:kivy '):
            raise ParserError(self, ln,
                           'Invalid doctype, must start with '
                           '#:kivy <version>')

        version = content[6:].strip()
        if version != '1.0':
            raise ParserError(self, ln, 'Only Kivy language 1.0 is supported'
                          ' (<%s> found)' % version)
        trace('Parser: Kivy version is %s' % version)

    def strip_comments(self, lines):
        '''Remove all comments from all lines in-place.
           Comments need to be on a single line and not at the end of a line.
           I.e., a comment line's first non-whitespace character must be a #.
        '''
        for ln, line in lines[:]:
            stripped = line.strip()
            if stripped.startswith('#:'):
                self.directives.append((ln, stripped[2:]))
            if stripped.startswith('#'):
                lines.remove((ln, line))
            if not stripped:
                lines.remove((ln, line))

    def parse_level(self, level, lines):
        '''Parse the current level (level * 4) indentation.
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
                               'Invalid indentation, '
                               'must be a multiple of 4 spaces')
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

            # Two more levels?
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

            # Too much indentation, invalid
            else:
                raise ParserError(self, ln,
                               'Invalid indentation (too many levels)')

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
    args = largs[1:]
    exec value


def create_handler(element, key, value, idmap):
    # first, remove all the string from the value
    tmp = re.sub('([\'"][^\'"]*[\'"])', '', value)

    # detect key.value inside value
    kw = re.findall('([a-zA-Z_][a-zA-Z0-9_.]*\.[a-zA-Z0-9_.]+)', tmp)
    if not kw:
        # look like no reference, just pass it
        return eval(value, _eval_globals, idmap)

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
        if hasattr(f, 'bind'):
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

    def get_bases(self, cls):
        for base in cls.__bases__:
            if base.__name__ == 'object':
                break
            yield base
            if base.__name__ == 'Widget':
                break
            for cbase in self.get_bases(base):
                yield cbase

    def match(self, widget):
        parents = BuilderRuleName.parents
        cls = widget.__class__
        if not cls in parents:
            classes = [x.__name__.lower() for x in \
                       [cls] + list(self.get_bases(cls))]
            parents[cls] = classes
        return self.key in parents[cls]


class BuilderBase(object):
    '''Kv objects are able to load a Kivy language file or string, return the
    root object of it and inject rules into the rule database.
    '''

    def __init__(self):
        super(BuilderBase, self).__init__()
        self.rules = []
        self.templates = {}
        self.idmap = {}
        self.gidmap = {}
        self.idmaps = []

        # List of all the setattr needed to be done after creating the tree
        self.listset = []
        # List of all widget created during the tree, and then apply the style
        # for each of them.
        self.listwidget = []

    def add_rule(self, rule, defs):
        trace('Builder: adding rule %s' % str(rule))
        self.rules.append((rule, defs))

    def add_template(self, name, cls, defs):
        trace('Builder: adding template %s' % str(name))
        if name in self.templates:
            raise Exception('The template <%s> already exist' % name)
        self.templates[name] = (cls, defs)

    def load_file(self, filename, **kwargs):
        '''Insert a file into the language builder.

        :parameters:
            `rulesonly`: bool, default to False
                If True, the Builder will raise an exception if you have a root
                widget inside the definition.
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
                widget inside the definition.
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
        '''Return a list of all rules matching the widget.
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
        have_root = 'root' in self.idmap
        if not have_root:
            self.idmap['root'] = widget
        for defs in matches:
            self.build_item(widget, defs, is_rule=True)
        if not have_root:
            del self.idmap['root']

    def template(self, *args, **ctx):
        '''Create a specialized template using a specific context.
        .. versionadded:: 1.0.5

        With template, you can construct custom widget from a kv lang definition
        by giving them a context. Check :ref:`Template usage <template_usage>`.
        '''
        # Prevent naming clash with whatever the user might be putting into the
        # ctx as key.
        name = args[0]
        if not name in self.templates:
            raise Exception('Unknown <%s> template name' % name)
        baseclasses, defs = self.templates[name]
        rootwidgets = []
        for basecls in baseclasses.split('+'):
            rootwidgets.append(Factory.get(basecls))
        cls = ClassType(name, tuple(rootwidgets), {})
        widget = cls()
        self.idmap['root'] = widget
        self.idmap['ctx'] = QueryDict(ctx)
        self.build_item(widget, defs, is_rule=True)
        del self.idmap['root']
        del self.idmap['ctx']
        return widget


    #
    # Private
    #
    def _push_ids(self):
        self.idmaps.append(self.idmap)
        self.idmap = copy(self.idmap)

    def _pop_ids(self):
        self.idmap = self.idmaps.pop()

    def build(self, objects):
        self.idmap = copy(global_idmap)
        root = None
        for item, params in objects:
            if item.startswith('<'):
                self.build_rule(item, params)
            elif item.startswith('['):
                self.build_template(item, params)
            else:
                if root is not None:
                    raise ParserError(params['__ctx__'], params['__line__'],
                                   'Only one root widget is allowed')
                root = self.build_item(item, params)
                self.build_attributes()
                self.apply(root)
        return root

    def _iterate(self, params):
        for key, value in params.iteritems():
            if key in ('__line__', '__ctx__'):
                continue
            yield key, value

    def build_item(self, item, params, is_rule=False):
        self._push_ids()
        is_template = False

        if is_rule is False:
            trace('Builder: build item %s' % item)
            if item.startswith('<'):
                raise ParserError(params['__ctx__'], params['__line__'],
                               'Rules are not accepted inside widgets')
            no_apply = False
            if item.startswith('+'):
                item = item[1:]
                no_apply = True

            # we are checking is the widget is a template or not
            # if yes, no child is allowed, and all the properties are used to
            # construct the context for the template.
            cls = Factory.get(item)
            if Factory.is_template(item):
                is_template = True
            else:
                widget = cls(__no_builder=True)
                if not no_apply:
                    self.listwidget.append(widget)
        else:
            widget = item

        if is_template:
            # checking reserved keyword
            ctx = {}
            for key, value in self._iterate(params):
                if key == 'children':
                    raise ParserError(params['__ctx__'], params['__line__'],
                           'Children in template are forbidden')
                if key in ('canvas.before', 'canvas', 'canvas.after'):
                    raise ParserError(params['__ctx__'], params['__line__'],
                           'Canvas instruction in template are forbidden')
                ctx[key] = eval(value[0], _eval_globals, self.idmap)
            widget = cls(**ctx)
        else:
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
        if is_rule:
            if item is self.idmap['root']:
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
            trace('Builder: create custom callback for ' + key)
            if not element.is_event_type(key):
                key = key[3:]
            element.bind(**{key: partial(custom_callback, (
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

    def build_template(self, item, params):
        trace('Builder: build template for %s' % item)
        if item[0] != '[' or item[-1] != ']':
            raise ParserError(params['__ctx__'], params['__line__'],
                'Invalid template (must be inside [])')
        item_content = item[1:-1]
        if not '@' in item_content:
            raise ParserError(params['__ctx__'], params['__line__'],
                'Invalid template name (missing @)')
        template_name, template_root_cls = item_content.split('@')
        self.add_template(template_name, template_root_cls, params)
        Factory.register(template_name,
                         cls=partial(self.template, template_name),
                         is_template=True)


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
