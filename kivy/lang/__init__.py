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
        You can use rules to specify interactive behavior or use them to add
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

    # Syntax for creating a template
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
- Keep class names capitalized to avoid syntax errors.
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

Value Expressions, on_property Expressions, ids, and Reserved Keywords
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
        to a call to :meth:`kivy.app.App.get_running_app` in Python. ::

            Label:
                text: app.name

    args
        This keyword is available in on_<action> callbacks. It refers to the
        arguments passed to the callback. ::

            TextInput:
                on_focus: self.insert_text("Focus" if args[1] else "No focus")


.. versionchanged:: 2.1.0

    f-strings are now parsed in value expressions, allowing to bind to the
    properties that they contain.

.. kv-lang-ids:

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
with `<id>.__self__` (`btn1.__self__` in this case).

When the kv file is processed, weakrefs to all the widgets tagged with ids are
added to the root widget's `ids` dictionary. In other words, following on from
the example above, the buttons state could also be accessed as follows:

.. code-block:: python

    widget = MyWidget()
    state = widget.ids["btn1"].state

    # Or, as an alternative syntax,
    state = widget.ids.btn1.state

Note that the outermost widget applies the kv rules to all its inner widgets
before any other rules are applied. This means if an inner widget contains ids,
these ids may not be available during the inner widget's `__init__` function.

Valid expressions
~~~~~~~~~~~~~~~~~

There are two places that accept python statements in a kv file:
after a property, which assigns to the property the result of the expression
(such as the text of a button as shown above) and after a on_property, which
executes the statement when the property is updated (such as on_state).

In the former case, the
`expression <http://docs.python.org/2/reference/expressions.html>`_ can only
span a single line, cannot be extended to multiple lines using newline
escaping, and must return a value. An example of a valid expression is
``text: self.state and ('up' if self.state == 'normal' else 'down')``.

In the latter case, multiple single line statements are valid, including
those that escape their newline, as long as they don't add an indentation
level.

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
callbacks to automatically update the property via your expression when changes
occur.

Here's a simple example that demonstrates this behavior::

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
constraint to be reevaluated whenever something changes. For example,
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

In addition, properties in python f-strings are also not yet supported::

    <FStringExample>:
        text: f"I want to use {self.a} in property"

Instead, the ``format()`` method should be used::

    <FormatStringExample>:
        text: "I want to use {} in property".format(self.a)


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

The `@` character is used to separate your class name from the classes you want
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

    Using dynamic classes, a child class can be declared before its parent.
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
will react to the *on_touch_down* event.

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
These can be the variable part of the template that we can put into a context.
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

Template definitions also replace any similarly named definitions in their
entirety and thus do not support inheritance.

.. _redefining-style:

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

Redefining a widget's property style
------------------------------------

Similar to :ref:`redefining style <redefining-style>`, sometimes we
would like to inherit from a widget, keep all its KV defined styles, except for
the style applied to a specific property. For example, we would
like to inherit from a :class:`~kivy.uix.button.Button`, but we would also
like to set our own `state_image`, rather then relying on the
`background_normal` and `background_down` values. We can achieve this by
prepending a dash (-) before the `state_image` property name in the .kv style
definition.

In myapp.py:

.. code-block:: python

    class MyWidget(Button):
        new_background = StringProperty('my_background.png')

and in my.kv:

.. code-block:: kv

    <MyWidget>:
        -state_image: self.new_background

MyWidget will now have a `state_image` background set only by `new_background`,
and not by any previous styles that may have set `state_image`.

.. note::

    Although the previous rules are cleared, they are still applied during
    widget construction and are only removed when the new rule with the dash
    is reached. This means that initially, previous rules could be used to set
    the property.

Order of kwargs and KV rule application
---------------------------------------

Properties can be initialized in KV as well as in python. For example, in KV:

.. code-block:: kv

    <MyRule@Widget>:
        text: 'Hello'
        ramp: 45.
        order: self.x + 10

Then `MyRule()` would initialize all three kivy properties to
the given KV values. Separately in python, if the properties already exist as
kivy properties one can do for example `MyRule(line='Bye', side=55)`.

However, what will be the final values of the properties when
`MyRule(text='Bye', order=55)` is executed? The quick rule is that python
initialization is stronger than KV initialization only for constant rules.

Specifically, the `kwargs` provided to the python initializer are always
applied first. So in the above example, `text` is set to
`'Bye'` and `order` is set to `55`. Then, all the KV rules are applied, except
those constant rules that overwrite a python initializer provided value.

That is, the KV rules that do not creates bindings such as `text: 'Hello'`
and `ramp: 45.`, if a value for that property has been provided in python, then
that rule will not be applied.

So in the `MyRule(text='Bye', order=55)` example, `text` will be `'Bye'`,
`ramp` will be `45.`, and `order`, which creates a binding, will first be set
to `55`, but then when KV rules are applied will end up being whatever
`self.x + 10` is.

.. versionchanged:: 1.9.1

    Before, KV rules always overwrote the python values, now, python values
    are not overwritten by constant rules.


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


from kivy.lang.builder import (Observable, Builder, BuilderBase,
                               BuilderException)
from kivy.lang.parser import Parser, ParserException, global_idmap

__all__ = ('Observable', 'Builder', 'BuilderBase', 'BuilderException',
           'Parser', 'ParserException', 'global_idmap')
