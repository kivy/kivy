Layouts
=======

Usage of layouts
----------------

Layouts are a special kind of widget designed to manage size and/or positions
of their direct children. Each layout intend to be specific to some use case,
but flexible enought to be useful in a large number of situations.

Layouts honors the size_hint and pos_hint properties of their children
differently.


Layout types
------------

BoxLayout:
 Arrange widgets in a side to side (either vertically or horizontally) manner,
 to fill all the place.
 size_hint of children can be used to change proportions allowed to each
 children, or set fixed size for some of them
 `pos_hint` not honored

 .. image:: ../images/boxlayout.gif

GridLayout:
  Arrange widgets in a grid. You must specifiy at least one dimension of the
  grid so kivy can compute the size of the elements and how to arrange them.

 `pos_hint` not honored

  .. image:: ../images/gridlayout.gif

StackLayout:
 Arrange widgets side to side, but with a set size in a dimension, without
 trying to make them fit the whole size, this is useful to have a set of
 chilgren of the same predefined size, side to side.
 `pos_hint` not honored

 .. image:: ../images/stacklayout.gif

AnchorLayout:
 A simple layout only caring about children position, allows to stick the
 children to a position relative to a border of the layout.
 `size_hint` not honored.

 .. image:: ../images/anchorlayout.gif

FloatLayout:
 Allow to place children to arbitrary places and size, either absolute or
 relative to the layout size. Default size_hint (1, 1) will make everychildren
 the same size as the whole layout, so you probably want to change this value
 if you have more than one child. You can set size_hint to (None, None) to use
 absolute size with `size`, this widget honors `pos_hint` too, which as a dict
 allowing to set position relatively to layout position.

 .. image:: ../images/floatlayout.gif

RelativeLayout:
 Behave just like FloatLayout, except children pos is relative to layout
 position, not screen.
