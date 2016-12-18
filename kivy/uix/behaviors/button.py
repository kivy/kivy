'''
Button Behavior
===============

The :class:`~kivy.uix.behaviors.button.ButtonBehavior`
`mixin <https://en.wikipedia.org/wiki/Mixin>`_ class provides
:class:`~kivy.uix.button.Button` behavior. You can combine this class with
other widgets, such as an :class:`~kivy.uix.image.Image`, to provide
alternative buttons that preserve Kivy button behavior.

For an overview of behaviors, please refer to the :mod:`~kivy.uix.behaviors`
documentation.

Example
-------

The following example adds button behavior to an image to make a checkbox that
behaves like a button::

    from kivy.app import App
    from kivy.uix.image import Image
    from kivy.uix.behaviors import ButtonBehavior


    class MyButton(ButtonBehavior, Image):
        def __init__(self, **kwargs):
            super(MyButton, self).__init__(**kwargs)
            self.source = 'atlas://data/images/defaulttheme/checkbox_off'

        def on_press(self):
            self.source = 'atlas://data/images/defaulttheme/checkbox_on'

        def on_release(self):
            self.source = 'atlas://data/images/defaulttheme/checkbox_off'


    class SampleApp(App):
        def build(self):
            return MyButton()


    SampleApp().run()

See :class:`~kivy.uix.behaviors.ButtonBehavior` for details.
'''

__all__ = ('ButtonBehavior', )

from kivy.clock import Clock
from kivy.config import Config
from kivy.properties import OptionProperty, ObjectProperty, \
    BooleanProperty, NumericProperty
from time import time


class ButtonBehavior(object):
    '''
    This `mixin <https://en.wikipedia.org/wiki/Mixin>`_ class provides
    :class:`~kivy.uix.button.Button` behavior. Please see the
    :mod:`button behaviors module <kivy.uix.behaviors.button>` documentation
    for more information.

    :Events:
        `on_press`
            Fired when the button is pressed.
        `on_release`
            Fired when the button is released (i.e. the touch/click that
            pressed the button goes away).

    '''

    state = OptionProperty('normal', options=('normal', 'down'))
    '''The state of the button, must be one of 'normal' or 'down'.
    The state is 'down' only when the button is currently touched/clicked,
    otherwise its 'normal'.

    :attr:`state` is an :class:`~kivy.properties.OptionProperty` and defaults
    to 'normal'.
    '''

    last_touch = ObjectProperty(None)
    '''Contains the last relevant touch received by the Button. This can
    be used in `on_press` or `on_release` in order to know which touch
    dispatched the event.

    .. versionadded:: 1.8.0

    :attr:`last_touch` is a :class:`~kivy.properties.ObjectProperty` and
    defaults to `None`.
    '''

    min_state_time = NumericProperty(0)
    '''The minimum period of time which the widget must remain in the
    `'down'` state.

    .. versionadded:: 1.9.1

    :attr:`min_state_time` is a float and defaults to 0.035. This value is
    taken from :class:`~kivy.config.Config`.
    '''

    always_release = BooleanProperty(False)
    '''This determines whether or not the widget fires an `on_release` event if
    the touch_up is outside the widget.

    .. versionadded:: 1.9.0

    .. versionchanged:: 1.9.2
        The default value is now False.

    :attr:`always_release` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to `False`.
    '''

    def __init__(self, **kwargs):
        self.register_event_type('on_press')
        self.register_event_type('on_release')
        if 'min_state_time' not in kwargs:
            self.min_state_time = float(Config.get('graphics',
                                                   'min_state_time'))
        super(ButtonBehavior, self).__init__(**kwargs)
        self.__state_event = None
        self.__touch_time = None
        self.fbind('state', self.cancel_event)

    def _do_press(self):
        self.state = 'down'

    def _do_release(self, *args):
        self.state = 'normal'

    def cancel_event(self, *args):
        if self.__state_event:
            self.__state_event.cancel()
            self.__state_event = None

    def on_touch_down(self, touch):
        if super(ButtonBehavior, self).on_touch_down(touch):
            return True
        if touch.is_mouse_scrolling:
            return False
        if not self.collide_point(touch.x, touch.y):
            return False
        if self in touch.ud:
            return False
        touch.grab(self)
        touch.ud[self] = True
        self.last_touch = touch
        self.__touch_time = time()
        self._do_press()
        self.dispatch('on_press')
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            return True
        if super(ButtonBehavior, self).on_touch_move(touch):
            return True
        return self in touch.ud

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super(ButtonBehavior, self).on_touch_up(touch)
        assert(self in touch.ud)
        touch.ungrab(self)
        self.last_touch = touch

        if (not self.always_release and
                not self.collide_point(*touch.pos)):
            self._do_release()
            return

        touchtime = time() - self.__touch_time
        if touchtime < self.min_state_time:
            self.__state_event = Clock.schedule_once(
                self._do_release, self.min_state_time - touchtime)
        else:
            self._do_release()
        self.dispatch('on_release')
        return True

    def on_press(self):
        pass

    def on_release(self):
        pass

    def trigger_action(self, duration=0.1):
        '''Trigger whatever action(s) have been bound to the button by calling
        both the on_press and on_release callbacks.

        This simulates a quick button press without using any touch events.

        Duration is the length of the press in seconds. Pass 0 if you want
        the action to happen instantly.

        .. versionadded:: 1.8.0
        '''
        self._do_press()
        self.dispatch('on_press')

        def trigger_release(dt):
            self._do_release()
            self.dispatch('on_release')
        if not duration:
            trigger_release(0)
        else:
            Clock.schedule_once(trigger_release, duration)
