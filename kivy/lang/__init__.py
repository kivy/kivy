'''Kivy Language
=============

The Kivy language is a language dedicated to describing user interface and
interactions. You could compare this language to Qt's QML
(http://qt.nokia.com), but we included new concepts such as rule definitions
(which are somewhat akin to what you may know from CSS), dynamic classes and
so on.

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

.. versionchanged:: 3.0.0

    The deprecated ``[Name@Base]:`` template syntax (introduced in 1.0.5,
    deprecated in 1.7.0) has been removed. Use dynamic classes
    (``<Name@Base>:``) instead.


Syntax of a kv File
-------------------

.. highlight:: kv

A Kivy language file must have ``.kv`` as filename extension.

The content of the file should always start with the Kivy header, where
`version` must be replaced with the Kivy language version you're using.
For now, use 1.0::

    #:kivy `1.0`

    # content here

The `content` can contain rule definitions, a root widget and dynamic
class definitions::

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

Regardless of whether it's a rule, root widget, or dynamic class you're
defining, the definition should look like this::

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
class definitions to the :class:`~kivy.factory.Factory` for later usage.

Value Expressions, on_property Expressions, ids, and Reserved Keywords
---------------------------------------------------------------------

When you specify a property's value, the value is evaluated as a Python
expression. This expression can be static or dynamic, which means that
the value can use the values of other properties using reserved keywords.

    self
        The keyword self references the "current widget instance"::

            Button:
                text: 'My pressed state is %s' % self.pressed

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
            text: 'The pressed state of the other button is %s' % btn1.pressed

Please note that the `id` will not be available in the widget instance:
it is used exclusively for external references. `id` is a weakref to the
widget, and not the widget itself. The widget itself can be accessed
with `<id>.__self__` (`btn1.__self__` in this case).

When the kv file is processed, weakrefs to all the widgets tagged with ids are
added to the root widget's `ids` dictionary. In other words, following on from
the example above, the buttons state could also be accessed as follows:

.. code-block:: python

    widget = MyWidget()
    pressed = widget.ids["btn1"].pressed

    # Or, as an alternative syntax,
    pressed = widget.ids.btn1.pressed

Note that the outermost widget applies the kv rules to all its inner widgets
before any other rules are applied. This means if an inner widget contains ids,
these ids may not be available during the inner widget's `__init__` function.

Valid expressions
~~~~~~~~~~~~~~~~~

There are two places that accept python statements in a kv file:
after a property, which assigns to the property the result of the expression
(such as the text of a button as shown above) and after a on_property, which
executes the statement when the property is updated (such as on_pressed).

In the former case, the
`expression <http://docs.python.org/2/reference/expressions.html>`_ can only
span a single line, cannot be extended to multiple lines using newline
escaping, and must return a value. An example of a valid expression is
``text: self.pressed and ('up' if self.pressed else 'down')``.

In the latter case, multiple single line statements are valid, including
those that escape their newline, as long as they don't add an indentation
level.

Examples of valid statements are:

.. code-block:: python

    on_press: if self.pressed: print('normal')
    on_pressed:
        if self.pressed: print('normal')
        else: print('down')
        if self.pressed: \\
        print('multiline normal')
        for i in range(10): print(i)
        print([1,2,3,4,
        5,6,7])

An example of a invalid statement:

.. code-block:: python

    on_pressed:
        if self.pressed:
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
        text: str(self.pressed)

In this example, the parser detects that `self.pressed` is a dynamic value (a
property). The :attr:`~kivy.uix.button.Button.pressed` property of the button
can change at any moment (when the user touches it).
We now want this button to display its own state as text, even as the state
changes. To do this, we use the state property of the Button and use it in the
value expression for the button's `text` property, which controls what text is
displayed on the button (We also convert the state to a string representation).
Now, whenever the button `pressed` state changes, the text property will be
updated automatically.

Remember: The value is a python expression! That means that you can do
something more interesting like::

    Button:
        text: 'Plop world' if self.pressed else 'Release me!'

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

.. _kv_control_statements:

Control statements
------------------

.. versionadded:: 3.0.0

Control statements let a rule's widget tree change at runtime: child widgets
that appear and disappear, and lists that grow and shrink, all described in kv
and kept in sync automatically.

At any child-widget position a rule may contain an ``if`` / ``elif`` / ``else``,
``for``, ``slot`` or ``factory`` block. Each block is **reactive**: when a
property used in its header changes, the block rebuilds the content it manages.
There is nothing to wire up -- reassign the property and the tree follows.

Conditional content
~~~~~~~~~~~~~~~~~~~~

Mount widgets only while a condition holds:

.. code-block:: kv

    <LoginPanel@BoxLayout>:
        logged_in: False
        Label:
            text: 'Account'
        if self.logged_in:
            Button:
                text: 'Log out'
        else:
            TextInput:
                hint_text: 'username'
            Button:
                text: 'Log in'

Toggling ``logged_in`` swaps a single *Log out* button for a username field
plus a *Log in* button, keeping their place after the *Account* label. An
inactive branch's widgets are not in the tree at all: unlike a widget hidden
with ``opacity`` / ``disabled``, they leave no ghost touch target and no
leftover layout space.

``elif`` and ``else`` are optional and chain as in Python. A bare ``if`` with no
matching branch simply builds nothing while its condition is false:

.. code-block:: kv

    if self.error:
        Label:
            text: self.message

Setting properties from a branch
********************************

An ``if`` / ``elif`` / ``else`` branch is a *full rule body* applied to the host
widget while active. Besides children it may set the host's own properties, so a
group of properties that all hinge on one condition can state it once instead of
repeating it on every line:

.. code-block:: kv

    <StatusLabel@Label>:
        error: False
        if self.error:
            color: 1, 0, 0, 1
            bold: True
            font_size: '18sp'
        else:
            color: 1, 1, 1, 1
            bold: False
            font_size: '14sp'

A property that does not exist yet is created on demand, exactly as elsewhere in
kv.

A branch only *adds* the bindings it declares while active and drops them when
it leaves; it never reverts a property to a previous value. So the ``else``
branch is what brings a value back -- without one, the property simply keeps the
active branch's last value after that branch leaves. (If an unconditional rule
and a branch, or two branches, drive the same property at once, that is allowed:
their bindings coexist and the last dependency to change wins, just as with
overlapping plain kv rules. Prefer a single ``if`` / ``else`` where you can.)

Canvas and event handlers in a branch
*************************************

A branch may also declare a ``canvas`` and bind event handlers, mounted when the
branch becomes active and torn down when it leaves:

.. code-block:: kv

    <Badge@Widget>:
        urgent: False
        count: 0
        if self.urgent:
            on_touch_down: print('badge tapped')
            canvas:
                Color:
                    rgba: 1, 0, 0, 1
                Ellipse:
                    pos: self.pos
                    size: self.size
            Label:
                text: f'{root.count}'

The branch's ``canvas`` is added to the host's canvas while active and removed
when the branch leaves; its instruction expressions update on the next
:meth:`Builder.sync <BuilderBase.sync>`, like any kv canvas. Handlers are bound
on activation and unbound on teardown. Host properties, ``canvas`` and handlers
belong to ``if`` / ``elif`` / ``else`` blocks *outside* any ``for``: an ``if``
nested inside a ``for`` follows the for-body rules instead (its property lines
are iteration-locals, and handlers and ``canvas`` stay forbidden -- see
`Iteration-local values`_).

Repeated content
~~~~~~~~~~~~~~~~

Build one copy of the body per item, kept in sync as the iterable changes:

.. code-block:: kv

    <TodoList@BoxLayout>:
        items: []
        for item in self.items:
            Label:
                text: item.title

A single iteration can build several widgets -- everything in the body is
repeated together, so the loop variables are available to a whole cluster of
children (and to their event handlers):

.. code-block:: kv

    for item in self.items:
        Label:
            text: item.title
        Button:
            text: 'delete'
            on_press: root.items = [x for x in root.items if x is not item]

The header uses Python's *comprehension* grammar -- exactly what is valid
between the brackets of a list comprehension, which is not quite statement
grammar -- so tuple (and starred) targets and a trailing ``if`` filter work:

.. code-block:: kv

    for i, item in enumerate(self.items) if item.visible:
        Label:
            text: f'{i}: {item.title}'

The iterable is an ordinary kv expression, so the usual binding rules and
gotchas apply: reassigning the property dispatches (and list/dict properties
dispatch on in-place changes), but mutating a plain value nested inside one
does not. Iterating something that is not iterable (``None``, say) fails
exactly as it does in Python; the error simply carries the kv file and line.

There is no ``for`` / ``else``. The idiomatic empty state is a paired ``if``
on the same property -- the duplicated condition costs one line and reads
plainly:

.. code-block:: kv

    if not self.items:
        Label:
            text: 'nothing here yet'
    for item in self.items:
        Label:
            text: item.title

``for`` builds a *real* widget per item, so it is not efficient for long lists
or frequently mutated ones. :class:`~kivy.uix.recycleview.RecycleView` is
the right tool for large, scrolling, virtualised lists. ``for`` targets the
everyday handful-of-widgets case where RecycleView would be overkill.

Keyed reconciliation
********************

By default an iteration's identity is its position in the iterable, so a change
rebuilds the widgets from the first differing position on. That is fine for
stateless content, but a widget holding live state -- text being edited, focus,
selection or scroll position -- would lose it as soon as an item is inserted or
the list is reordered.

Add a ``key:`` line as the first entry in the body to give each iteration a
stable identity instead:

.. code-block:: kv

    for item in self.items:
        key: item.uid
        TextInput:
            text: item.title

Now an iteration keeps its widgets for as long as its key is present: **same
key, same widgets**. When the order changes the widgets are moved, not rebuilt;
and when the item behind a kept key is *replaced*, the new loop values are
re-dispatched through the existing bindings instead of rebuilding. So a
``TextInput`` the user is editing survives another item being inserted above
it, the whole list being reordered, or its own item being swapped for an
updated copy: the same widget instance stays, and with it its text, cursor and
focus. Only new keys build widgets, and only vanished keys destroy them.

Keys behave like dict keys -- hashable, compared by equality -- and must be
unique. Use *stable* values (an id, a uuid), not something that editing the
item would change. Re-dispatch follows ordinary property semantics: a
replacement that compares equal to the previous value does not dispatch.

Iteration-local values
**********************

A property line in a ``for`` body is not a host property but an
*iteration-local*: a named, reactive value computed once per iteration and
shared by everything in that iteration's body (so a ``[]`` is a single list, not
a fresh one at each use):

.. code-block:: kv

    <Cart@BoxLayout>:
        items: []
        for item in self.items:
            total: item.qty * item.price      # iteration-local
            Label:
                text: f'{item.qty}'
            Label:
                text: f'= {total}'             # reads the same value

The name is visible only inside the block (it is not a property of the host
widget), shadows enclosing names, and re-evaluates reactively when its
dependencies change. A local may reference the loop targets and earlier locals
of the same block:

.. code-block:: kv

    for x in self.values:
        squared: x * x
        scaled: squared * self.factor
        Label:
            text: f'{scaled}'

The general rule is that **a property line binds to the nearest enclosing
scope**: the iteration scope when a ``for`` encloses it, the host widget
otherwise. So a property line in an ``if`` nested inside a ``for`` is a
*conditional* iteration-local: it starts as ``None``, is bound while the
branch is active, and keeps its last value when the branch leaves -- one-way,
like every kv binding; give the chain an ``else`` to set it back. Handlers
and ``canvas`` follow the same nesting-context rule and stay forbidden
anywhere under a ``for``.

A local may not share its name with an ``id`` in the same block. Unlike
Python shadowing, both writers would stay live (the id is written at mount,
the local re-evaluates on every dependency change), so the collision is a
parse-time error.

Slots
~~~~~

A slot is a named hole a container rule leaves for its callers to fill, with
fallback content for when they don't -- the same idea as Vue slots or the
web-components ``<slot>``. It lets you build a reusable shell once and drop
different content into it at each call site, without subclassing:

.. code-block:: kv

    <Card@BoxLayout>:
        orientation: 'vertical'
        slot header:
            Label:                       # fallback, shown if nobody fills it
                text: 'Untitled'
        slot:                            # default slot: plain children land here
        Label:
            text: 'footer'

    # usage:
    Card:
        slot header:
            Image:
                source: root.logo
        Label:                           # plain child, routed to the default slot
            text: 'body'

The first rule declaring ``slot name:`` defines the insertion point and its
fallback. Any later rule declaring the same name provides content instead, and
the most derived provider wins: a subclass rule overrides the base fallback, and
the widget instance overrides both. Fill content is evaluated in the context of
the rule providing it, so ``root.logo`` above refers to the rule instantiating
the ``Card``, not to the ``Card`` itself. A filled slot never builds its
fallback.

A slot may be defined inside an ``if`` block (the insertion point then comes and
goes with the branch), and a fill may itself declare new slots under a fresh
name, re-exposing customization through a wrapper class. Filling a name that no
class rule ever declared degrades to defining a new insertion point at the fill's
own position -- since nothing can ever fill an instance-level definition, this is
almost always a typo, and a warning is logged.

Slot-scoped locals (slot props)
*******************************

A property line in a slot *definition* declares a slot-scoped local: a
reactive value computed in the defining rule's context and handed to whatever
content ends up in the hole. Fallback and fill content read it through the
reserved ``slot`` name:

.. code-block:: kv

    <UserCard@BoxLayout>:
        user: None
        slot badge:
            display_name: self.user.name if self.user else ''
            Label:
                text: slot.display_name        # the fallback reads it

    # call site -- the fill reads the same value, still computed by UserCard
    UserCard:
        user: some_user
        slot badge:
            Label:
                text: '@' + slot.display_name
                bold: True

This is how a reusable shell passes data to caller-provided content (the same
idea as Vue's scoped slots). When slots nest, the innermost ``slot`` wins.

An ``id`` is allowed on content declared in an explicit ``slot`` block -- a
definition's fallback or a fill. It becomes a reactive id on the rule
*providing* that content (``None`` while the content is not built), reachable
by that rule's other expressions like an ``if`` id. Implicitly routed plain
children cannot carry an id: whether they are routed depends on the class
rules, which the parser cannot see from the call site -- use an explicit
``slot:`` fill block instead.

Widgets chosen by class
~~~~~~~~~~~~~~~~~~~~~~~~~

``factory <expr>`` builds a single child widget whose *class* is chosen by an
expression -- a class object, or a name resolved through the
:class:`~kivy.factory.Factory`. The block body is applied to the instance, and
the widget is rebuilt when the class expression changes:

.. code-block:: kv

    <Form@BoxLayout>:
        schema: []
        for field in self.schema:
            factory field['cls']:        # e.g. 'TextInput', 'CheckBox', ...
                hint_text: field.get('label', '')

The expression is ordinary Python, so a runtime choice between classes needs no
extra machinery:

.. code-block:: kv

    for item in self.items:
        factory 'StrongLabel' if item.highlighted else 'Label':
            text: item.text

A ``None`` class builds nothing, and a constant class name is built once with no
binding. When the class does change, the widget is rebuilt and the body
re-applied; while it stays the same the instance is kept and its body
expressions stay reactive.

In depth
~~~~~~~~

Reactive ids
************

A widget inside a control block may carry an ``id``. Because such a widget comes
and goes, the id is *reactive* rather than a fixed entry in ``root.ids``.

In an ``if`` / ``elif`` / ``else`` block the id is reachable across the whole
rule and is ``None`` while its branch is inactive, so other expressions can
react to the widget mounting and unmounting:

.. code-block:: kv

    <Editor@BoxLayout>:
        editing: False
        if self.editing:
            TextInput:
                id: field
        Button:
            disabled: field is None          # True until the TextInput exists

Because the id really is ``None`` while its branch is inactive, guard
attribute access accordingly: ``field.text if field else ''``. The usual kv
binding rules apply through a reactive id exactly as through a static one --
in particular the property you depend on must end the dotted chain
(``(field.text or '').strip()`` re-evaluates on typing; a bare
``field.text.strip()`` never does). Two branches of one chain may declare
the same id, and so may two complementary chains (``if cond:`` /
``if not cond:``): the id always points at the widget most recently mounted
under that name, and a branch tearing down only clears the id if it still
owns it.

In a ``for`` block the id is iteration-local, like an iteration-local value:
reachable only by that iteration's own content, never on ``root.ids``:

.. code-block:: kv

    for row in self.rows:
        CheckBox:
            id: box
        Label:
            text: 'on' if box.activated else 'off'

Such ids never appear in ``root.ids`` -- an entry that blinked in and out would
silently break anything bound to it.

Control statements inside canvas
********************************

``if`` and ``for`` also work *inside* a ``canvas`` (or ``canvas.before`` /
``canvas.after``) block, where they generate graphics instructions instead of
widgets -- data-driven drawing that reacts to its inputs:

.. code-block:: kv

    <Chart@Widget>:
        series: []
        selected: False
        canvas:
            Color:
                rgba: 1, 1, 1, 1
            for line in self.series:
                Line:
                    points: line.points
            if self.selected:
                Color:
                    rgba: 1, 0, 0, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

The instructions a block produces occupy the block's position among the
surrounding instructions, and are rebuilt when the condition or iterable
changes; instructions declared after the block stay after it. As with any kv
canvas, instruction property expressions update on the next
:meth:`Builder.sync <BuilderBase.sync>`. Blocks nest, so a ``for`` inside an
``if`` composes as expected.

A canvas ``for`` without a ``key:`` rebuilds its instructions wholesale on
change -- fine for cheap, stateless drawing. With a ``key:`` it reconciles per
iteration (keeping, moving or rebuilding instruction groups by key), so
textured or stateful instructions and large series are not destroyed and
re-uploaded on every change. Unlike the widget ``for``, a kept canvas
iteration whose loop values changed is rebuilt rather than re-dispatched --
instructions hold no user state worth preserving.

Restrictions
~~~~~~~~~~~~~

- Control statements cannot appear at the top level of a kv file.
- A property line binds to the nearest enclosing scope: host properties in an
  ``if`` at rule level, iteration-locals anywhere under a ``for`` (including
  inside an ``if`` nested in the ``for``), slot-scoped locals in a ``slot``
  definition. Event handlers and ``canvas`` are accepted only in ``if`` /
  ``elif`` / ``else`` blocks outside any ``for``; ``for`` bodies and ``slot``
  blocks take neither.
- Inside a ``canvas`` block only ``if`` and ``for`` are allowed (not ``slot`` or
  ``factory``); their bodies hold graphics instructions only, and a control
  statement may not be nested under an individual instruction.
- A ``key:`` line is valid only inside a ``for`` and must come before the
  block's child widgets; ``key`` is a reserved name there (an iteration-local
  cannot be called ``key``). Keys behave like dict keys and must be unique.
- ``id`` is allowed on widgets inside ``if`` / ``for`` blocks and inside
  explicit ``slot`` blocks (reactive); it is rejected directly on a control
  statement, on plain children implicitly routed into a slot, and inside
  ``factory`` blocks. A local and an ``id`` cannot share a name.
- Loop targets form their own scope and may shadow any name, including
  ``self`` / ``root`` / ``app`` and the metric helpers: within the block the
  loop variable wins over the global kv context. A child widget's own ``self``
  (and a handler's ``args``) still take precedence inside that widget, so
  shadowing ``self`` only affects the block's structure, not the children's
  expressions. Assignment expressions (``:=``) and ``async for`` are not allowed
  in headers, and a ``for`` header takes a single ``for ... in ...`` clause.
- A slot cannot be defined inside a ``for`` block; slot fills must be direct
  children of the widget instance (put an ``if`` *inside* the fill to make its
  content conditional), and a default ``slot:`` fill block cannot be mixed with
  plain children.
- ``factory`` requires a class expression and cannot be declared inside a
  ``canvas`` block.

Nothing is reserved beyond this: names like ``while`` or ``match`` in control
position are syntax errors today, so future statements can be added exactly as
additively as these were.

.. warning::

    The children built by control statements are managed. Manually *adding*
    children is safe -- appended widgets always land after the managed
    content. But manually removing or reordering the children of a widget
    that uses control statements (``clear_widgets()`` included) declares a
    second, competing owner of the same list: nothing raises and nothing
    leaks, but the insertion position of managed content becomes undefined
    from then on. Drive such changes through the bound properties instead.

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
                rgb: my_color if self.pressed else my_color_hl

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
