'''Kivy Language
=============

The Kivy language is a language dedicated to describing user interface and
interactions. You could compare this language to Qt's QML
(http://qt.nokia.com), but we included new concepts such as rule definitions
(which are somewhat akin to what you may know from CSS), templating and so on.

.. versionchanged:: 1.7.0

    The Builder doesn't execute canvas expressions in realtime anymore. It will
    pack all the expressions that need to be executed first and execute them
    after dispatching input, just before drawing the frame. If you want to
    force the execution of canvas drawing, just call
    :meth:`Builder.sync <BuilderBase.sync>`.

    An experimental profiling tool for the kv lang is also included. You can
    activate it by setting the environment variable `KIVY_PROFILE_LANG=1`.
    It will then generate an html file named `builder_stats.html`.

Overview
--------

The language consists of several constructs that you can use:

    Rules
        A rule is similar to a CSS rule. A rule applies to specific widgets (or
        classes thereof) in your widget tree and modifies them in a
        certain way.
        You can use rules to specify interactive behaviour or use them to add
        graphical representations of the widgets they apply to.
        You can target a specific class of widgets (similar to the CSS
        concept of a *class*) by using the ``cls`` attribute (e.g.
        ``cls=MyTestWidget``).

    A Root Widget
        You can use the language to create your entire user interface.
        A kv file must contain only one root widget at most.

    Dynamic Classes
        *(introduced in version 1.7.0)*
        Dynamic classes let you create new widgets and rules on-the-fly,
        without any Python declaration.

    Templates (deprecated)
        *(introduced in version 1.0.5, deprecated from version 1.7.0)*
        Templates were used to populate parts of an application, such as
        styling the content of a list (e.g. icon on the left, text on the
        right). They are now deprecated by dynamic classes.


Syntax of a kv File
-------------------

.. highlight:: kv

A Kivy language file must have ``.kv`` as filename extension.

The content of the file should always start with the Kivy header, where
`version` must be replaced with the Kivy language version you're using.
For now, use 1.0::

    #:kivy `1.0`

    # content here

The `content` can contain rule definitions, a root widget, dynamic class
definitions and templates::

    # Syntax of a rule definition. Note that several Rules can share the same
    # definition (as in CSS). Note the braces: they are part of the definition.
    <Rule1,Rule2>:
        # .. definitions ..

    <Rule3>:
        # .. definitions ..

    # Syntax for creating a root widget
    RootClassName:
        # .. definitions ..

    # Syntax for creating a dynamic class
    <NewWidget@BaseClass>:
        # .. definitions ..

    # Syntax for create a template
    [TemplateName@BaseClass1,BaseClass2]:
        # .. definitions ..

Regardless of whether it's a rule, root widget, dynamic class or
template you're defining, the definition should look like this::

    # With the braces it's a rule. Without them, it's a root widget.
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
property of `AnotherClass`. If the widget doesn't have a property with
the given name, an :class:`~kivy.properties.ObjectProperty` will be
automatically created and added to the widget.

`AnotherClass` will be created and added as a child of the `ClassName`
instance.

- The indentation is important and must be consistent. The spacing must be a
  multiple of the number of spaces used on the first indented line. Spaces
  are encouraged: mixing tabs and spaces is not recommended.
- The value of a property must be given on a single line (for now at least).
- The `canvas` property is special: you can put graphics instructions in it
  to create a graphical representation of the current class.


Here is a simple example of a kv file that contains a root widget::

    #:kivy 1.0

    Button:
        text: 'Hello world'


.. versionchanged:: 1.7.0

    The indentation is not limited to 4 spaces anymore. The spacing must be a
    multiple of the number of spaces used on the first indented line.

Both the :meth:`~BuilderBase.load_file` and the
:meth:`~BuilderBase.load_string` methods
return the root widget defined in your kv file/string. They will also add any
class and template definitions to the :class:`~kivy.factory.Factory` for later
usage.

Value Expressions, on_property Expressions, ids and Reserved Keywords
---------------------------------------------------------------------

When you specify a property's value, the value is evaluated as a Python
expression. This expression can be static or dynamic, which means that
the value can use the values of other properties using reserved keywords.

    self
        The keyword self references the "current widget instance"::

            Button:
                text: 'My state is %s' % self.state

    root
        This keyword is available only in rule definitions and represents the
        root widget of the rule (the first instance of the rule)::

            <MyWidget>:
                custom: 'Hello world'
                Button:
                    text: root.custom

    app
        This keyword always refers to your app instance. It's equivalent
        to a call to :meth:`kivy.app.App.get_running_app` in Python.::

            Label:
                text: app.name

    args
        This keyword is available in on_<action> callbacks. It refers to the
        arguments passed to the callback.::

            TextInput:
                on_focus: self.insert_text("Focus" if args[1] else "No focus")

ids
~~~

Class definitions may contain ids which can be used as a keywords:::

    <MyWidget>:
        Button:
            id: btn1
        Button:
            text: 'The state of the other button is %s' % btn1.state

Please note that the `id` will not be available in the widget instance:
it is used exclusively for external references. `id` is a weakref to the
widget, and not the widget itself. The widget itself can be accessed
with `id.__self__` (`btn1.__self__` in this case).

When the kv file is processed, weakrefs to all the widgets tagged with ids are
added to the root widgets `ids` dictionary. In other words, following on from
the example above, the buttons state could also be accessed as follows:

.. code-block:: python

    widget = MyWidget()
    state = widget.ids["btn1"].state

    # Or, as an alternative syntax,
    state = widget.ids.btn1.state

Note that the outermost widget applies the kv rules to all its inner widgets
before any other rules are applied. This means if an inner widget contains ids,
these ids may not be available during the inner widget's `__init__` function.

Valid expressons
~~~~~~~~~~~~~~~~

There are two places that accept python statments in a kv file:
after a property, which assigns to the property the result of the expression
(such as the text of a button as shown above) and after a on_property, which
executes the statement when the property is updated (such as on_state).

In the former case, the
`expression <http://docs.python.org/2/reference/expressions.html>`_ can only
span a single line, cannot be extended to multiple lines using newline
escaping, and must return a value. An example of a valid expression is
``text: self.state and ('up' if self.state == 'normal' else 'down')``.

In the latter case, multiple single line statements are valid including
multi-line statements that escape their newline, as long as they don't
add an indentation level.

Examples of valid statements are:

.. code-block:: python

    on_press: if self.state == 'normal': print('normal')
    on_state:
        if self.state == 'normal': print('normal')
        else: print('down')
        if self.state == 'normal': \\
        print('multiline normal')
        for i in range(10): print(i)
        print([1,2,3,4,
        5,6,7])

An example of a invalid statement:

.. code-block:: python

    on_state:
        if self.state == 'normal':
            print('normal')

Relation Between Values and Properties
--------------------------------------

When you use the Kivy language, you might notice that we do some work
behind the scenes to automatically make things work properly. You should
know that :doc:`api-kivy.properties` implement the
`Observer Design Pattern <http://en.wikipedia.org/wiki/Observer_pattern>`_.
That means that you can bind your own function to be
called when the value of a property changes (i.e. you passively
`observe` the property for potential changes).

The Kivy language detects properties in your `value` expression and will create
create callbacks to automatically update the property via your expression when
changes occur.

Here's a simple example that demonstrates this behaviour::

    Button:
        text: str(self.state)

In this example, the parser detects that `self.state` is a dynamic value (a
property). The :attr:`~kivy.uix.button.Button.state` property of the button
can change at any moment (when the user touches it).
We now want this button to display its own state as text, even as the state
changes. To do this, we use the state property of the Button and use it in the
value expression for the button's `text` property, which controls what text is
displayed on the button (We also convert the state to a string representation).
Now, whenever the button state changes, the text property will be updated
automatically.

Remember: The value is a python expression! That means that you can do
something more interesting like::

    Button:
        text: 'Plop world' if self.state == 'normal' else 'Release me!'

The Button text changes with the state of the button. By default, the button
text will be 'Plop world', but when the button is being pressed, the text will
change to 'Release me!'.

More precisely, the kivy language parser detects all substrings of the form
`X.a.b` where `X` is `self` or `root` or `app` or a known id, and `a` and `b`
are properties: it then adds the appropriate dependencies to cause the
the constraint to be reevaluated whenever something changes. For example,
this works exactly as expected::

    <IndexedExample>:
        beta: self.a.b[self.c.d]

However, due to limitations in the parser which hopefully may be lifted in the
future, the following doesn't work::

    <BadExample>:
        beta: self.a.b[self.c.d].e.f

indeed the `.e.f` part is not recognized because it doesn't follow the expected
pattern, and so, does not result in an appropriate dependency being setup.
Instead, an intermediate property should be introduced to allow the following
constraint::

    <GoodExample>:
        alpha: self.a.b[self.c.d]
        beta: self.alpha.e.f


Graphical Instructions
----------------------

The graphical instructions are a special part of the Kivy language. They are
handled by the 'canvas' property definition::

    Widget:
        canvas:
            Color:
                rgb: (1, 1, 1)
            Rectangle:
                size: self.size
                pos: self.pos

All the classes added inside the canvas property must be derived from the
:class:`~kivy.graphics.Instruction` class. You cannot put any Widget class
inside the canvas property (as that would not make sense because a
widget is not a graphics instruction).

If you want to do theming, you'll have the same question as in CSS: which rules
have been executed first? In our case, the rules are executed
in processing order (i.e. top-down).

If you want to change how Buttons are rendered, you can create your own kv file
and add something like this::

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

This will result in buttons having a red background with the label in the
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

.. _dynamic_classes:

Dynamic classes
---------------

Dynamic classes allow you to create new widgets on-the-fly, without any python
declaration in the first place. The syntax of the dynamic classes is similar to
the Rules, but you need to specify the base classes you want to
subclass.

The syntax looks like:

.. code-block:: kv

    # Simple inheritance
    <NewWidget@Button>:
        # kv code here ...

    # Multiple inheritance
    <NewWidget@ButtonBehavior+Label>:
        # kv code here ...

The `@` character is used to seperate your class name from the classes you want
to subclass. The Python equivalent would have been:

.. code-block:: python

    # Simple inheritance
    class NewWidget(Button):
        pass

    # Multiple inheritance
    class NewWidget(ButtonBehavior, Label):
        pass

Any new properties, usually added in python code, should be declared
first. If the property doesn't exist in the dynamic class, it will be
automatically created as an :class:`~kivy.properties.ObjectProperty`
(pre 1.8.0) or as an appropriate typed property (from version
1.8.0).

.. versionchanged:: 1.8.0

    If the property value is an expression that can be evaluated right away (no
    external binding), then the value will be used as default value of the
    property, and the type of the value will be used for the specialization of
    the Property class. In other terms: if you declare `hello: "world"`, a new
    :class:`~kivy.properties.StringProperty` will be instantiated, with the
    default value `"world"`. Lists, tuples, dictionaries and strings are
    supported.

Let's illustrate the usage of these dynamic classes with an
implementation of a basic Image button. We could derive our classes from
the Button and just add a property for the image filename:

.. code-block:: kv

    <ImageButton@Button>:
        source: None

        Image:
            source: root.source
            pos: root.pos
            size: root.size

    # let's use the new classes in another rule:
    <MainUI>:
        BoxLayout:
            ImageButton:
                source: 'hello.png'
                on_press: root.do_something()
            ImageButton:
                source: 'world.png'
                on_press: root.do_something_else()

In Python, you can create an instance of the dynamic class as follows:

.. code-block:: python

    from kivy.factory import Factory
    button_inst = Factory.ImageButton()

.. note::

    Using dynamic classes, a child class can be declared before it's parent.
    This however, leads to the unintuitive situation where the parent
    properties/methods override those of the child. Be careful if you choose
    to do this.

.. _template_usage:

Templates
---------

.. versionchanged:: 1.7.0

    Template usage is now deprecated. Please use Dynamic classes instead.

Syntax of templates
~~~~~~~~~~~~~~~~~~~

Using a template in Kivy requires 2 things :

    #. a context to pass for the context (will be ctx inside template).
    #. a kv definition of the template.

Syntax of a template:

.. code-block:: kv

    # With only one base class
    [ClassName@BaseClass]:
        # .. definitions ..

    # With more than one base class
    [ClassName@BaseClass1,BaseClass2]:
        # .. definitions ..

For example, for a list, you'll need to create a entry with a image on
the left, and a label on the right. You can create a template for making
that definition easier to use.
So, we'll create a template that uses 2 entries in the context: an image
filename and a title:

.. code-block:: kv

    [IconItem@BoxLayout]:
        Image:
            source: ctx.image
        Label:
            text: ctx.title

Then in Python, you can instantiate the template using:

.. code-block:: python

    from kivy.lang import Builder

    # create a template with hello world + an image
    # the context values should be passed as kwargs to the Builder.template
    # function
    icon1 = Builder.template('IconItem', title='Hello world',
        image='myimage.png')

    # create a second template with other information
    ctx = {'title': 'Another hello world',
           'image': 'myimage2.png'}
    icon2 = Builder.template('IconItem', **ctx)
    # and use icon1 and icon2 as other widget.


Template example
~~~~~~~~~~~~~~~~

Most of time, when you are creating a screen in the kv lang, you use a lot of
redefinitions. In our example, we'll create a Toolbar, based on a
BoxLayout, and put in a few :class:`~kivy.uix.image.Image` widgets that
will react to the *on_touch_down* event.:

.. code-block:: kv

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

We can see that the size and size_hint attribute are exactly the same.
More than that, the callback in on_touch_down and the image are changing.
Theses can be the variable part of the template that we can put into a context.
Let's try to create a template for the Image:

.. code-block:: kv

    [ToolbarButton@Image]:

        # This is the same as before
        size: self.texture_size
        size_hint: None, None

        # Now, we are using the ctx for the variable part of the template
        source: 'data/%s.png' % ctx.image
        on_touch_down: self.collide_point(*args[1].pos) and ctx.callback()

The template can be used directly in the MyToolbar rule:

.. code-block:: kv

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

    #. you cannot use references other than "root":

        .. code-block:: kv

            <MyRule>:
                Widget:
                    id: mywidget
                    value: 'bleh'
                Template:
                    ctxkey: mywidget.value # << fail, this references the id
                    # mywidget

    #. not all of the dynamic parts will be understood:

        .. code-block:: kv

            <MyRule>:
                Template:
                    ctxkey: 'value 1' if root.prop1 else 'value2' # << even if
                    # root.prop1 is a property, if it changes value, ctxkey
                    # will not be updated

Redefining a widget's style
---------------------------

Sometimes we would like to inherit from a widget in order to use its Python
properties without also using its .kv defined style. For example, we would
like to inherit from a Label, but we would also like to define our own
canvas instructions instead of automatically using the canvas instructions
inherited from the Label. We can achieve this by prepending a dash (-) before
the class name in the .kv style definition.

In myapp.py:

.. code-block:: python

    class MyWidget(Label):
        pass

and in my.kv:

.. code-block:: kv

    <-MyWidget>:
        canvas:
            Color:
                rgb: 1, 1, 1
            Rectangle:
                size: (32, 32)

MyWidget will now have a Color and Rectangle instruction in its canvas
without any of the instructions inherited from the Label.

Lang Directives
---------------

You can use directives to add declarative commands, such as imports or constant
definitions, to the lang files. Directives are added as comments in the
following format:

.. code-block:: kv

    #:<directivename> <options>

import <package>
~~~~~~~~~~~~~~~~

.. versionadded:: 1.0.5

Syntax:

.. code-block:: kv

    #:import <alias> <package>

You can import a package by writing:

.. code-block:: kv

    #:import os os

    <Rule>:
        Button:
            text: os.getcwd()

Or more complex:

.. code-block:: kv

    #:import ut kivy.utils

    <Rule>:
        canvas:
            Color:
                rgba: ut.get_random_color()

.. versionadded:: 1.0.7

You can directly import classes from a module:

.. code-block:: kv

    #: import Animation kivy.animation.Animation
    <Rule>:
        on_prop: Animation(x=.5).start(self)

set <key> <expr>
~~~~~~~~~~~~~~~~

.. versionadded:: 1.0.6

Syntax:

.. code-block:: kv

    #:set <key> <expr>

Set a key that will be available anywhere in the kv. For example:

.. code-block:: kv

    #:set my_color (.4, .3, .4)
    #:set my_color_hl (.5, .4, .5)

    <Rule>:
        state: 'normal'
        canvas:
            Color:
                rgb: my_color if self.state == 'normal' else my_color_hl

include <file>
~~~~~~~~~~~~~~~~

.. versionadded:: 1.9.0

Syntax:

.. code-block:: kv

    #:include [force] <file>

Includes an external kivy file. This allows you to split complex
widgets into their own files. If the include is forced, the file
will first be unloaded and then reloaded again. For example:

.. code-block:: kv

    # Test.kv
    #:include mycomponent.kv
    #:include force mybutton.kv

    <Rule>:
        state: 'normal'
        MyButton:
        MyComponent:


.. code-block:: kv

    # mycomponent.kv
    #:include mybutton.kv

    <MyComponent>:
        MyButton:

.. code-block:: kv

    # mybutton.kv

    <MyButton>:
        canvas:
            Color:
                rgb: (1.0, 0.0, 0.0)
            Rectangle:
                pos: self.pos
                size: (self.size[0]/4, self.size[1]/4)

'''
import os

__all__ = ('Observable', 'Builder', 'BuilderBase', 'BuilderException', 'Parser',
           'ParserException')

import codecs
import re
import sys
import traceback
import types
from re import sub, findall
from os import environ
from os.path import join
from copy import copy
from types import CodeType
from functools import partial
from collections import OrderedDict, defaultdict

from kivy.factory import Factory
from kivy.logger import Logger
from kivy.utils import QueryDict
from kivy.cache import Cache
from kivy import kivy_data_dir, require
from kivy.compat import PY2, iteritems, iterkeys
from kivy.context import register_context
from kivy.resources import resource_find
import kivy.metrics as Metrics
from kivy._event import Observable, EventDispatcher


trace = Logger.trace
global_idmap = {}

# late import
Instruction = None

# register cache for creating new classtype (template)
Cache.register('kv.lang')

# all previously included files
__KV_INCLUDES__ = []

# precompile regexp expression
lang_str = re.compile('([\'"][^\'"]*[\'"])')
lang_key = re.compile('([a-zA-Z_]+)')
lang_keyvalue = re.compile('([a-zA-Z_][a-zA-Z0-9_.]*\.[a-zA-Z0-9_.]+)')
lang_tr = re.compile('(_\()')

# class types to check with isinstance
if PY2:
    _cls_type = (type, types.ClassType)
else:
    _cls_type = (type, )

# all the widget handlers, used to correctly unbind all the callbacks then the
# widget is deleted
_handlers = defaultdict(list)


class ProxyApp(object):
    # proxy app object
    # taken from http://code.activestate.com/recipes/496741-object-proxying/

    __slots__ = ['_obj']

    def __init__(self):
        object.__init__(self)
        object.__setattr__(self, '_obj', None)

    def _ensure_app(self):
        app = object.__getattribute__(self, '_obj')
        if app is None:
            from kivy.app import App
            app = App.get_running_app()
            object.__setattr__(self, '_obj', app)
            # Clear cached application instance, when it stops
            app.bind(on_stop=lambda instance:
                     object.__setattr__(self, '_obj', None))
        return app

    def __getattribute__(self, name):
        object.__getattribute__(self, '_ensure_app')()
        return getattr(object.__getattribute__(self, '_obj'), name)

    def __delattr__(self, name):
        object.__getattribute__(self, '_ensure_app')()
        delattr(object.__getattribute__(self, '_obj'), name)

    def __setattr__(self, name, value):
        object.__getattribute__(self, '_ensure_app')()
        setattr(object.__getattribute__(self, '_obj'), name, value)

    def __bool__(self):
        object.__getattribute__(self, '_ensure_app')()
        return bool(object.__getattribute__(self, '_obj'))

    def __str__(self):
        object.__getattribute__(self, '_ensure_app')()
        return str(object.__getattribute__(self, '_obj'))

    def __repr__(self):
        object.__getattribute__(self, '_ensure_app')()
        return repr(object.__getattribute__(self, '_obj'))


global_idmap['app'] = ProxyApp()
global_idmap['pt'] = Metrics.pt
global_idmap['inch'] = Metrics.inch
global_idmap['cm'] = Metrics.cm
global_idmap['mm'] = Metrics.mm
global_idmap['dp'] = Metrics.dp
global_idmap['sp'] = Metrics.sp


# delayed calls are canvas expression triggered during an loop. It is one
# directional linked list of args to call call_fn with. Each element is a list
# whos last element points to the next list of args to execute when
# Builder.sync is called.
_delayed_start = None


class ParserException(Exception):
    '''Exception raised when something wrong happened in a kv file.
    '''

    def __init__(self, context, line, message, cause=None):
        self.filename = context.filename or '<inline>'
        self.line = line
        sourcecode = context.sourcecode
        sc_start = max(0, line - 2)
        sc_stop = min(len(sourcecode), line + 3)
        sc = ['...']
        for x in range(sc_start, sc_stop):
            if x == line:
                sc += ['>> %4d:%s' % (line + 1, sourcecode[line][1])]
            else:
                sc += ['   %4d:%s' % (x + 1, sourcecode[x][1])]
        sc += ['...']
        sc = '\n'.join(sc)

        message = 'Parser: File "%s", line %d:\n%s\n%s' % (
            self.filename, self.line + 1, sc, message)
        if cause:
            message += '\n' + ''.join(traceback.format_tb(cause))

        super(ParserException, self).__init__(message)


class BuilderException(ParserException):
    '''Exception raised when the Builder failed to apply a rule on a widget.
    '''
    pass


class ParserRuleProperty(object):
    '''Represent a property inside a rule.
    '''

    __slots__ = ('ctx', 'line', 'name', 'value', 'co_value',
                 'watched_keys', 'mode', 'count')

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
        #: Stats
        self.count = 0

    def precompile(self):
        name = self.name
        value = self.value

        # first, remove all the string from the value
        tmp = sub(lang_str, '', self.value)

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
        value = '\n' * self.line + value
        self.co_value = compile(value, self.ctx.filename or '<string>', mode)

        # for exec mode, we don't need to watch any keys.
        if mode == 'exec':
            return

        # now, detect obj.prop
        # first, remove all the string from the value
        tmp = sub(lang_str, '', value)
        idx = tmp.find('#')
        if idx != -1:
            tmp = tmp[:idx]
        # detect key.value inside value, and split them
        wk = list(set(findall(lang_keyvalue, tmp)))
        if len(wk):
            self.watched_keys = [x.split('.') for x in wk]
        if findall(lang_tr, tmp):
            if self.watched_keys:
                self.watched_keys += [['_']]
            else:
                self.watched_keys = [['_']]

    def __repr__(self):
        return '<ParserRuleProperty name=%r filename=%s:%d ' \
               'value=%r watched_keys=%r>' % (
                   self.name, self.ctx.filename, self.line + 1,
                   self.value, self.watched_keys)


class ParserRule(object):
    '''Represents a rule, in terms of the Kivy internal language.
    '''

    __slots__ = ('ctx', 'line', 'name', 'children', 'id', 'properties',
                 'canvas_before', 'canvas_root', 'canvas_after',
                 'handlers', 'level', 'cache_marked', 'avoid_previous_rules')

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
        #: Indicate if any previous rules should be avoided.
        self.avoid_previous_rules = False

        if level == 0:
            self._detect_selectors()
        else:
            self._forbid_selectors()

    def precompile(self):
        for x in self.properties.values():
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
            if hasattr(widget, name):
                continue
            value = self.properties[name].co_value
            if type(value) is CodeType:
                value = None
            widget.create_property(name, value)

    def _forbid_selectors(self):
        c = self.name[0]
        if c == '<' or c == '[':
            raise ParserException(
                self.ctx, self.line,
                'Selectors rules are allowed only at the first level')

    def _detect_selectors(self):
        c = self.name[0]
        if c == '<':
            self._build_rule()
        elif c == '[':
            self._build_template()
        else:
            if self.ctx.root is not None:
                raise ParserException(
                    self.ctx, self.line,
                    'Only one root object is allowed by .kv')
            self.ctx.root = self

    def _build_rule(self):
        name = self.name
        if __debug__:
            trace('Builder: build rule for %s' % name)
        if name[0] != '<' or name[-1] != '>':
            raise ParserException(self.ctx, self.line,
                                  'Invalid rule (must be inside <>)')

        # if the very first name start with a -, avoid previous rules
        name = name[1:-1]
        if name[:1] == '-':
            self.avoid_previous_rules = True
            name = name[1:]

        rules = name.split(',')
        for rule in rules:
            crule = None

            if not len(rule):
                raise ParserException(self.ctx, self.line,
                                      'Empty rule detected')

            if '@' in rule:
                # new class creation ?
                # ensure the name is correctly written
                rule, baseclasses = rule.split('@', 1)
                if not re.match(lang_key, rule):
                    raise ParserException(self.ctx, self.line,
                                          'Invalid dynamic class name')

                # save the name in the dynamic classes dict.
                self.ctx.dynamic_classes[rule] = baseclasses
                crule = ParserSelectorName(rule)

            else:
                # classical selectors.

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
    CLASS_RANGE = list(range(ord('A'), ord('Z') + 1))
    PROP_RANGE = (
        list(range(ord('A'), ord('Z') + 1)) +
        list(range(ord('a'), ord('z') + 1)) +
        list(range(ord('0'), ord('9') + 1)) + [ord('_')])

    __slots__ = ('rules', 'templates', 'root', 'sourcecode',
                 'directives', 'filename', 'dynamic_classes')

    def __init__(self, **kwargs):
        super(Parser, self).__init__()
        self.rules = []
        self.templates = []
        self.root = None
        self.sourcecode = []
        self.directives = []
        self.dynamic_classes = {}
        self.filename = kwargs.get('filename', None)
        content = kwargs.get('content', None)
        if content is None:
            raise ValueError('No content passed')
        self.parse(content)

    def execute_directives(self):
        global __KV_INCLUDES__
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
            elif cmd[:8] == 'include ':
                ref = cmd[8:].strip()
                force_load = False

                if ref[:6] == 'force ':
                    ref = ref[6:].strip()
                    force_load = True

                if ref[-3:] != '.kv':
                    Logger.warn('WARNING: {0} does not have a valid Kivy'
                                'Language extension (.kv)'.format(ref))
                    break
                if ref in __KV_INCLUDES__:
                    if not os.path.isfile(ref):
                        raise ParserException(self, ln,
                            'Invalid or unknown file: {0}'.format(ref))
                    if not force_load:
                        Logger.warn('WARNING: {0} has already been included!'
                                    .format(ref))
                        break
                    else:
                        Logger.debug('Reloading {0} because include was forced.'
                                    .format(ref))
                        Builder.unload_file(ref)
                        Builder.load_file(ref)
                        continue
                Logger.debug('Including file: {0}'.format(0))
                __KV_INCLUDES__.append(ref)
                Builder.load_file(ref)
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
                                          'Unable to import package %r' %
                                          package)
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
        lines = list(zip(list(range(num_lines)), lines))
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
           i.e. a comment line's first non-whitespace character must be a #.
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

    def parse_level(self, level, lines, spaces=0):
        '''Parse the current level (level * spaces) indentation.
        '''
        indent = spaces * level if spaces > 0 else 0
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
            tmp = content[:len(content) - len(tmp)]
            tmp = tmp.replace('\t', '    ')

            # first indent designates the indentation
            if spaces == 0:
                spaces = len(tmp)

            count = len(tmp)

            if spaces > 0 and count % spaces != 0:
                raise ParserException(self, ln,
                                      'Invalid indentation, '
                                      'must be a multiple of '
                                      '%s spaces' % spaces)
            content = content.strip()
            rlevel = count // spaces if spaces > 0 else 0

            # Level finished
            if count < indent:
                return objects, lines[i - 1:]

            # Current level, create an object
            elif count == indent:
                x = content.split(':', 1)
                if not len(x[0]):
                    raise ParserException(self, ln, 'Identifier missing')
                if (len(x) == 2 and len(x[1]) and
                    not x[1].lstrip().startswith('#')):
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
            elif count == indent + spaces:
                x = content.split(':', 1)
                if not len(x[0]):
                    raise ParserException(self, ln, 'Identifier missing')

                # It's a class, add to the current object as a children
                current_property = None
                name = x[0]
                if ord(name[0]) in Parser.CLASS_RANGE or name[0] == '+':
                    _objects, _lines = self.parse_level(
                        level + 1, lines[i:], spaces)
                    current_object.children = _objects
                    lines = _lines
                    i = 0

                # It's a property
                else:
                    if name not in Parser.PROP_ALLOWED:
                        if not all(ord(z) in Parser.PROP_RANGE for z in name):
                            raise ParserException(self, ln,
                                                  'Invalid property name')
                    if len(x) == 1:
                        raise ParserException(self, ln, 'Syntax error')
                    value = x[1].strip()
                    if name == 'id':
                        if len(value) <= 0:
                            raise ParserException(self, ln, 'Empty id')
                        if value in ('self', 'root'):
                            raise ParserException(
                                self, ln,
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
            elif count == indent + 2 * spaces:
                if current_property in (
                        'canvas', 'canvas.after', 'canvas.before'):
                    _objects, _lines = self.parse_level(
                        level + 2, lines[i:], spaces)
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


def get_proxy(widget):
    try:
        return widget.proxy_ref
    except AttributeError:
        return widget


def custom_callback(__kvlang__, idmap, *largs, **kwargs):
    idmap['args'] = largs
    exec(__kvlang__.co_value, idmap)


def call_fn(args, instance, v):
    element, key, value, rule, idmap = args
    if __debug__:
        trace('Builder: call_fn %s, key=%s, value=%r, %r' % (
            element, key, value, rule.value))
    rule.count += 1
    e_value = eval(value, idmap)
    if __debug__:
        trace('Builder: call_fn => value=%r' % (e_value, ))
    setattr(element, key, e_value)


def delayed_call_fn(args, instance, v):
    # it's already on the list
    if args[-1] is not None:
        return

    global _delayed_start
    if _delayed_start is None:
        _delayed_start = args
        args[-1] = StopIteration
    else:
        args[-1] = _delayed_start
        _delayed_start = args


def update_intermediates(base, keys, bound, s, fn, args, instance, value):
    ''' Function that is called when an intermediate property is updated
    and `rebind` of that property is True. In that case, we unbind
    all bound funcs that were bound to attrs of the old value of the
    property and rebind to the new value of the property.

    For example, if the rule is `self.a.b.c.d`, then when b is changed, we
    unbind from `b`, `c` and `d`, if they were bound before (they were not
    None and `rebind` of the respective properties was True) and we rebind
    to the new values of the attrs `b`, `c``, `d` that are not None and
    `rebind` is True.

    :Parameters:
        `base`
            A (proxied) ref to the base widget, `self` in the example
            above.
        `keys`
            A list of the name off the attrs of `base` being watched. In
            the example above it'd be `['a', 'b', 'c', 'd']`.
        `bound`
            A list 4-tuples, each tuple being (widget, attr, callback, uid)
            representing callback functions bound to the attributed `attr`
            of `widget`. `uid` is returned by `fast_bind` when binding.
            The callback may be None, in which case the attr
            was not bound, but is there to be able to walk the attr tree.
            E.g. in the example above, if `b` was not an eventdispatcher,
            `(_b_ref_, `c`, None)` would be added to the list so we can get
            to `c` and `d`, which may be eventdispatchers and their attrs.
        `s`
            The index in `keys` of the of the attr that needs to be
            updated. That is all the keys from `s` and further will be
            rebound, since the `s` key was changed. In bound, the
            corresponding index is `s - 1`. If `s` is None, we start from
            1 (first attr).
        `fn`
            The function to be called args, `args` on bound callback.
    '''
    # first remove all the old bound functions from `s` and down.
    for f, k, fun, uid in bound[s:]:
        if fun is None:
            continue
        try:
            f.unbind_uid(k, uid)
        except ReferenceError:
            pass
    del bound[s:]

    # find the first attr from which we need to start rebinding.
    f = getattr(*bound[-1][:2])
    if f is None:
        fn(args, None, None)
        return
    s += 1
    append = bound.append

    # bind all attrs, except last to update_intermediates
    for val in keys[s:-1]:
        # if we need to dynamically rebind, bindm otherwise just
        # add the attr to the list
        if isinstance(f, (EventDispatcher, Observable)):
            prop = f.property(val, True)
            if prop is not None and getattr(prop, 'rebind', False):
                # fast_bind should not dispatch, otherwise
                # update_intermediates might be called in the middle
                # here messing things up
                uid = f.fast_bind(
                    val, update_intermediates, base, keys, bound, s, fn, args)
                append([f.proxy_ref, val, update_intermediates, uid])
            else:
                append([f.proxy_ref, val, None, None])
        else:
            append([getattr(f, 'proxy_ref', f), val, None, None])

        f = getattr(f, val, None)
        if f is None:
            break
        s += 1

    # for the last attr we bind directly to the setting function,
    # because that attr sets the value of the rule.
    if isinstance(f, (EventDispatcher, Observable)):
        uid = f.fast_bind(keys[-1], fn, args)
        if uid:
            append([f.proxy_ref, keys[-1], fn, uid])
    # when we rebind we have to update the
    # rule with the most recent value, otherwise, the value might be wrong
    # and wouldn't be updated since we might not have tracked it before.
    # This only happens for a callback when rebind was True for the prop.
    fn(args, None, None)


def create_handler(iself, element, key, value, rule, idmap, delayed=False):
    idmap = copy(idmap)
    idmap.update(global_idmap)
    idmap['self'] = iself.proxy_ref
    handler_append = _handlers[iself.uid].append

    # we need a hash for when delayed, so we don't execute duplicate canvas
    # callbacks from the same handler during a sync op
    if delayed:
        fn = delayed_call_fn
        args = [element, key, value, rule, idmap, None]  # see _delayed_start
    else:
        fn = call_fn
        args = (element, key, value, rule, idmap)

    # bind every key.value
    if rule.watched_keys is not None:
        for keys in rule.watched_keys:
            base = idmap.get(keys[0])
            if base is None:
                continue
            f = base = getattr(base, 'proxy_ref', base)
            bound = []
            was_bound = False
            append = bound.append

            # bind all attrs, except last to update_intermediates
            k = 1
            for val in keys[1:-1]:
                # if we need to dynamically rebind, bindm otherwise
                # just add the attr to the list
                if isinstance(f, (EventDispatcher, Observable)):
                    prop = f.property(val, True)
                    if prop is not None and getattr(prop, 'rebind', False):
                        # fast_bind should not dispatch, otherwise
                        # update_intermediates might be called in the middle
                        # here messing things up
                        uid = f.fast_bind(
                            val, update_intermediates, base, keys, bound, k,
                            fn, args)
                        append([f.proxy_ref, val, update_intermediates, uid])
                        was_bound = True
                    else:
                        append([f.proxy_ref, val, None, None])
                elif not isinstance(f, _cls_type):
                    append([getattr(f, 'proxy_ref', f), val, None, None])
                else:
                    append([f, val, None, None])
                f = getattr(f, val, None)
                if f is None:
                    break
                k += 1

            # for the last attr we bind directly to the setting
            # function, because that attr sets the value of the rule.
            if isinstance(f, (EventDispatcher, Observable)):
                uid = f.fast_bind(keys[-1], fn, args)  # f is not None
                if uid:
                    append([f.proxy_ref, keys[-1], fn, uid])
                    was_bound = True
            if was_bound:
                handler_append(bound)

    try:
        return eval(value, idmap)
    except Exception as e:
        tb = sys.exc_info()[2]
        raise BuilderException(rule.ctx, rule.line,
                               '{}: {}'.format(e.__class__.__name__, e),
                               cause=tb)


class ParserSelector(object):

    def __init__(self, key):
        self.key = key.lower()

    def match(self, widget):
        raise NotImplemented()

    def __repr__(self):
        return '<%s key=%s>' % (self.__class__.__name__, self.key)


class ParserSelectorId(ParserSelector):

    def match(self, widget):
        if widget.id:
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
            classes = [x.__name__.lower() for x in
                       [cls] + list(self.get_bases(cls))]
            parents[cls] = classes
        return self.key in parents[cls]


class BuilderBase(object):
    '''The Builder is responsible for creating a :class:`Parser` for parsing a
    kv file, merging the results into its internal rules, templates, etc.

    By default, :class:`Builder` is a global Kivy instance used in widgets
    that you can use to load other kv files in addition to the default ones.
    '''

    _match_cache = {}

    def __init__(self):
        super(BuilderBase, self).__init__()
        self.files = []
        self.dynamic_classes = {}
        self.templates = {}
        self.rules = []
        self.rulectx = {}

    def load_file(self, filename, **kwargs):
        '''Insert a file into the language builder and return the root widget
        (if defined) of the kv file.

        :parameters:
            `rulesonly`: bool, defaults to False
                If True, the Builder will raise an exception if you have a root
                widget inside the definition.
        '''
        filename = resource_find(filename) or filename
        if __debug__:
            trace('Builder: load file %s' % filename)
        with open(filename, 'r') as fd:
            kwargs['filename'] = filename
            data = fd.read()

            # remove bom ?
            if PY2:
                if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
                    raise ValueError('Unsupported UTF16 for kv files.')
                if data.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
                    raise ValueError('Unsupported UTF32 for kv files.')
                if data.startswith(codecs.BOM_UTF8):
                    data = data[len(codecs.BOM_UTF8):]

            return self.load_string(data, **kwargs)

    def unload_file(self, filename):
        '''Unload all rules associated with a previously imported file.

        .. versionadded:: 1.0.8

        .. warning::

            This will not remove rules or templates already applied/used on
            current widgets. It will only effect the next widgets creation or
            template invocation.
        '''
        # remove rules and templates
        self.rules = [x for x in self.rules if x[1].ctx.filename != filename]
        self._clear_matchcache()
        templates = {}
        for x, y in self.templates.items():
            if y[2] != filename:
                templates[x] = y
        self.templates = templates
        if filename in self.files:
            self.files.remove(filename)

        # unregister all the dynamic classes
        Factory.unregister_from_filename(filename)

    def load_string(self, string, **kwargs):
        '''Insert a string into the Language Builder and return the root widget
        (if defined) of the kv string.

        :Parameters:
            `rulesonly`: bool, defaults to False
                If True, the Builder will raise an exception if you have a root
                widget inside the definition.
        '''
        kwargs.setdefault('rulesonly', False)
        self._current_filename = fn = kwargs.get('filename', None)

        # put a warning if a file is loaded multiple times
        if fn in self.files:
            Logger.warning(
                'Lang: The file {} is loaded multiples times, '
                'you might have unwanted behaviors.'.format(fn))

        try:
            # parse the string
            parser = Parser(content=string, filename=fn)

            # merge rules with our rules
            self.rules.extend(parser.rules)
            self._clear_matchcache()

            # add the template found by the parser into ours
            for name, cls, template in parser.templates:
                self.templates[name] = (cls, template, fn)
                Factory.register(name,
                                 cls=partial(self.template, name),
                                 is_template=True, warn=True)

            # register all the dynamic classes
            for name, baseclasses in iteritems(parser.dynamic_classes):
                Factory.register(name, baseclasses=baseclasses, filename=fn,
                                 warn=True)

            # create root object is exist
            if kwargs['rulesonly'] and parser.root:
                filename = kwargs.get('rulesonly', '<string>')
                raise Exception('The file <%s> contain also non-rules '
                                'directives' % filename)

            # save the loaded files only if there is a root without
            # template/dynamic classes
            if fn and (parser.templates or
                       parser.dynamic_classes or parser.rules):
                self.files.append(fn)

            if parser.root:
                widget = Factory.get(parser.root.name)()
                self._apply_rule(widget, parser.root, parser.root)
                return widget
        finally:
            self._current_filename = None

    def template(self, *args, **ctx):
        '''Create a specialized template using a specific context.
        .. versionadded:: 1.0.5

        With templates, you can construct custom widgets from a kv lang
        definition by giving them a context. Check :ref:`Template usage
        <template_usage>`.
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
            cls = type(name, tuple(rootwidgets), {})
            Cache.append('kv.lang', key, cls)
        widget = cls()
        # in previous versions, ``ctx`` is passed as is as ``template_ctx``
        # preventing widgets in it from be collected by the GC. This was
        # especially relevant to AccordionItem's title_template.
        proxy_ctx = {k: get_proxy(v) for k, v in ctx.items()}
        self._apply_rule(widget, rule, rule, template_ctx=proxy_ctx)
        return widget

    def apply(self, widget):
        '''Search all the rules that match the widget and apply them.
        '''
        rules = self.match(widget)
        if __debug__:
            trace('Builder: Found %d rules for %s' % (len(rules), widget))
        if not rules:
            return
        for rule in rules:
            self._apply_rule(widget, rule, rule)

    def _clear_matchcache(self):
        BuilderBase._match_cache = {}

    def _apply_rule(self, widget, rule, rootrule, template_ctx=None):
        # widget: the current instantiated widget
        # rule: the current rule
        # rootrule: the current root rule (for children of a rule)

        # will collect reference to all the id in children
        assert(rule not in self.rulectx)
        self.rulectx[rule] = rctx = {
            'ids': {'root': widget.proxy_ref},
            'set': [], 'hdl': []}

        # extract the context of the rootrule (not rule!)
        assert(rootrule in self.rulectx)
        rctx = self.rulectx[rootrule]

        # if a template context is passed, put it as "ctx"
        if template_ctx is not None:
            rctx['ids']['ctx'] = QueryDict(template_ctx)

        # if we got an id, put it in the root rule for a later global usage
        if rule.id:
            # use only the first word as `id` discard the rest.
            rule.id = rule.id.split('#', 1)[0].strip()
            rctx['ids'][rule.id] = widget.proxy_ref
            # set id name as a attribute for root widget so one can in python
            # code simply access root_widget.id_name
            _ids = dict(rctx['ids'])
            _root = _ids.pop('root')
            _new_ids = _root.ids
            for _key in iterkeys(_ids):
                if _ids[_key] == _root:
                    # skip on self
                    continue
                _new_ids[_key] = _ids[_key]
            _root.ids = _new_ids

        # first, ensure that the widget have all the properties used in
        # the rule if not, they will be created as ObjectProperty.
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

            if cname in ('canvas', 'canvas.before', 'canvas.after'):
                raise ParserException(
                    crule.ctx, crule.line,
                    'Canvas instructions added in kv must '
                    'be declared before child widgets.')

            # depending if the child rule is a template or not, we are not
            # having the same approach
            cls = Factory_get(cname)

            if Factory_is_template(cname):
                # we got a template, so extract all the properties and
                # handlers, and push them in a "ctx" dictionary.
                ctx = {}
                idmap = copy(global_idmap)
                idmap.update({'root': rctx['ids']['root']})
                if 'ctx' in rctx['ids']:
                    idmap.update({'ctx': rctx['ids']['ctx']})
                try:
                    for prule in crule.properties.values():
                        value = prule.co_value
                        if type(value) is CodeType:
                            value = eval(value, idmap)
                        ctx[prule.name] = value
                    for prule in crule.handlers:
                        value = eval(prule.value, idmap)
                        ctx[prule.name] = value
                except Exception as e:
                    tb = sys.exc_info()[2]
                    raise BuilderException(
                        prule.ctx, prule.line,
                        '{}: {}'.format(e.__class__.__name__, e), cause=tb)

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
            rctx['set'].append((widget.proxy_ref,
                                list(rule.properties.values())))
        if rule.handlers:
            rctx['hdl'].append((widget.proxy_ref, rule.handlers))

        # if we are applying another rule that the root one, then it's done for
        # us!
        if rootrule is not rule:
            del self.rulectx[rule]
            return

        # normally, we can apply a list of properties with a proper context
        try:
            rule = None
            for widget_set, rules in reversed(rctx['set']):
                for rule in rules:
                    assert(isinstance(rule, ParserRuleProperty))
                    key = rule.name
                    value = rule.co_value
                    if type(value) is CodeType:
                        value = create_handler(widget_set, widget_set, key,
                                               value, rule, rctx['ids'])
                    setattr(widget_set, key, value)
        except Exception as e:
            if rule is not None:
                tb = sys.exc_info()[2]
                raise BuilderException(rule.ctx, rule.line,
                                       '{}: {}'.format(e.__class__.__name__,
                                                       e), cause=tb)
            raise e

        # build handlers
        try:
            crule = None
            for widget_set, rules in rctx['hdl']:
                for crule in rules:
                    assert(isinstance(crule, ParserRuleProperty))
                    assert(crule.name.startswith('on_'))
                    key = crule.name
                    if not widget_set.is_event_type(key):
                        key = key[3:]
                    idmap = copy(global_idmap)
                    idmap.update(rctx['ids'])
                    idmap['self'] = widget_set.proxy_ref
                    if not widget_set.fast_bind(key, custom_callback, crule,
                                                idmap):
                        raise AttributeError(key)
                    #hack for on_parent
                    if crule.name == 'on_parent':
                        Factory.Widget.parent.dispatch(widget_set.__self__)
        except Exception as e:
            if crule is not None:
                tb = sys.exc_info()[2]
                raise BuilderException(
                    crule.ctx, crule.line,
                    '{}: {}'.format(e.__class__.__name__, e), cause=tb)
            raise e

        # rule finished, forget it
        del self.rulectx[rootrule]

    def match(self, widget):
        '''Return a list of :class:`ParserRule` objects matching the widget.
        '''
        cache = BuilderBase._match_cache
        k = (widget.__class__, widget.id, tuple(widget.cls))
        if k in cache:
            return cache[k]
        rules = []
        for selector, rule in self.rules:
            if selector.match(widget):
                if rule.avoid_previous_rules:
                    del rules[:]
                rules.append(rule)
        cache[k] = rules
        return rules

    def sync(self):
        '''Execute all the waiting operations, such as the execution of all the
        expressions related to the canvas.

        .. versionadded:: 1.7.0
        '''
        global _delayed_start
        next_args = _delayed_start
        if next_args is None:
            return

        while next_args is not StopIteration:
            # is this try/except still needed? yes, in case widget died in this
            # frame after the call was scheduled
            try:
                call_fn(next_args[:-1], None, None)
            except ReferenceError:
                pass
            args = next_args
            next_args = args[-1]
            args[-1] = None
        _delayed_start = None

    def unbind_widget(self, uid):
        '''(internal) Unbind all the handlers created by the rules of the
        widget. The :attr:`kivy.uix.widget.Widget.uid` is passed here
        instead of the widget itself, because we are using it in the
        widget destructor.

        .. versionadded:: 1.7.2
        '''
        if uid not in _handlers:
            return
        for callbacks in _handlers[uid]:
            for f, k, fn, bound_uid in callbacks:
                if fn is None:  # it's not a kivy prop.
                    continue
                try:
                    f.unbind_uid(k, bound_uid)
                except ReferenceError:
                    # proxy widget is already gone, that's cool :)
                    pass
        del _handlers[uid]

    def _build_canvas(self, canvas, widget, rule, rootrule):
        global Instruction
        if Instruction is None:
            Instruction = Factory.get('Instruction')
        idmap = copy(self.rulectx[rootrule]['ids'])
        for crule in rule.children:
            name = crule.name
            if name == 'Clear':
                canvas.clear()
                continue
            instr = Factory.get(name)()
            if not isinstance(instr, Instruction):
                raise BuilderException(
                    crule.ctx, crule.line,
                    'You can add only graphics Instruction in canvas.')
            try:
                for prule in crule.properties.values():
                    key = prule.name
                    value = prule.co_value
                    if type(value) is CodeType:
                        value = create_handler(
                            widget, instr.proxy_ref,
                            key, value, prule, idmap, True)
                    setattr(instr, key, value)
            except Exception as e:
                tb = sys.exc_info()[2]
                raise BuilderException(
                    prule.ctx, prule.line,
                    '{}: {}'.format(e.__class__.__name__, e), cause=tb)

#: Main instance of a :class:`BuilderBase`.
Builder = register_context('Builder', BuilderBase)
Builder.load_file(join(kivy_data_dir, 'style.kv'), rulesonly=True)

if 'KIVY_PROFILE_LANG' in environ:
    import atexit
    import cgi

    def match_rule(fn, index, rule):
        if rule.ctx.filename != fn:
            return
        for prop, prp in iteritems(rule.properties):
            if prp.line != index:
                continue
            yield prp
        for child in rule.children:
            for r in match_rule(fn, index, child):
                yield r
        if rule.canvas_root:
            for r in match_rule(fn, index, rule.canvas_root):
                yield r
        if rule.canvas_before:
            for r in match_rule(fn, index, rule.canvas_before):
                yield r
        if rule.canvas_after:
            for r in match_rule(fn, index, rule.canvas_after):
                yield r

    def dump_builder_stats():
        html = [
            '<!doctype html>'
            '<html><body>',
            '<style type="text/css">\n',
            'pre { margin: 0; }\n',
            '</style>']
        files = set([x[1].ctx.filename for x in Builder.rules])
        for fn in files:
            lines = open(fn).readlines()
            html += ['<h2>', fn, '</h2>', '<table>']
            count = 0
            for index, line in enumerate(lines):
                line = line.rstrip()
                line = cgi.escape(line)
                matched_prp = []
                for psn, rule in Builder.rules:
                    matched_prp += list(match_rule(fn, index, rule))

                count = sum(set([x.count for x in matched_prp]))

                color = (255, 155, 155) if count else (255, 255, 255)
                html += ['<tr style="background-color: rgb{}">'.format(color),
                         '<td>', str(index + 1), '</td>',
                         '<td>', str(count), '</td>',
                         '<td><pre>', line, '</pre></td>',
                         '</tr>']
            html += ['</table>']
        html += ['</body></html>']
        with open('builder_stats.html', 'w') as fd:
            fd.write(''.join(html))

        print('Profiling written at builder_stats.html')

    atexit.register(dump_builder_stats)
