.. _widgets:

Widgets
=======

.. |size_hint| replace:: :attr:`~kivy.uix.widget.Widget.size_hint`
.. |pos_hint| replace:: :attr:`~kivy.uix.widget.Widget.pos_hint`
.. |size_hint_x| replace:: :attr:`~kivy.uix.widget.Widget.size_hint_x`
.. |size_hint_y| replace:: :attr:`~kivy.uix.widget.Widget.size_hint_y`
.. |pos| replace:: :attr:`~kivy.uix.widget.Widget.pos`
.. |size| replace:: :attr:`~kivy.uix.widget.Widget.size`
.. |width| replace:: :attr:`~kivy.uix.widget.Widget.width`
.. |height| replace:: :attr:`~kivy.uix.widget.Widget.height`
.. |children| replace:: :attr:`~kivy.uix.widget.Widget.children`
.. |parent| replace:: :attr:`~kivy.uix.widget.Widget.parent`
.. |x| replace:: :attr:`~kivy.uix.widget.Widget.x`
.. |y| replace:: :attr:`~kivy.uix.widget.Widget.y`
.. |left| replace:: :attr:`~kivy.uix.widget.Widget.left`
.. |top| replace:: :attr:`~kivy.uix.widget.Widget.top`
.. |center_x| replace:: :attr:`~kivy.uix.widget.Widget.center_x`
.. |center_y| replace:: :attr:`~kivy.uix.widget.Widget.center_y`
.. |orientation| replace:: :attr:`~kivy.uix.boxlayout.BoxLayout.orientation`
.. |Widget| replace:: :class:`~kivy.uix.widget.Widget`
.. |Button| replace:: :class:`~kivy.uix.button.Button`
.. |Canvas| replace:: :class:`~kivy.graphics.Canvas`
.. |ListProperty| replace:: :class:`~kivy.properties.ListProperty``
.. |ReferenceListProperty| replace:: :class:`~kivy.properties.ReferenceListProperty`
.. |Layout| replace:: :mod:`~kivy.uix.layout`
.. |RelativeLayout| replace:: :mod:`~kivy.uix.relativelayout`
.. |BoxLayout| replace:: :mod:`~kivy.uix.boxlayout`
.. |FloatLayout| replace:: :mod:`~kivy.uix.floatlayout`
.. |GridLayout| replace:: :mod:`~kivy.uix.gridlayout`
.. |StackLayout| replace:: :mod:`~kivy.uix.stacklayout`
.. |AnchorLayout| replace:: :mod:`~kivy.uix.anchorlayout`
.. |add_widget| replace:: :meth:`~kivy.uix.widget.Widget.add_widget`
.. |remove_widget| replace:: :meth:`~kivy.uix.widget.Widget.remove_widget`

Introduction to Widget
----------------------

A |Widget| can be termed as the base building block of GUI interfaces in Kivy.
It provides a |Canvas| that can be used to draw on screen. It receives events
and reacts to them. For a in depth explanation about the |Widget| class,
Look at the module documentation.

Manipulating the Widget tree
----------------------------

Widgets in kivy like in many other frameworks are organized in Trees, your
application has a `root widget`, which usually has |children| that can have
|children| of their own. Children of a widget are represented as the |children|
attribute which is a |ListProperty|.

The Widget Tree can be manipulated with the following methods:

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
    add a widget into the children list without adding its canvas to the
    graphics tree, the widget will be a child yes, but nothing will be drawn
    on the screen. More than that, you might have issues on further calls of
    add_widget, remove_widget and clear_widgets.


Traversing the tree
-------------------

The widget class has a :data:`~kivy.uix.widget.Widget.children` list property
that contains all the children. You can easily traverse the tree by doing::

    root = BoxLayout()
    # ... add widgets to root ...
    for child in root.children:
        print child

However, this must be used carefuly. If you intend to modify the children list
with one of the methods shown in the previous section, you must use a copy of
the list like this::

    for child in root.children[:]:
        # manipulate the tree. For example here, remove all widgets that have a
        # width < 100
        if child.width < 100:
            root.remove_widget(child)


Widgets don't influence the size/pos of their children by default, so the
|pos| attribute is the absolute position in screen co-ordinates (unless, of
course, you use the |RelativeLayout|, more on that later) and |size|, its
absolute size.

Widgets Z index
---------------
Widgets canvas/graphical representation is drawn based on their position in
the Widget Tree. I.E. The last widgets canvas is drawn last(on top of everything
else inside its parent). Add Widget takes a `index` parameter that you can use like so::

    root.add_widget(widget, index)

to try and manipulate the z-index of a child

Organize with Layouts
---------------------

|Layout| is a special kind of widget that controls the size and position of
its children. There are different kinds of layouts, allowing for different
automatic organization of their children. Layouts use |size_hint| and |pos_hint|
properties to determine the |size| and |pos| of their |children|.

**BoxLayout**:
Arranges widgets in a side to side (either vertically or horizontally) manner,
to fill all the place.
size_hint of children can be used to change proportions allowed to each
children, or set fixed size for some of them

.. only:: html

    .. image:: ../images/boxlayout.gif
        :align: left
    .. image:: ../images/gridlayout.gif
        :align: right
    .. image:: ../images/stacklayout.gif
        :align: left
    .. image:: ../images/anchorlayout.gif
        :align: right
    .. image:: ../images/floatlayout.gif

.. only:: latex

    .. image:: ../images/boxlayout.png
    .. image:: ../images/gridlayout.png
    .. image:: ../images/stacklayout.png
    .. image:: ../images/anchorlayout.png
    .. image:: ../images/floatlayout.png


**GridLayout**:
Arranges widgets in a grid. You must specifiy at least one dimension of the
grid so kivy can compute the size of the elements and how to arrange them.

**StackLayout**:
Arranges widgets side to side, but with a set size in a dimension, without
trying to make them fit the whole size, this is useful to have a set of
chilgren of the same predefined size, side to side.

**AnchorLayout**:
A simple layout only caring about children position, allows to stick the
children to a position relative to a border of the layout.
`size_hint` not honored.

**FloatLayout**:
Allow to place children to arbitrary places and size, either absolute or
relative to the layout size. Default size_hint (1, 1) will make everychildren
the same size as the whole layout, so you probably want to change this value
if you have more than one child. You can set size_hint to (None, None) to use
absolute size with `size`, this widget honors `pos_hint` too, which as a dict
allowing to set position relatively to layout position.

**RelativeLayout**:
Behave just like FloatLayout, except children pos is relative to layout
position, not screen.

Look at the documentation of the various Layouts to get a in-depth
understanding.
|size_hint| and |pos_hint|:

- |FloatLayout|
- |BoxLayout|
- |GridLayout|
- |StackLayout|
- |RelativeLayout|
- |AnchorLayout|


|size_hint| is a |ReferenceListProperty| of
|size_hint_x| and |size_hint_y|. It excepts values from `0` to `1` or `None`
and defaults to `(1, 1)`. This signifies that if the widget is in a layout,
the layout will allocate it as much place as possible in both directions
(relative to the layouts size).

Setting |size_hint| to (0.5, 0.8) for example, will make the widget 50% the
width and 80% the height of available size for the |widget| inside a |layout|.

Consider the following example:

.. code-block:: kv

    BoxLayout:
        Button:
            text: 'Button 1'
            # default size_hint is 1, 1, we don't need to specify it explicitly
            # however it's provided here to make things clear
            size_hint: 1, 1

load kivy catalog::

    cd $KIVYDIR/examples/demo/kivycatalog
    python main.py

Replace $KIVYDIR with the directory of your installation of Kivy. Click on the
button labeled `Box Layout` from the left. Now paste the code from above into
the Editor on the right.

.. image:: images/size_hint[B].jpg

As you can see from the image above the `Button` takes up 100% of the layouts
|size|.

Changing the |size_hint_x|/|size_hint_y| to .5 will make the |widget| take 50%
of the |layout| |width|/|height|.

.. image:: images/size_hint[b_].jpg

You can see here that although we specify |size_hint_x| and |size_hint_y| both
to be .5, only |size_hint_x| seems to be honored that's because |BoxLayout|
controls the |size_hint_y| when |orientation| is `vertical` and |size_hint_x|
when 'horizontal'. That means the controlled side's size is calculated depending
upon the total No. of |children| in the |BoxLayout|. Here that's one child with
|size_hint_y| controlled so, .5/.5 = 1. Thus the widget takes 100% of the parent
layout's height.

Let's add another |Button| to the |layout| and see what happens.

.. image:: images/size_hint[bb].jpg

|BoxLayout| by its very nature devides the available space up between its
|children| equally, in our case that's 50-50 as we have two |children|. Let's
use size_hint on one of the children and see at the results.

.. image:: images/size_hint[oB].jpg

If a child specifies |size_hint|, that specifies how much space the |Widget|
will take out of the |size| allotted to it by the |BoxLayout|. In our case the
first |Button| specifies .5 for |size_hint_x|. The space for the widget is
calculated like so::

    first child's size_hint devided by
    first child's size_hint + second child's size_hint + ...n(no of children)
    
    .5/(.5+1) = .333...


The rest of the BoxLayouts |width| is divided among the rest of the |children|.
In our case that means the second |Button| takes up 66.66% of the |layout|
|width|.

Go ahead and experiment with |size_hint| to get comfortable with it.

If you want to control the absolute |size| of a |Widget|, you can set
|size_hint_x|/|size_hint_y| or both to `None` so that widgets |width| and or
|height| attributes will be honored.

|pos_hint| is a dict, which defaults to empty, As for |size_hint|, different
Layouts honor |pos_hint| differently, but you can add values to any of the |pos|
attributes (|x|, |y|, |left|, |top|, |center_x|, |center_y|) to have the
|Widget| positioned relatively to its |parent|.

Lets experiment with the following code in kivycatalog to understand |pos_hint|
visually:

.. code-block:: kv

    FloatLayout:
        Button:
            text: "We Will"
            pos: 100, 100
            size_hint: .2, .4
        Button:
            text: "Wee Wiill"
            pos: 200, 200
            size_hint: .4, .2

        Button:
            text: "ROCK YOU!!"
            pos_hint: {'x': .3, 'y': .6}
            size_hint: .5, .2

Should give us something that looks like this.

.. image:: images/pos_hint.jpg

You should experiment further with |pos_hint| by changing the values to
understand the effect they have on the widgets position.

Adding a Background to a Layout
-------------------------------

One of the frequently asked questions about layouts is:

    "How to add a background image/color/video/... to a Layout"

Layouts by their nature have no visual representation, i.e. they have no canvas
instructions by default. However you can add instructions to the Layouts canvas.

To add a color to the background of a **layouts Instance**

In Python::

    with layout_instance.canvas.before:
        Color(rgba(0, 1, 0, 1)) # green; colors range from 0-1 instead of 0-255
        self.rect = Rectangle(
                                size=layout_instance.size,
                                pos=layout_instance.pos)

Unfortunately this will only draw a rectangle at the layouts initial position
and size.To make sure the rect is drawn inside the layout if layout size/pos
changes we need to listen to any changes and update the Rectangles size and pos
like so::

    # listen to size and position changes
    layout_instance.bind(
                        size=self._update_rect,
                        pos=self._update_rect)
    
    ...
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

In kv:

.. code-block:: kv

    ...
    ...
    FloatLayout:
        canvas.before:
            Color:
                rgba: 0, 1, 0, 1
            Rectangle:
                # self here refers to the widget i.e BoxLayout
                pos: self.pos
                size: self.size

That's it the binding is implicit. kv language in the last two lines updates the
values |pos| and |size| of the rectangle when the |pos| of the |FloatLayout|
changes. QED.

Now Let's put the snippets above into the shell of Kivy App.
Pure Python way::

    from kivy.app import App
    from kivy.graphics import Color, Rectangle
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.button import Button


    class RootWidget(FloatLayout):

        def __init__(self, **kwargs):
            # make sure we aren't overriding any important functionality
            super(RootWidget, self).__init__(**kwargs)

            with self.canvas.before:
                Color(0, 1, 0, 1) # green; colors range from 0-1 instead of 0-255
                self.rect = Rectangle(
                                size=self.size,
                                pos=self.pos)

            # let's add a Widgetto this layout
            self.add_widget(
                            Button( text="Hello World",
                                    size_hint= (.5, .5),
                                    pos_hint={'center_x':.5,
                                            'center_y':.5}))

            self.bind(
                        size=self._update_rect,
                        pos=self._update_rect)

        def _update_rect(self, instance, value):
            self.rect.pos = instance.pos
            self.rect.size = instance.size


    class MainApp(App):

        def build(self):
            return RootWidget()

    if __name__ == '__main__':
        MainApp().run()

Using KV Language::

    from kivy.app import App
    from kivy.uix.floatlayout import FloatLayout
    from kivy.lang import Builder


    Builder.load_string('''
    <RootWidget>
        canvas.before:
            Color:
                rgba: 0, 1, 0, 1
            Rectangle:
                # self here refers to the widget i.e BoxLayout
                pos: self.pos
                size: self.size
        Button:
            text: 'Hello World!!'
            size_hint: .5, .5
            pos_hint: {'center_x':.5, 'center_y': .5}
    ''')

    class RootWidget(FloatLayout):
        pass


    class MainApp(App):

        def build(self):
            return RootWidget()

    if __name__ == '__main__':
        MainApp().run()

Isn't this a lot simpler?

Both of the Apps should look something like this

.. image:: images/layout_background.png

To add a color to the background of a **custom layouts rule/class**

To add a color to the background of a **layout globally**

Now Let's have some fun and add a **Image to the background**

a bit Advanced Topics::

    How about a **Animated background**?

    Blitt custom data to the background

Nesting Layouts
---------------

Yes! not only can you nest Layouts, it is actually quite fun to seee how extensible nesting Layouts is

Size and position metrics
-------------------------

.. |Transitions| replace:: :class:`~kivy.uix.screenmanager.TransitionBase`
.. |ScreenManager| replace:: :class:`~kivy.uix.screenmanager.ScreenManager`
.. |Screen| replace:: :class:`~kivy.uix.screenmanager.Screen`
.. |screen| replace:: :mod:`~kivy.modules.screen`
.. |metrics| replace:: :mod:`~kivy.metrics`
.. |pt| replace:: :attr:`~kivy.metrics.pt`
.. |mm| replace:: :attr:`~kivy.metrics.mm`
.. |cm| replace:: :attr:`~kivy.metrics.cm`
.. |in| replace:: :attr:`~kivy.metrics.in`
.. |dp| replace:: :attr:`~kivy.metrics.dp`
.. |sp| replace:: :attr:`~kivy.metrics.sp`

Kivys default unit for length is the pixel, all sizes and positions are
expressed in it by default. You can express them in other units, which is
useful to achieve better consistency across devices (they get converted to the
size in pixel automatically).

All available units are |pt|, |mm|, |cm|, |in|, |dp| and |sp|, you can see
about their usage in the |metrics| documentation.

On a related note, you can see the |screen| usage to simulate various devices
screens for your application.

Screen Separation with Screen Manager
-------------------------------------

If your application is composed of various screens, you likely want an easy
way to navigate from one |Screen| to another. Fortunately, there is
|ScreenManager| class, that allows you to define screens separately, and to set
the |Transitions| from one to another.
