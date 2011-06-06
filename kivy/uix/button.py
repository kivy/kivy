'''
Button
======

.. image:: images/button.jpg
    :align: right

The button is a :class:`~kivy.uix.label.Label` with an action associated to it
that is triggered when the button is pressed (or released after a click/touch).
To configure the button, you can use the same properties that you can use for
the Label class::

    button = Button(text='Hello world', font_size=14)

Attaching a callback when the button is pressed (clicked/touched) ::

    def callback(instance):
        print 'The button <%s> is being pressed' % instance.text

    btn1 = Button(text='Hello world 1')
    btn1.bind(on_press=callback)
    btn2 = Button(text='Hello world 2')
    btn2.bind(on_press=callback)

If you want to be notified every time the button state changes, you can attach
to the :data:`Button.state` property ::

    def callback(instance, value):
        print 'My button <%s> state is <%s>' % (instance, value)
    btn1 = Button(text='Hello world 1')
    btn1.bind(state=callback)

'''

__all__ = ('Button', )

from kivy.uix.label import Label
from kivy.properties import OptionProperty, StringProperty


class Button(Label):
    '''Button class, see module documentation for more information.

    :Events:
        `on_press`
            Fired when the button is pressed.
        `on_release`
            Fired when the button is released (i.e., the touch/click that
            pressed the button goes away).
    '''

    state = OptionProperty('normal', options=('normal', 'down'))
    '''State of the button, can be one of 'normal' or 'down'.
    By default, the state of the button is 'normal'.

    :data:`state` is an :class:`~kivy.properties.OptionProperty`.
    '''

    background_normal = StringProperty('data/images/button.png')
    '''Background image of the button used for default graphical representation,
    when the button is not pressed.

    .. versionadded:: 1.0.4

    :data:`background_normal` is an :class:`~kivy.properties.StringProperty`,
    default to 'data/images/button.png'
    '''

    background_down = StringProperty('data/images/button_pressed.png')
    '''Background image of the button used for default graphical representation,
    when the button is pressed.

    .. versionadded:: 1.0.4

    :data:`background_down` is an :class:`~kivy.properties.StringProperty`,
    default to 'data/images/button_pressed.png'
    '''

    def __init__(self, **kwargs):
        super(Button, self).__init__(**kwargs)
        self.register_event_type('on_press')
        self.register_event_type('on_release')

    def _do_press(self):
        self.state = 'down'

    def _do_release(self):
        self.state = 'normal'

    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return False
        if self in touch.ud:
            return False
        touch.grab(self)
        touch.ud[self] = True
        self._do_press()
        self.dispatch('on_press')
        return True

    def on_touch_move(self, touch):
        return self in touch.ud

    def on_touch_up(self, touch):
        if not self in touch.ud:
            return False
        touch.ungrab(self)
        self._do_release()
        self.dispatch('on_release')
        return True

    def on_press(self):
        pass

    def on_release(self):
        pass

