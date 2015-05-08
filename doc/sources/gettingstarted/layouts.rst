Layouts
--------

Layouts are containers used to arrange widgets in a particular manner.

    :mod:`AnchorLayout <kivy.uix.anchorlayout>`:
        Widgets can be anchored to the 'top', 'bottom', 'left',
        'right' or 'center'.
    :mod:`BoxLayout <kivy.uix.boxlayout>`:
        Widgets are arranged sequentially, in either a 'vertical'
        or a 'horizontal' orientation.
    :mod:`FloatLayout <kivy.uix.floatlayout>`:
        Widgets are essentially unrestricted.
    :mod:`RelativeLayout <kivy.uix.relativelayout>`:
        Child widgets are positioned relative to the layout.
    :mod:`GridLayout <kivy.uix.gridlayout>`:
        Widgets are arranged in a grid defined by the `rows` and
        `cols` properties.
    :mod:`PageLayout <kivy.uix.pagelayout>`:
        Used to create simple multi-page layouts, in a way that
        allows easy flipping from one page to another using
        borders.
    :mod:`ScatterLayout <kivy.uix.scatterlayout>`:
        Widgets are positioned similarly to a RelativeLayout, but
        they can be translated, rotate and scaled.
    :mod:`StackLayout <kivy.uix.stacklayout>`:
        Widgets are stacked in a `lr-tb` (left to right then top to
        bottom) or `tb-lr` order.

When you add a widget to a layout, the following properties are used to
determine the widget's size and position, depending on the type of layout:

    **size_hint**: defines the size of a widget in its parent space as a percentage.
    Values are restricted to the range 0.0 - 1.0 i.e. 0.01 = 1% and 1. = 100%.

    **pos_hint**: is used to place the widget relative to the parent.

The **size_hint** and **pos_hint** are used to calculate a widget's size and
position only if the value(s) are not set to ``None``. If you set these values to
``None``, the layout will not position/size the widget and you can specify the
values (x, y, width, height) directly in screen coordinates.
