__all__ = ('HoverBehavior', )

from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty
from kivy.weakproxy import WeakProxy


class HoverBehavior(object):
    hovering = BooleanProperty(False)
    _last_hover = None

    def on_motion(self, touch):
        if super(HoverBehavior, self).on_motion(touch):
            if self.hovering:
                self.hovering = False
            return True
        if self.collide_point(touch.x, touch.y):
            self.hovering = True
            last = HoverBehavior._last_hover
            if last and last != self:
                HoverBehavior._last_hover.hovering = False
            HoverBehavior._last_hover = WeakProxy(self)
            return True
        elif self.hovering:
            self.hovering = False
            HoverBehavior._last_hover = None
