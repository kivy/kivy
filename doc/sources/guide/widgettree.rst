.. _widgettree:

Widget tree
===========

Like most of GUI toolkit, Kivy have a tree for handling a hierarchy of widgets.
The top level widget is called "root". Each widget can be connected to others
widgets, as a parent or as a child.

You cannot add into the widget tree something that is not a
:class:`~kivy.uix.widget.Widget` subclass.

Manipulating the tree
---------------------

The tree can be manipulated with 3 methods:

- :meth:`~kivy.uix.widget.Widget.add_widget`: add a widget as a child
- :meth:`~kivy.uix.widget.Widget.remove_widget`: remove a widget from the
  children list
- :meth:`~kivy.uix.widget.Widget.clear_widgets`: remove all children from a
  widget

For example, if you want to add a button inside a boxlayout, you can do::

    layout = BoxLayout(padding=10)
    button = Button(text='My first button')
    layout.add_widget(button)

Now, the button parent will be set to layout, and layout will have button in his
children list. To remove the button from the layout::

    layout.remove_widget(button)

The button parent will be set to None, and layout will remove button from his
children list.

If you want to clear all the children inside a widget, use
:meth:`~kivy.uix.widget.Widget.clear_widgets` method::

    layout.clear_widgets()

.. warning::

    Never manipulate the children list yourself, if you don't know what you are
    doing. The widget tree is associated to a graphic tree. For example, if you
    add a widget into the children list without adding his canvas to the
    graphics tree, the widget will be a children yes, but nothing will be drawed
    on the screen. More than that, you might have issue on further call of
    add_widget, remove_widget and clear_widgets.


Traversing the tree
-------------------

The widget class have a :data:`~kivy.uix.widget.Widget.children` list property
that contain all the children. You can easily traverse the tree by doing ::

    root = BoxLayout()
    # ... add widgets to root ...
    for child in root.children:
        print child

However, this must be used carefuly. If you intend to modify the children list
with one of the methods showed in the previous section, you must use a copy of
the list like this::

    for child in root.children[:]:
        # manipulate the tree. For example here, remove all widget that have a
        # width < 100
        if child.width < 100:
            root.remove_widget(child)
