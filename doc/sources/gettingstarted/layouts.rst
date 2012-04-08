Layouts
--------

.. container:: title

    Arranging Your Widgets

Layouts are used to arrange widgets in a perticular manner. ::

    AnchorLayout:   widgets can be anchored to 'top', 'bottom', 'left', 'right', 'center'
    BoxLayout:      widgets arranged in a box either in 'vertical' or 'horizontal' orientation
    FloatLayout:    Widgets are essentially unrestricted
    GridLayout:     widgets arranged in a grid defined by `rows` and `cols` properties
    StackLayout:    widgets are stacked in `lr-tb` (left to right then top to bottom) or `tb-lr`

**Size_hint**: defines the size of a widget in parent space in percentages, values restricted to range 0 - 1 i.e. 0.01 = 1% and 1. = 100%.
**pos_hint**: is used to place the widget relative to the parent.

size_hint or pos_hint are used to calculate widget's size and position only if the value/s are not set to None.
However one can set these to None and provide direct values in screen coordinates.

For a detailed look at how you can arrange widgets using layouts look in
`AnchorLayout <http://kivy.org/docs/api-kivy.uix.anchorlayout.html>`_
`BoxLayout <http://kivy.org/docs/api-kivy.uix.boxlayout.html>`_
`FloatLayout <http://kivy.org/docs/api-kivy.uix.floatlayout.html>`_
`GridLayout <http://kivy.org/docs/api-kivy.uix.gridlayout.html>`_
`StackLayout <http://kivy.org/docs/api-kivy.uix.stacklayout.html>`_