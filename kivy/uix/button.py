'''
Button
======
'''

__all__ = ('Button', )

from kivy.uix.label import Label
from kivy.properties import OptionProperty, StringProperty


class Button(Label):

    state = OptionProperty('normal', options=('normal', 'down'))

    text = StringProperty('Hello')

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

