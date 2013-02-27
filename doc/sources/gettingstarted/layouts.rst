Layouts
--------

.. container:: title

    Arranging Your Widgetsx

Layouts are used to arrange widgets in a perticular manner::

    AnchorLayout:   widgets can be anchored to the 'top', 'bottom', 'left', 'right' or 'center'.
    BoxLayout:      widgets are arranged in a box in either 'vertical' or 'horizontal' orientation.
    FloatLayout:    widgets are essentially unrestricted.
    RelativeLayout: Child widgets are positioned relative to the layout.
    GridLayout:     widgets are arranged in a grid defined by `rows` and `cols` properties.
    StackLayout:    widgets are stacked in `lr-tb` (left to right then top to bottom) or `tb-lr` order.

**Size_hint**: defines the size of a widget in parent space as a percentage. Values are restricted to 
the range 0.0 - 1.0 i.e. 0.01 = 1% and 1. = 100%.
**pos_hint**: is used to place the widget relative to the parent.

*size_hint* and *pos_hint* are used to calculate the widget's size and position only if the value/s are not set to *None*.
One can, however, set these to *None* and provide direct values in screen coordinates.

For a detailed look at how you can arrange widgets using layouts look in
:mod:`AnchorLayout <kivy.uix.anchorlayout>`
:mod:`BoxLayout <kivy.uix.boxlayout>`
:mod:`FloatLayout <kivy.uix.floatlayout>`
:mod:`GridLayout <kivy.uix.gridlayout>`
:mod:`StackLayout <kivy.uix.stacklayout>`
:mod:`RelativeLayout <kivy.uix.relativelayout>`
