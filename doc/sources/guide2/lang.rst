.. _lang:

Kv language
===========

Concept behind the language
---------------------------

As your applications grow more complexes, you will notice that construction of
widget trees and explicit declaration of bindings, become verbose, and hard to
maintain. Thus, a language more suited to this need has been developed.

The KV language (sometime called kvlang, or kivy language), allows you to
create your widget tree in a very declarative way, and to bind properties of
widget to each other, or to callbacks very naturally, you allows very fast
prototyping and agile changes to your UI, and a good separation between the
logic of your application, and the look it have.

How to load kv
--------------

There are two ays to load kv code into your application:

- By name convention:
  Kivy looks if there is a kv file with the same name as your App class, lowercase,
  minus "app" if it endswith 'app', e.g: MyApp -> my.kv. If this file define a
  root rule it will be attached to the App's `root` attribute and used as the
  application widget tree.

- :obj:`kivy.lang.Builder`:
  you can tell directly kivy to load a string or a file, if it defines a root
  widget, it will be returned by the method::

    Builder.load_file('path/to/file.kv')

  or::

    Builder.load_string(kv_string)
  
Rule context
------------

A kv source is constituted from `rules`, which are used to describe the content
of a Widget, you can have one `root` rule, and any number of `class` rules.

The `root` rule is declared by declaring the class of your root widget, without
any indentation, followed by `:` and will be set as the `root` attribute of the
App instance::

    Widget:

A `class` rule, which define how any instance of that widget class will be created
is declared by declaring the name of the class, between chevrons, followed by `:`::

    <MyWidget>:

Rules use indentation for delimitation, as python, indentation should be of
four spaces per level, like the python good practice recommendations.

There are three keywords specific to kv languages:

- `app`: always refer to the instance of your application.
- `root`: always refer to the base widget of the current rule.
- `self`: always refer to the current widget.

Special syntaxes
----------------

There are two special syntax to define values for the whole kv context:

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
this child inside the rule::

    MyRootWidget:
        BoxLayout:
            Button:
            Button:

The example above define that our root widget, which is an instance of `MyRootWidget`
has a child, which is an instance of the :class:`kivy.uix.boxlayout.BoxLayout` and that
this child has itself two child, instances of the :class:`kivy.uix.button.Button` class.

A python equivalent of this code could be::

    root = MyRootWidget()
    box = BoxLayout()
    box.add_widget(Button())
    box.add_widget(Button())
    root.add_widget(box)

Which you way find maybe less nice, both to read and to write.

Of course, in python, you can pass keyword arguments to your widgets at
creation, to specify their behaviour, for example, to set the number of columns
of a :mod:`kivy.uix.gridlayout`, we would do::

    grid = GridLayout(cols=3)

To do the same thing in kv, you can set properties of the child widget directly
in the rule::

    GridLayout:
        cols: 3

The value is evaluated as a python expression, and all the properties used in
the expression will be observed, that means that if you had something like this
in python (this assume `self` is a widget with a `data`
:class:`kivy.property.ListProperty`)::

    grid = GridLayout(cols=len(self.data))
    self.bind(data=grid.setter('cols'))

To have your display updated when your data change, you can now have just::

    GridLayout:
        cols: len(root.data)

Extend canvas
-------------

Kv lang can be used to define the canvas instructions of your widget too::

    MyWidget:
        canvas:
            Color:
                rgba: 1, .3, .8, .5
            Line:
                points: zip(self.data.x, self.data.y)

And yes, they get updated too if properties values change.

Of course you can use `canvas.before` and `canvas.after`.

Templating
----------
