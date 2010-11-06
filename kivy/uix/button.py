'''
Button: 
'''

__all__ = ('Button', )

from kivy.uix.widget import Widget
from kivy.c_ext.properties import OptionProperty, StringProperty

class Button(Widget):

    state = OptionProperty('normal', options=('normal', 'down'))

    text = StringProperty('Hello')

    def __init__(self, **kwargs):
        super(Button, self).__init__(**kwargs)
        self.register_event_type('on_press')
        self.register_event_type('on_release')

    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return False
        if self in touch.userdata:
            return False
        touch.grab(self)
        touch.userdata[self] = True
        self.state = 'down'
        self.dispatch('on_press')
        return True

    def on_touch_move(self, touch):
        return self in touch.userdata

    def on_touch_up(self, touch):
        if not self in touch.userdata:
            return False
        touch.ungrab(self)
        self.state = 'normal'
        self.dispatch('on_release')
        return True

    def on_press(self):
        pass

    def on_release(self):
        pass

