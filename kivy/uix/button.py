'''
Button
======

.. image:: images/button.jpg
    :align: right

The :class:`Button` is a :class:`~kivy.uix.label.Label` with associated actions
that are triggered when the button is pressed (or released after a click/touch).
To configure the button, you can use the same properties that you can use for
the Label class::

    button = Button(text='Hello world', font_size=14)

To attach a callback when the button is pressed (clicked/touched), use
:class:`~kivy.uix.widget.Widget.bind`::

    def callback(instance):
        print('The button <%s> is being pressed' % instance.text)

    btn1 = Button(text='Hello world 1')
    btn1.bind(on_press=callback)
    btn2 = Button(text='Hello world 2')
    btn2.bind(on_press=callback)

If you want to be notified every time the button state changes, you can bind
to the :data:`Button.state` property::

    def callback(instance, value):
        print('My button <%s> state is <%s>' % (instance, value))
    btn1 = Button(text='Hello world 1')
    btn1.bind(state=callback)

'''

__all__ = ('Button', )

from kivy.uix.label import Label
from kivy.properties import StringProperty, ListProperty
from kivy.uix.behaviors import ButtonBehavior


class Button(ButtonBehavior, Label):
    '''Button class, see module documentation for more information.

    .. versionchanged:: 1.8.0

        The behavior / logic of the button has been moved to
        :class:`~kivy.uix.behaviors.ButtonBehaviors`.

    '''

    background_color = ListProperty([1, 1, 1, 1])
    '''Background color, in the format (r, g, b, a).

    .. versionadded:: 1.0.8

    The :data:`background_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [1, 1, 1, 1].
    '''

    background_normal = StringProperty(
        'atlas://data/images/defaulttheme/button')
    '''Background image of the button used for the default graphical
    representation when the button is not pressed.

    .. versionadded:: 1.0.4

    :data:`background_normal` is a :class:`~kivy.properties.StringProperty`
    and defaults to 'atlas://data/images/defaulttheme/button'.
    '''

    background_down = StringProperty(
        'atlas://data/images/defaulttheme/button_pressed')
    '''Background image of the button used for the default graphical
    representation when the button is pressed.

    .. versionadded:: 1.0.4

    :data:`background_down` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/button_pressed'.
    '''

    background_disabled_normal = StringProperty(
        'atlas://data/images/defaulttheme/button_disabled')
    '''Background image of the button used for the default graphical
    representation when the button is not pressed.

    .. versionadded:: 1.8.0

    :data:`background_normal` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/button_disabled'.
    '''

    background_disabled_down = StringProperty(
        'atlas://data/images/defaulttheme/button_disabled_pressed')
    '''Background image of the button used for the default graphical
    representation when the button is pressed.

    .. versionadded:: 1.8.0

    :data:`background_down` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/button_disabled_pressed'.
    '''

    border = ListProperty([16, 16, 16, 16])
    '''Border used for :class:`~kivy.graphics.vertex_instructions.BorderImage`
    graphics instruction. Used with :data:`background_normal` and
    :data:`background_down`. Can be used for custom backgrounds.

    It must be a list of four values: (top, right, bottom, left). Read the
    BorderImage instruction for more information about how to use it.

    :data:`border` is a :class:`~kivy.properties.ListProperty` and defaults to
    (16, 16, 16, 16)
    '''

