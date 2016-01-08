from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import CanvasBase
from kivy.graphics import Color
from kivy.graphics import Ellipse
from kivy.graphics import ScissorPush
from kivy.graphics import ScissorPop
from kivy.properties import ListProperty
from kivy.properties import NumericProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.relativelayout import RelativeLayout


class TouchRippleBehavior(object):
    """Touch ripple behavior.

    Supposed to be used as mixin on widget classes.

    Ripple behavior does not trigger automatically, concrete implementation
    needs to call ``ripple_show`` respective ``ripple_fade`` manually.

    Example::

        class RippleButton(TouchRippleBehavior, ButtonBehavior, Label):

            def __init__(self, **kwargs):
                super(RippleButton, self).__init__(**kwargs)

            def on_touch_down(self, touch):
                collide_point = self.collide_point(touch.x, touch.y)
                if collide_point and self.disabled:
                    return True
                elif collide_point:
                    self.ripple_show(touch)
                return super(RippleButton, self).on_touch_down(touch)

            def on_touch_up(self, touch):
                if touch.grab_current is self:
                    touch.ungrab(self)
                    self.ripple_fade()
                    if self.disabled:
                        return True
                return super(RippleButton, self).on_touch_up(touch)
    """
    ripple_rad_default = 10
    ripple_duration_in = .5
    ripple_duration_out = .2
    ripple_fade_from_alpha = .5
    ripple_fade_to_alpha = .8
    ripple_scale = 2.
    ripple_func_in = 'in_cubic'
    ripple_func_out = 'out_quad'

    ripple_rad = NumericProperty(ripple_rad_default)
    ripple_pos = ListProperty([0, 0])
    ripple_color = ListProperty((1., 1., 1., ripple_fade_from_alpha))

    def __init__(self, **kwargs):
        super(TouchRippleBehavior, self).__init__(**kwargs)
        self.ripple_pane = CanvasBase()
        self.canvas.add(self.ripple_pane)
        self.bind(
            ripple_color=self._ripple_set_color,
            ripple_pos=self._ripple_set_ellipse,
            ripple_rad=self._ripple_set_ellipse
        )
        self.ripple_ellipse = None
        self.ripple_col_instruction = None

    def ripple_show(self, touch):
        """Begin ripple animation on current widget.

        Expects touch event as argument.
        """
        Animation.cancel_all(self, 'ripple_rad', 'ripple_color')
        self._ripple_anim_complete(self, self)
        x, y = self.to_window(*self.pos)
        width, height = self.size
        if isinstance(self, RelativeLayout):
            self.ripple_pos = ripple_pos = (touch.x - x, touch.y - y)
        else:
            self.ripple_pos = ripple_pos = (touch.x, touch.y)
        rc = self.ripple_color
        ripple_rad = self.ripple_rad
        self.ripple_color = [rc[0], rc[1], rc[2], self.ripple_fade_from_alpha]
        with self.ripple_pane:
            # In python 3 the int cast will be unnecessary
            ScissorPush(
                x=int(round(x)),
                y=int(round(y)),
                width=int(round(width)),
                height=int(round(height))
            )
            self.ripple_col_instruction = Color(rgba=self.ripple_color)
            self.ripple_ellipse = Ellipse(
                size=(ripple_rad, ripple_rad),
                pos=(
                    ripple_pos[0] - ripple_rad / 2.,
                    ripple_pos[1] - ripple_rad / 2.
                )
            )
            ScissorPop()
        anim = Animation(
            ripple_rad=max(width, height) * self.ripple_scale,
            t=self.ripple_func_in,
            ripple_color=[rc[0], rc[1], rc[2], self.ripple_fade_to_alpha],
            duration=self.ripple_duration_in
        )
        anim.start(self)

    def ripple_fade(self):
        """Finish ripple animation on current widget.
        """
        Animation.cancel_all(self, 'ripple_rad', 'ripple_color')
        width, height = self.size
        rc = self.ripple_color
        duration = self.ripple_duration_out
        anim = Animation(
            ripple_rad=max(width, height) * self.ripple_scale,
            ripple_color=[rc[0], rc[1], rc[2], 0.],
            t=self.ripple_func_out,
            duration=duration
        )
        anim.bind(on_complete=self._ripple_anim_complete)
        anim.start(self)

    def _ripple_set_ellipse(self, instance, value):
        ellipse = self.ripple_ellipse
        if not ellipse:
            return
        ripple_pos = self.ripple_pos
        ripple_rad = self.ripple_rad
        ellipse.size = (ripple_rad, ripple_rad)
        ellipse.pos = (
            ripple_pos[0] - ripple_rad / 2.,
            ripple_pos[1] - ripple_rad / 2.
        )

    def _ripple_set_color(self, instance, value):
        if not self.ripple_col_instruction:
            return
        self.ripple_col_instruction.rgba = value

    def _ripple_anim_complete(self, anim, instance):
        self.ripple_rad = self.ripple_rad_default
        self.ripple_pane.clear()


class TouchRippleButtonBehavior(TouchRippleBehavior, ButtonBehavior):

    def __init__(self, **kwargs):
        super(TouchRippleButtonBehavior, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        collide_point = self.collide_point(touch.x, touch.y)
        if collide_point and self.disabled:
            return True
        elif collide_point:
            self.ripple_show(touch)
        return super(TouchRippleButtonBehavior, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.ripple_fade()
            if self.disabled:
                return True
            self.last_touch = touch

            def defer_release(dt):
                self.dispatch('on_release')
            Clock.schedule_once(defer_release, self.ripple_duration_out)
            return True
        return super(TouchRippleButtonBehavior, self).on_touch_up(touch)
