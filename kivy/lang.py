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
        *(introduced in version 1.0.5.)*
        Templates will be used to populate parts of your application, such as a
        list's content. If you want to design the look of an entry in a list
        (icon on the left, text on the right), you will use a template for that.


Syntax of a kv File
-------------------

.. highlight:: kv

A Kivy language file must have ``.kv`` as filename extension.

The content of the file must always start with the Kivy header, where `version`
must be replaced with the Kivy language version you're using. For now, use
1.0::

    #:kivy `version`

    # content here

The `content` can contain rule definitions, a root widget and templates::

    # Syntax of a rule definition. Note that several Rules can share the same
    # definition (as in CSS). Note the braces; They are part of the definition.
    <Rule1,Rule2>:
        # .. definitions ..

    <Rule3>:
        # .. definitions ..

    # Syntax for creating a root widget
    RootClassName:
        # .. definitions ..

    # Syntax for create a template
    [TemplateName@BaseClass1,BaseClass2]:
        # .. definitions ..

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

    <Button>:
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

    <Button>:
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
        # .. definitions ..

    # With more than one base class
    [ClassName@BaseClass1,BaseClass2]:
        # .. definitions ..

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

.. highlight:: python

Then in Python, you can create instanciate the template with ::

    from kivy.lang import Builder

    # create a template with hello world + an image
    # the context values should be passed as kwargs to the Builder.template
    # function
    icon1 = Builder.template('IconItem', title='Hello world',
        image='myimage.png')

    # create a second template with another information
    ctx = {'title': 'Another hello world',
           'image': 'myimage2.png'}
    icon2 = Builder.template('IconItem', **ctx)
    # and use icon1 and icon2 as other widget.


Template example
~~~~~~~~~~~~~~~~

.. highlight:: kv

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
                nput: 'data/video.png'
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

.. versionadded:: 1.0.7

You can directly import class from a module::

    #: import Animation kivy.animation.Animation
    <Rule>:
        on_prop: Animation(x=.5).start(self)

set <key> <expr>
~~~~~~~~~~~~~~~~

.. versionadded:: 1.0.6

Syntax::

    #:set <key> <expr>

Set a key that will be available anywhere in the kv. For example::

    #:set my_color (.4, .3, .4)
    #:set my_color_hl (.5, .4, .5)

    <Rule>:
        state: 'normal'
        canvas:
            Color:
                rgb: my_color if self.state == 'normal' else my_color_hl
'''

__all__ = ('Builder', 'BuilderBase', 'BuilderException',
    'Parser', 'ParserException')

import codecs
import re
import sys
from os.path import join
from copy import copy
from types import ClassType, CodeType
from functools import partial
from kivy.factory import Factory
from kivy.logger import Logger
from kivy.utils import OrderedDict, QueryDict
from kivy.cache import Cache
from kivy import kivy_data_dir, require
from kivy.lib.debug import make_traceback


trace = Logger.trace
global_idmap = {}

# register cache for creating new classtype (template)
Cache.register('kv.lang')

# precompile regexp expression
lang_str = re.compile('([\'"][^\'"]*[\'"])')
lang_key = re.compile('([a-zA-Z_]+)')
lang_keyvalue = re.compile('([a-zA-Z_][a-zA-Z0-9_.]*\.[a-zA-Z0-9_.]+)')


class ParserException(Exception):
    '''Exception raised when something wrong happened in a kv file.
    '''

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
            self.filename, self.line+1, sc, message)
        super(ParserException, self).__init__(message)


class BuilderException(ParserException):
    '''Exception raised when the Builder failed to apply a rule on a widget.
    '''
    pass


class ParserRuleProperty(object):
    '''Represent a property inside a rule
    '''

    __slots__ = ('ctx', 'line', 'name', 'value', 'co_value', \
            'watched_keys', 'mode')

    def __init__(self, ctx, line, name, value):
        super(ParserRuleProperty, self).__init__()
        #: Associated parser
        self.ctx = ctx
        #: Line of the rule
        self.line = line
        #: Name of the property
        self.name = name
        #: Value of the property
        self.value = value
        #: Compiled value
        self.co_value = None
        #: Compilation mode
        self.mode = None
        #: Watched keys
        self.watched_keys = None

    def precompile(self):
        name = self.name
        value = self.value

        # first, remove all the string from the value
        tmp = re.sub(lang_str, '', self.value)

        # detecting how to handle the value according to the key name
        mode = self.mode
        if self.mode is None:
            self.mode = mode = 'exec' if name[:3] == 'on_' else 'eval'
        if mode == 'eval':
            # if we don't detect any string/key in it, we can eval and give the
            # result
            if re.search(lang_key, tmp) is None:
                self.co_value = eval(value)
                return

        # ok, we can compile.
        self.co_value = compile(value, self.ctx.filename or '<string>', mode)

        # now, detect obj.prop
        # first, remove all the string from the value
        tmp = re.sub(lang_str, '', value)
        # detect key.value inside value, and split them
        self.watched_keys = [x.split('.') for x in re.findall(lang_keyvalue,
            tmp)]
        if len(self.watched_keys) == 0:
            self.watched_keys = None

    def __repr__(self):
        return '<ParserRuleProperty name=%r filename=%s:%d' \
               'value=%r watched_keys=%r>' % (
                self.name, self.ctx.filename, self.line + 1,
                self.value, self.watched_keys)


class ParserRule(object):
    '''Represent a rule, in term if Kivy internal language
    '''

    __slots__ = ('ctx', 'line', 'name', 'children', 'id', 'properties',
            'canvas_before', 'canvas_root', 'canvas_after',
            'handlers', 'level', 'cache_marked')

    def __init__(self, ctx, line, name, level):
        super(ParserRule, self).__init__()
        #: Level of the rule in the kv
        self.level = level
        #: Associated parser
        self.ctx = ctx
        #: Line of the rule
        self.line = line
        #: Name of the rule
        self.name = name
        #: List of children to create
        self.children = []
        #: Id given to the rule
        self.id = None
        #: Properties associated to the rule
        self.properties = OrderedDict()
        #: Canvas normal
        self.canvas_root = None
        #: Canvas before
        self.canvas_before = None
        #: Canvas after
        self.canvas_after = None
        #: Handlers associated to the rule
        self.handlers = []
        #: Properties cache list: mark which class have already been checked
        self.cache_marked = []

        if level == 0:
            self._detect_selectors()
        else:
            self._forbid_selectors()

    def precompile(self):
        for x in self.properties.itervalues():
            x.precompile()
        for x in self.handlers:
            x.precompile()
        for x in self.children:
            x.precompile()
        if self.canvas_before:
            self.canvas_before.precompile()
        if self.canvas_root:
            self.canvas_root.precompile()
        if self.canvas_after:
            self.canvas_after.precompile()

    def create_missing(self, widget):
        # check first if the widget class already been processed by this rule
        cls = widget.__class__
        if cls in self.cache_marked:
            return
        self.cache_marked.append(cls)
        for name in self.properties:
            if not hasattr(widget, name):
                widget.create_property(name)

    def _forbid_selectors(self):
        c = self.name[0]
        if c == '<' or c == '[':
            raise ParserException(self.ctx, self.line,
               'Selectors rules are allowed only at the first level')

    def _detect_selectors(self):
        c = self.name[0]
        if c == '<':
            self._build_rule()
        elif c == '[':
            self._build_template()
        else:
            if self.ctx.root is not None:
                raise ParserException(self.ctx, self.line,
                   'Only one root object is allowed by .kv')
            self.ctx.root = self

    def _build_rule(self):
        name = self.name
        if __debug__:
            trace('Builder: build rule for %s' % name)
        if name[0] != '<' or name[-1] != '>':
            raise ParserException(self.ctx, self.line,
                           'Invalid rule (must be inside <>)')
        rules = name[1:-1].split(',')
        for rule in rules:
            if not len(rule):
                raise ParserException(self.ctx, self.line,
                               'Empty rule detected')
            crule = None
            if rule[0] == '.':
                crule = ParserSelectorClass(rule[1:])
            elif rule[0] == '#':
                crule = ParserSelectorId(rule[1:])
            else:
                crule = ParserSelectorName(rule)
            self.ctx.rules.append((crule, self))

    def _build_template(self):
        name = self.name
        if __debug__:
            trace('Builder: build template for %s' % name)
        if name[0] != '[' or name[-1] != ']':
            raise ParserException(self.ctx, self.line,
                'Invalid template (must be inside [])')
        item_content = name[1:-1]
        if not '@' in item_content:
            raise ParserException(self.ctx, self.line,
                'Invalid template name (missing @)')
        template_name, template_root_cls = item_content.split('@')
        self.ctx.templates.append((template_name, template_root_cls, self))

    def __repr__(self):
        return '<ParserRule name=%r>' % (self.name, )


class Parser(object):
    '''Create a Parser object to parse a Kivy language file or Kivy content.
    '''

    PROP_ALLOWED = ('canvas.before', 'canvas.after')
    CLASS_RANGE = range(ord('A'), ord('Z') + 1)
    PROP_RANGE = range(ord('A'), ord('Z') + 1) + \
                 range(ord('a'), ord('z') + 1) + \
                 range(ord('0'), ord('9') + 1) + [ord('_')]

    __slots__ = ('rules', 'templates', 'root', 'sourcecode',
        'directives', 'filename')

    def __init__(self, **kwargs):
        super(Parser, self).__init__()
        self.rules = []
        self.templates = []
        self.root = None
        self.sourcecode = []
        self.directives = []
        self.filename = kwargs.get('filename', None)
        content = kwargs.get('content', None)
        if content is None:
            raise ValueError('No content passed')
        self.parse(content)

    def execute_directives(self):
        for ln, cmd in self.directives:
            cmd = cmd.strip()
            if __debug__:
                trace('Parser: got directive <%s>' % cmd)
            if cmd[:5] == 'kivy ':
                version = cmd[5:].strip()
                if len(version.split('.')) == 2:
                    version += '.0'
                require(version)
            elif cmd[:4] == 'set ':
                try:
                    name, value = cmd[4:].strip().split(' ', 1)
                except:
                    Logger.exception('')
                    raise ParserException(self, ln, 'Invalid directive syntax')
                try:
                    value = eval(value)
                except:
                    Logger.exception('')
                    raise ParserException(self, ln, 'Invalid value')
                global_idmap[name] = value

            elif cmd[:7] == 'import ':
                package = cmd[7:].strip()
                l = package.split(' ')
                if len(l) != 2:
                    raise ParserException(self, ln, 'Invalid import syntax')
                alias, package = l
                try:
                    if package not in sys.modules:
                        try:
                            mod = __import__(package)
                        except ImportError:
                            mod = __import__('.'.join(package.split('.')[:-1]))
                        # resolve the whole thing
                        for part in package.split('.')[1:]:
                            mod = getattr(mod, part)
                    else:
                        mod = sys.modules[package]
                    global_idmap[alias] = mod
                except ImportError:
                    Logger.exception('')
                    raise ParserException(self, ln,
                            'Unable to import package %r' % package)
            else:
                raise ParserException(self, ln, 'Unknown directive')

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

        if __debug__:
            trace('Parser: parsing %d lines' % num_lines)

        # Strip all comments
        self.strip_comments(lines)

        # Execute directives
        self.execute_directives()

        # Get object from the first level
        objects, remaining_lines = self.parse_level(0, lines)

        # Precompile rules tree
        for rule in objects:
            rule.precompile()

        # After parsing, there should be no remaining lines
        # or there's an error we did not catch earlier.
        if remaining_lines:
            ln, content = remaining_lines[0]
            raise ParserException(self, ln, 'Invalid data (not parsed)')

    def strip_comments(self, lines):
        '''Remove all comments from all lines in-place.
           Comments need to be on a single line and not at the end of a line.
           I.e., a comment line's first non-whitespace character must be a #.
        '''
        # extract directives
        for ln, line in lines[:]:
            stripped = line.strip()
            if stripped[:2] == '#:':
                self.directives.append((ln, stripped[2:]))
            if stripped[:1] == '#':
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
        current_propobject = None
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
                raise ParserException(self, ln,
                               'Invalid indentation, '
                               'must be a multiple of 4 spaces')
            content = content.strip()
            rlevel = count // 4

            # Level finished
            if count < indent:
                return objects, lines[i-1:]

            # Current level, create an object
            elif count == indent:
                x = content.split(':', 1)
                if not len(x[0]):
                    raise ParserException(self, ln, 'Identifier missing')
                if len(x) == 2 and len(x[1]):
                    raise ParserException(self, ln,
                                        'Invalid data after declaration')
                name = x[0]
                # if it's not a root rule, then we got some restriction
                # aka, a valid name, without point or everything else
                if count != 0:
                    if False in [ord(z) in Parser.PROP_RANGE for z in name]:
                        raise ParserException(self, ln, 'Invalid class name')

                current_object = ParserRule(self, ln, x[0], rlevel)
                current_property = None
                objects.append(current_object)

            # Next level, is it a property or an object ?
            elif count == indent + 4:
                x = content.split(':', 1)
                if not len(x[0]):
                    raise ParserException(self, ln, 'Identifier missing')

                # It's a class, add to the current object as a children
                current_property = None
                name = x[0]
                if ord(name[0]) in Parser.CLASS_RANGE or name[0] == '+':
                    _objects, _lines = self.parse_level(level + 1, lines[i:])
                    current_object.children = _objects
                    lines = _lines
                    i = 0

                # It's a property
                else:
                    if name not in Parser.PROP_ALLOWED:
                        if False in [ord(z) in Parser.PROP_RANGE for z in name]:
                            raise ParserException(self, ln,
                                'Invalid property name')
                    if len(x) == 1:
                        raise ParserException(self, ln, 'Syntax error')
                    value = x[1].strip()
                    if name == 'id':
                        if len(value) <= 0:
                            raise ParserException(self, ln, 'Empty id')
                        if value in ('self', 'root'):
                            raise ParserException(self, ln,
                                'Invalid id, cannot be "self" or "root"')
                        current_object.id = value
                    elif len(value):
                        rule = ParserRuleProperty(self, ln, name, value)
                        if name[:3] == 'on_':
                            current_object.handlers.append(rule)
                        else:
                            current_object.properties[name] = rule
                    else:
                        current_property = name
                        current_propobject = None

            # Two more levels?
            elif count == indent + 8:
                if current_property in (
                        'canvas', 'canvas.after', 'canvas.before'):
                    _objects, _lines = self.parse_level(level + 2, lines[i:])
                    rl = ParserRule(self, ln, current_property, rlevel)
                    rl.children = _objects
                    if current_property == 'canvas':
                        current_object.canvas_root = rl
                    elif current_property == 'canvas.before':
                        current_object.canvas_before = rl
                    else:
                        current_object.canvas_after = rl
                    current_property = None
                    lines = _lines
                    i = 0
                else:
                    if current_propobject is None:
                        current_propobject = ParserRuleProperty(
                            self, ln, current_property, content)
                        if current_property[:3] == 'on_':
                            current_object.handlers.append(current_propobject)
                        else:
                            current_object.properties[current_property] = \
                                current_propobject
                    else:
                        current_propobject.value += '\n' + content

            # Too much indentation, invalid
            else:
                raise ParserException(self, ln,
                               'Invalid indentation (too many levels)')

            # Check the next line
            i += 1

        return objects, []


def custom_callback(__kvlang__, idmap, *largs, **kwargs):
    idmap['args'] = largs
    try:
        exec __kvlang__.co_value in idmap
    except:
        exc_info = sys.exc_info()
        traceback = make_traceback(exc_info)
        exc_type, exc_value, tb = traceback.standard_exc_info
        raise exc_type, exc_value, tb


def create_handler(iself, element, key, value, rule, idmap):
    locals()['__kvlang__'] = rule

    # create an handler
    idmap = copy(idmap)
    idmap.update(global_idmap)
    idmap['self'] = iself

    def call_fn(sender, _value):
        if __debug__:
            trace('Builder: call_fn %s, key=%s, value=%r' % (
                element, key, value))
        e_value = eval(value, idmap)
        if __debug__:
            trace('Builder: call_fn => value=%r' % (e_value, ))
        setattr(element, key, e_value)

    # bind every key.value
    if rule.watched_keys is not None:
        for k in rule.watched_keys:
            try:
                f = idmap[k[0]]
                for x in k[1:-1]:
                    f = getattr(f, x)
                if hasattr(f, 'bind'):
                    f.bind(**{k[-1]: call_fn})
            except KeyError:
                continue
            except AttributeError:
                continue

    try:
        return eval(value, idmap)
    except Exception, e:
        raise BuilderException(rule.ctx, rule.line, str(e))


class ParserSelector(object):

    def __init__(self, key):
        self.key = key.lower()

    def match(self, widget):
        raise NotImplemented()

    def __repr__(self):
        return '<%s key=%s>' % (self.__class__.__name__, self.key)


class ParserSelectorId(ParserSelector):

    def match(self, widget):
        return widget.id.lower() == self.key


class ParserSelectorClass(ParserSelector):

    def match(self, widget):
        return self.key in widget.cls


class ParserSelectorName(ParserSelector):

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
        parents = ParserSelectorName.parents
        cls = widget.__class__
        if not cls in parents:
            classes = [x.__name__.lower() for x in \
                       [cls] + list(self.get_bases(cls))]
            parents[cls] = classes
        return self.key in parents[cls]


class BuilderBase(object):
    '''Builder is responsible for creating a :class:`Parser` for parsing a kv
    file, merging the results to its internal rules, templates, etc.

    By default, :class:`Builder` is the global Kivy instance used in widgets,
    that you can use to load other kv file in addition to the default one.
    '''

    def __init__(self):
        super(BuilderBase, self).__init__()
        self.templates = {}
        self.rules = []
        self.rulectx = {}

    def load_file(self, filename, **kwargs):
        '''Insert a file into the language builder.

        :parameters:
            `rulesonly`: bool, default to False
                If True, the Builder will raise an exception if you have a root
                widget inside the definition.
        '''
        if __debug__:
            trace('Builder: load file %s' % filename)
        with open(filename, 'r') as fd:
            kwargs['filename'] = filename
            data = fd.read()

            # remove bom ?
            if data.startswith(codecs.BOM_UTF16_LE) or \
                data.startswith(codecs.BOM_UTF16_BE):
                raise ValueError('Unsupported UTF16 for kv files.')
            if data.startswith(codecs.BOM_UTF32_LE) or \
                data.startswith(codecs.BOM_UTF32_BE):
                raise ValueError('Unsupported UTF32 for kv files.')
            if data.startswith(codecs.BOM_UTF8):
                data = data[len(codecs.BOM_UTF8):]

            return self.load_string(data, **kwargs)

    def unload_file(self, filename):
        '''Unload all rules associated to a previously imported file.

        .. versionadded:: 1.0.8

        .. warning::

            This will not remove rule or template already applied/used on
            current widget. It will act only for the next widget creation or
            template invocation.
        '''
        # remove rules and templates
        self.rules = [x for x in self.rules if x[1].ctx.filename != filename]
        templates = {}
        for x, y in self.templates.iteritems():
            if y[2] != filename:
                templates[x] = y
        self.templates = templates

    def load_string(self, string, **kwargs):
        '''Insert a string into the Language Builder

        :Parameters:
            `rulesonly`: bool, default to False
                If True, the Builder will raise an exception if you have a root
                widget inside the definition.
        '''
        kwargs.setdefault('rulesonly', False)
        self._current_filename = fn = kwargs.get('filename', None)
        try:
            # parse the string
            parser = Parser(content=string, filename=fn)

            # merge rules with our rules
            self.rules.extend(parser.rules)

            # add the template found by the parser into ours
            for name, cls, template in parser.templates:
                self.templates[name] = (cls, template, fn)
                Factory.register(name,
                    cls=partial(self.template, name),
                    is_template=True)

            # create root object is exist
            if kwargs['rulesonly'] and parser.root:
                filename = kwargs.get('rulesonly', '<string>')
                raise Exception('The file <%s> contain also non-rules '
                                'directives' % filename)

            if parser.root:
                widget = Factory.get(parser.root.name)()
                self._apply_rule(widget, parser.root, parser.root)
                return widget
        finally:
            self._current_filename = None

    def template(self, *args, **ctx):
        '''Create a specialized template using a specific context.
        .. versionadded:: 1.0.5

        With template, you can construct custom widget from a kv lang definition
        by giving them a context. Check :ref:`Template usage <template_usage>`.
        '''
        # Prevent naming clash with whatever the user might be putting into the
        # ctx as key.
        name = args[0]
        if name not in self.templates:
            raise Exception('Unknown <%s> template name' % name)
        baseclasses, rule, fn = self.templates[name]
        key = '%s|%s' % (name, baseclasses)
        cls = Cache.get('kv.lang', key)
        if cls is None:
            rootwidgets = []
            for basecls in baseclasses.split('+'):
                rootwidgets.append(Factory.get(basecls))
            cls = ClassType(name, tuple(rootwidgets), {})
            Cache.append('kv.lang', key, cls)
        widget = cls()
        self._apply_rule(widget, rule, rule, template_ctx=ctx)
        return widget

    def apply(self, widget):
        '''Search all the rules that match the widget, and apply them.
        '''
        rules = self.match(widget)
        if __debug__:
            trace('Builder: Found %d rules for %s' % (len(rules), widget))
        if not rules:
            return
        for rule in rules:
            self._apply_rule(widget, rule, rule)

    def _apply_rule(self, widget, rule, rootrule, template_ctx=None):
        # widget: the current instanciated widget
        # rule: the current rule
        # rootrule: the current root rule (for children of a rule)

        # will collect reference to all the id in children
        assert(rule not in self.rulectx)
        self.rulectx[rule] = rctx = {
            'ids': {'root': widget},
            'set': [], 'hdl': []}

        # extract the context of the rootrule (not rule!)
        assert(rootrule in self.rulectx)
        rctx = self.rulectx[rootrule]

        # if a template context is passed, put it as "ctx"
        if template_ctx is not None:
            rctx['ids']['ctx'] = QueryDict(template_ctx)

        # if we got an id, put it in the root rule for a later global usage
        if rule.id:
            rctx['ids'][rule.id] = widget

        # first, ensure that the widget have all the properties used in the rule
        # if not, they will be created as ObjectProperty.
        rule.create_missing(widget)

        # build the widget canvas
        if rule.canvas_before:
            with widget.canvas.before:
                self._build_canvas(widget.canvas.before, widget,
                        rule.canvas_before, rootrule)
        if rule.canvas_root:
            with widget.canvas:
                self._build_canvas(widget.canvas, widget,
                        rule.canvas_root, rootrule)
        if rule.canvas_after:
            with widget.canvas.after:
                self._build_canvas(widget.canvas.after, widget,
                        rule.canvas_after, rootrule)

        # create children tree
        Factory_get = Factory.get
        Factory_is_template = Factory.is_template
        for crule in rule.children:
            cname = crule.name

            # depending if the child rule is a template or not, we are not
            # having the same approach
            cls = Factory_get(cname)

            if Factory_is_template(cname):
                # we got a template, so extract all the properties and handlers,
                # and push them in a "ctx" dictionnary.
                ctx = {}
                idmap = copy(global_idmap)
                idmap.update({'root': rctx['ids']['root']})
                for prule in crule.properties.itervalues():
                    value = prule.co_value
                    if type(value) is CodeType:
                        try:
                            value = eval(value, idmap)
                        except Exception, e:
                            raise BuilderException(
                                    prule.ctx, prule.line, str(e))
                    ctx[prule.name] = value
                for prule in crule.handlers:
                    try:
                        value = eval(prule.value, idmap)
                    except Exception, e:
                        raise BuilderException(prule.ctx, prule.line, str(e))
                    ctx[prule.name] = value

                # create the template with an explicit ctx
                child = cls(**ctx)
                widget.add_widget(child)

                # reference it on our root rule context
                if crule.id:
                    rctx['ids'][crule.id] = child

            else:
                # we got a "normal" rule, construct it manually
                # we can't construct it without __no_builder=True, because the
                # previous implementation was doing the add_widget() before
                # apply(), and so, we could use "self.parent".
                child = cls(__no_builder=True)
                widget.add_widget(child)
                self.apply(child)
                self._apply_rule(child, crule, rootrule)

        # append the properties and handlers to our final resolution task
        if rule.properties:
            rctx['set'].append((widget, rule.properties.values()))
        if rule.handlers:
            rctx['hdl'].append((widget, rule.handlers))

        # if we are applying another rule that the root one, then it's done for
        # us!
        if rootrule is not rule:
            del self.rulectx[rule]
            return

        # normally, we can apply a list of properties with a proper context
        for widget_set, rules in reversed(rctx['set']):
            for rule in rules:
                assert(isinstance(rule, ParserRuleProperty))
                key = rule.name
                value = rule.co_value
                if type(value) is CodeType:
                    value = create_handler(widget_set, widget_set, key,
                            value, rule, rctx['ids'])
                setattr(widget_set, key, value)

        # build handlers
        for widget_set, rules in rctx['hdl']:
            for crule in rules:
                assert(isinstance(crule, ParserRuleProperty))
                assert(crule.name.startswith('on_'))
                key = crule.name
                if not widget_set.is_event_type(key):
                    key = key[3:]
                idmap = copy(global_idmap)
                idmap.update(rctx['ids'])
                idmap['self'] = widget_set
                widget_set.bind(**{key: partial(custom_callback,
                    crule, idmap)})

        # rule finished, forget it
        del self.rulectx[rootrule]

    def match(self, widget):
        '''Return a list of :class:`ParserRule` matching the widget.
        '''
        rules = []
        for selector, rule in self.rules:
            if selector.match(widget):
                rules.append(rule)
        return rules

    def _build_canvas(self, canvas, widget, rule, rootrule):
        idmap = copy(self.rulectx[rootrule]['ids'])
        for crule in rule.children:
            name = crule.name
            if name == 'Clear':
                canvas.clear()
                continue
            instr = Factory.get(name)()
            for prule in crule.properties.itervalues():
                try:
                    key = prule.name
                    value = prule.co_value
                    if type(value) is CodeType:
                        value = create_handler(
                            widget, instr, key, value, prule, idmap)
                    setattr(instr, key, value)
                except Exception, e:
                    raise BuilderException(prule.ctx, prule.line, str(e))

#: Main instance of a :class:`BuilderBase`.
Builder = BuilderBase()
Builder.load_file(join(kivy_data_dir, 'style.kv'), rulesonly=True)

