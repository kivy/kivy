.. _lang:

Kv language
===========

Concept behind the language
---------------------------

As your application grow more complex, it's common that the construction of
widget trees and explicit declaration of bindings, becomes verbose and hard to
maintain. The `KV` Language is a attempt to overcome these short-comings.

The `KV` language (sometimes called kvlang, or kivy language), allows you to
create your widget tree in a declarative way and to bind widget properties
to each other or to callbacks in a natural manner. It allows for very fast
prototyping and agile changes to your UI. It also facilitates a good
separation between the logic of your application and it's User Interface.

How to load KV
--------------

There are two ways to load Kv code into your application:
- By name convention:

  Kivy looks if there is a Kv file with the same name as your App class in 
  lowercase,  minus "App" if it ends with 'App'. E.g::
  
    MyApp -> my.kv.

  If this file defines a `Root Widget` it will be attached to the App's `root` 
  attribute and used as the base of the application widget tree.

- :obj:`~kivy.lang.Builder`:
  you can tell kivy to directly load a string or a file. If this string or file
  defines a root widget, it will be returned by the method::

    Builder.load_file('path/to/file.kv')

  or::

    Builder.load_string(kv_string)
  
Rule context
------------

A Kv source constitutes of `rules`, which are used to describe the content
of a Widget, you can have one `root` rule, and any number of `class` or
`template` rules.

The `root` rule is declared by declaring the class of your root widget, without
any indentation, followed by `:` and will be set as the `root` attribute of the
App instance::

    Widget:

A `class` rule, which defines how any instance of that widget class will be
graphically represented is declared by declaring the name of the class, between
`< >`, followed by `:`::

    <MyWidget>:

Rules use indentation for delimitation, as python, indentation should be of
four spaces per level, like the python good practice recommendations.

There are three keywords specific to Kv language:

- `app`: always refers to the instance of your application.
- `root`: refers to the base widget/template in the current rule
- `self`: always refer to the current widget

Special syntaxes
----------------

There are two special syntax to define values for the whole Kv context:

To import something from python::

    #:import name x.y.z

Is equivalent to::

    from x.y import z as name

in python.

To set a global value::

    #:set name value

Is equivalent to::

    name = value

in python.

Instantiate children
--------------------

To declare the widget has a child widget, instance of some class, just declare
this child inside the rule:

.. code-block:: kv

    MyRootWidget:
        BoxLayout:
            Button:
            Button:

The example above defines that our root widget, an instance of `MyRootWidget`
has a child; an instance of the :class:`~kivy.uix.boxlayout.BoxLayout` which
has two children, instances of the :class:`~kivy.uix.button.Button` class.

A python equivalent of this code could be:

.. code-block:: python

    root = MyRootWidget()
    box = BoxLayout()
    box.add_widget(Button())
    box.add_widget(Button())
    root.add_widget(box)

Which you way find maybe less nice, both to read and to write.

Of course, in python, you can pass keyword arguments to your widgets at
creation, to specify their behaviour, for example, to set the number of columns
of a :mod:`~kivy.uix.gridlayout`, we would do::

    grid = GridLayout(cols=3)

To do the same thing in kv, you can set properties of the child widget directly
in the rule:

.. code-block:: kv

    GridLayout:
        cols: 3

The value is evaluated as a python expression, and all the properties used in
the expression will be observed, that means that if you had something like this
in python (this assume `self` is a widget with a `data`
:class:`~kivy.property.ListProperty`)::

    grid = GridLayout(cols=len(self.data))
    self.bind(data=grid.setter('cols'))

To have your display updated when your data change, you can now have just:

.. code-block:: kv

    GridLayout:
        cols: len(root.data)

Event Bindings
--------------

You can bind to events in Kv using the ":" syntax, that is, associating a
callback to an event:

.. code-block:: kv

    Widget:
        on_size: my_callback()

You can pass the values dispatched by the signal using the `args` keyword:

.. code-block:: kv

    TextInput:
        on_text: app.search(args[1])

More complex expressions can be used, like:

.. code-block:: kv

    pos: self.center_x - self.texture_size[0] / 2., self.center_y - self.texture_size[1] / 2.

This expression listens for a change in ``center_x``, ``center_y``,
and ``texture_size``. If one of them is changing, the expression will be
re-evaluated, and update the ``pos`` field.

You can also handle ``on_`` events inside your kv language.
For example the TextInput class has a ``focus`` property whose auto-generated
``on_focus`` event can be accessed inside the kv language like so:

.. code-block:: kv

    TextInput:
        on_focus: print args 


Extend canvas
-------------

Kv lang can be used to define the canvas instructions of your widget too:

.. code-block:: kv

    MyWidget:
        canvas:
            Color:
                rgba: 1, .3, .8, .5
            Line:
                points: zip(self.data.x, self.data.y)

And yes, they get updated too if properties values change.

Of course you can use `canvas.before` and `canvas.after`.

Referencing Widgets
-------------------

In a widget tree there is often a need to access/reference other widgets.
Kv Language provides a way to do this using id's. Think of them as class
level variables that can only be used in the Kv language. Consider the
following:

.. code-block:: kv

    <MyFirstWidget>:
        Button:
            id: f_but
        TextInput:
            text: f_but.state

    <MySecondWidget>:
        Button:
            id:s_but
        TextInput:
            text: s_but.state

id's are limited in scope to the rule they are declared in so, in the
code above `s_but` can not be accessed outside the <MySecondWidget>
rule.

Accessing Widgets defined inside Kv lang in your python code
------------------------------------------------------------

Consider the code below in my.kv:

.. code-block:: kv

    <MyFirstWidget>:
        # both these variable don't have to be the same name and this doesn't
        # lead to a issue with uniqueness as id's are accessible only in kv.
        txt_inpt: txt_inpt
        Button:
            id: f_but
        TextInput:
            id: txt_inpt
            text: f_but.state
            on_text: root.check_status(f_but)


In myapp.py:

.. code-block:: py

    ...
    class MyFirstWidget(BoxLayout):
    
        txt_inpt = ObjectProperty(None)
    
        def check_status(self, btn):
            print ('button state is: {state}'.format(state=btn.state))
            print ('text input text is: {txt}'.format(txt=self.txt_inpt))
    ...

`txt_inpt` is defined as a :class:`~kivy.properties.ObjectProperty` initialized
to `None` inside the Class.::

    txt_inpt = ObjectProperty(None)

At this point self.txt_inpt is `None`. In Kv lang this property is updated to
hold the instance of the :class:`~kivy.uix.TextInput` referenced by the id
`txt_inpt`.::

    txt_inpt: txt_inpt

Thus; self.txt_inpt from this point onwards holds the instance to the widget
referenced by the id `txt_input` and can be used anywhere in the class like in
the function `check_status`. In contrast to this method you could also just pass
the `id` to the function that needs to use it, like in case of `f_but` in the
code above.


Templates
---------
Consider the code below:

.. code-block:: kv

    <MyWidget>:
        Button:
            text:
                "Hello world, watch this text wrap inside the button"
            text_size: self.size
            font_size: '25sp'
            markup: True
        Button:
            text:
                "Even absolute is relative to itself"
            text_size: self.size
            font_size: '25sp'
            markup: True
        Button:
            text:
                "repeating the same thing over and over in a comp = fail"
            text_size: self.size
            font_size: '25sp'
            markup: True
        Button:

Instead of having to repeat the same values for every button, we can just use a
template instead, like so:

.. code-block:: kv

    [MyBigButt@Button]:
        text: ctx.text if hasattr(ctx, 'text') else ''
        text_size: self.size
        font_size: '25sp'
        markup: True
    
    <MyWidget>:
        MyBigButt:
            text: "Hello world, watch this text wrap inside the button"
        MyBigButt:
            text: "Even absolute is relative to itself"
        MyBigButt:
            text: "repeating the same thing over and over in a comp = fail"
        MyBigButt:

`ctx` is a keyword inside a template that can be used to access the individual
attributes of each instance of this template.
