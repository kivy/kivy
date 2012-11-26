.. _widgets:

Widgets
=======

Introduction to Widget
----------------------

A `:cls:kivy.uix.widget.Widget` is the basic component of the interface,
it can display things at places, and recieve touch (and other) events,
and react to them. It's representation and behaviour.

Manipulating the Widget tree
----------------------------

Widgets are organized in Trees, your application usually
have a root widget, which have children, which can
have children on their own. Childrens of a widget are
represented as a :cls:`kivy.properties.ListProperty`
:attr:`kivy.uix.widget.Widget.children`. The way to add a children to a
widget is to call :meth:`kivy.uix.widget.Widget.add_widget`, likely, to
remove a widget, you use :meth:`kivy.uix.widget.Widget.remove_widget`.

Organize with Layouts
---------------------

Layouts are a special kind of widget that allows automatic control of the size
and position of their children. There are different kind of layouts, allowing
for different automatic organisation. A common caracteristic of layouts is that
they use (even if differently) of the
:attr:`kivy.uix.widget.Widget.size_hint` and
:attr:`kivy.uix.widget.Widget.pos_hint` properties. Those properties allow to
define size and pos of the widget relatively to the parent layout.

Seperate with Screen Manager
----------------------------

If your application is composed of various screens, you likely want an
easy way to navigate from one to another, fortunately, there is the
:cls:`kivy.uix.screenmanager.ScreenManager` class, that allows you
to define screens separatly, and to set the transitions from one to
another.
