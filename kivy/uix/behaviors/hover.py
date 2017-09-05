__all__ = ('HoverBehavior', )

from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty


class HoverBehavior(object):
    hovering = BooleanProperty(False)
    _last_hover = None

    def on_motion(self, event):
        if super(HoverBehavior, self).on_motion(event):
            if self.hovering:
                self.hovering = False
            return True
        if self.collide_point(event.x, event.y):
            self.hovering = True
            last = HoverBehavior._last_hover
            if last and last != self:
                HoverBehavior._last_hover.hovering = False
            HoverBehavior._last_hover = self.proxy_ref
            return True
        elif self.hovering:
            self.hovering = False
            HoverBehavior._last_hover = None
