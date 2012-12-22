.. _widgets:

Widgets
=======

Introduction to Widget
----------------------

A :class:`kivy.uix.widget.Widget` is the basic component of the interface, it
can display things at places, and receive events (touches and others), and
react to them. It has a representation and a behaviour.

Manipulating the Widget tree
----------------------------

Widgets are organized in Trees, your application have a root widget, which
usually have children, which can have children on their own. Children of a
widget are represented as the :attr:`kivy.uix.widget.Widget.children`
:class:`kivy.properties.ListProperty`. The way to add a children to a widget is
to call :meth:`kivy.uix.widget.Widget.add_widget`, likely, to remove a widget
from its parent, you use :meth:`kivy.uix.widget.Widget.remove_widget`.

Widget don't influence the size/pos of their children by default, so the
:attr:`~kivy.uix.widget.Widget.pos` attribute is the absolute position of the
widget (unless, of course, you use the :mod:`~kivy.uix.relativelayout`, more on
that later) and size, its absolute size (ditto). 


Organize with Layouts
---------------------

Layouts are a special kind of widget that allows automatic control of the size
and position of their children . There are different kind of layouts,
allowing for different automatic organisation. A common characteristic of
layouts is that they use (even if differently) of the
:attr:`kivy.uix.widget.Widget.size_hint` and
:attr:`kivy.uix.widget.Widget.pos_hint` properties. Those properties allow to
define size and position of the widget relatively to the parent layout.

Look at the documentation of the various Layouts to see to which situation each
one applies:

- :mod:`kivy.uix.floatlayout`
- :mod:`kivy.uix.boxlayout`
- :mod:`kivy.uix.gridlayout`
- :mod:`kivy.uix.stacklayout`
- :mod:`kivy.uix.relativelayout`
- :mod:`kivy.uix.anchorlayout`

:attr:`kivy.uix.widget.Widget.size_hint` default value is (1, 1), this means
that if the widget is in a layout, the layout will allows it as much place as
possible, in both direction (relative to the layout's size), if you want to
change that, you can either change these values to different ones, (0.5, 0.8)
for example, will make the widget 50% the width and 80% the height of what it
would have been with the default value, if you want to control the size of the
widget absolutely, you can desactivate size_hint in either or both direction,
using None for the directions you want to desactivate (e.g: (None, None) for
both direction).

:attr:`kivy.uix.widget.Widget.pos_hint` is a dict, which defaults to empty, As
for size_hint, different Layouts honors pos_hint differently, but you can add
values to any of the pos attributes (x, y, left, top, center_x, center_y) to
have the widget positioned relatively to its parent.

Separate with Screen Manager
----------------------------

If your application is composed of various screens, you likely want an easy way
to navigate from one to another, fortunately, there is the
:class:`kivy.uix.screenmanager.ScreenManager` class, that allows you to define
screens separately, and to set the transitions from one to another.
