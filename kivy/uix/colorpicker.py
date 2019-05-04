'''
Color Picker
============

.. versionadded:: 1.7.0

.. warning::

    This widget is experimental. Its use and API can change at any time until
    this warning is removed.

.. image:: images/colorpicker.png
    :align: right

The ColorPicker widget allows a user to select a color from a chromatic
wheel where pinch and zoom can be used to change the wheel's saturation.
Sliders and TextInputs are also provided for entering the RGBA/HSV/HEX values
directly.

Usage::

    clr_picker = ColorPicker()
    parent.add_widget(clr_picker)

    # To monitor changes, we can bind to color property changes
    def on_color(instance, value):
        print "RGBA = ", str(value)  #  or instance.color
        print "HSV = ", str(instance.hsv)
        print "HEX = ", str(instance.hex_color)

    clr_picker.bind(color=on_color)


'''

__all__ = ('ColorPicker', 'ColorWheel')

from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.widget import Widget
from kivy.properties import (NumericProperty, BoundedNumericProperty,
                             ListProperty, ObjectProperty,
                             ReferenceListProperty, StringProperty,
                             AliasProperty)
from kivy.clock import Clock
from kivy.graphics import Mesh, InstructionGroup, Color
from kivy.utils import get_color_from_hex, get_hex_from_color
from kivy.logger import Logger
from math import cos, sin, pi, sqrt, atan
from colorsys import rgb_to_hsv, hsv_to_rgb


def distance(pt1, pt2):
    return sqrt((pt1[0] - pt2[0]) ** 2. + (pt1[1] - pt2[1]) ** 2.)


def polar_to_rect(origin, r, theta):
    return origin[0] + r * cos(theta), origin[1] + r * sin(theta)


def rect_to_polar(origin, x, y):
    if x == origin[0]:
        if y == origin[1]:
            return (0, 0)
        elif y > origin[1]:
            return (y - origin[1], pi / 2.)
        else:
            return (origin[1] - y, 3 * pi / 2.)
    t = atan(float((y - origin[1])) / (x - origin[0]))
    if x - origin[0] < 0:
        t += pi

    if t < 0:
        t += 2 * pi

    return (distance((x, y), origin), t)


class ColorWheel(Widget):
    '''Chromatic wheel for the ColorPicker.

    .. versionchanged:: 1.7.1
        `font_size`, `font_name` and `foreground_color` have been removed. The
        sizing is now the same as others widget, based on 'sp'. Orientation is
        also automatically determined according to the width/height ratio.

    '''

    r = BoundedNumericProperty(0, min=0, max=1)
    '''The Red value of the color currently selected.

    :attr:`r` is a :class:`~kivy.properties.BoundedNumericProperty` and
    can be a value from 0 to 1. It defaults to 0.
    '''

    g = BoundedNumericProperty(0, min=0, max=1)
    '''The Green value of the color currently selected.

    :attr:`g` is a :class:`~kivy.properties.BoundedNumericProperty`
    and can be a value from 0 to 1.
    '''

    b = BoundedNumericProperty(0, min=0, max=1)
    '''The Blue value of the color currently selected.

    :attr:`b` is a :class:`~kivy.properties.BoundedNumericProperty` and
    can be a value from 0 to 1.
    '''

    a = BoundedNumericProperty(0, min=0, max=1)
    '''The Alpha value of the color currently selected.

    :attr:`a` is a :class:`~kivy.properties.BoundedNumericProperty` and
    can be a value from 0 to 1.
    '''

    color = ReferenceListProperty(r, g, b, a)
    '''The holds the color currently selected.

    :attr:`color` is a :class:`~kivy.properties.ReferenceListProperty` and
    contains a list of `r`, `g`, `b`, `a` values.
    '''

    _origin = ListProperty((100, 100))
    _radius = NumericProperty(100)

    _piece_divisions = NumericProperty(10)
    _pieces_of_pie = NumericProperty(16)

    _inertia_slowdown = 1.25
    _inertia_cutoff = .25

    _num_touches = 0
    _pinch_flag = False

    _hsv = ListProperty([1, 1, 1, 0])

    def __init__(self, **kwargs):
        super(ColorWheel, self).__init__(**kwargs)

        pdv = self._piece_divisions
        self.sv_s = [(float(x) / pdv, 1) for x in range(pdv)] + [
            (1, float(y) / pdv) for y in reversed(range(pdv))]

    def on__origin(self, instance, value):
        self.init_wheel(None)

    def on__radius(self, instance, value):
        self.init_wheel(None)

    def init_wheel(self, dt):
        # initialize list to hold all meshes
        self.canvas.clear()
        self.arcs = []
        self.sv_idx = 0
        pdv = self._piece_divisions
        ppie = self._pieces_of_pie

        for r in range(pdv):
            for t in range(ppie):
                self.arcs.append(
                    _ColorArc(
                        self._radius * (float(r) / float(pdv)),
                        self._radius * (float(r + 1) / float(pdv)),
                        2 * pi * (float(t) / float(ppie)),
                        2 * pi * (float(t + 1) / float(ppie)),
                        origin=self._origin,
                        color=(float(t) / ppie,
                               self.sv_s[self.sv_idx + r][0],
                               self.sv_s[self.sv_idx + r][1],
                               1)))

                self.canvas.add(self.arcs[-1])

    def recolor_wheel(self):
        ppie = self._pieces_of_pie
        for idx, segment in enumerate(self.arcs):
            segment.change_color(
                sv=self.sv_s[int(self.sv_idx + idx / ppie)])

    def change_alpha(self, val):
        for idx, segment in enumerate(self.arcs):
            segment.change_color(a=val)

    def inertial_incr_sv_idx(self, dt):
        # if its already zoomed all the way out, cancel the inertial zoom
        if self.sv_idx == len(self.sv_s) - self._piece_divisions:
            return False

        self.sv_idx += 1
        self.recolor_wheel()
        if dt * self._inertia_slowdown > self._inertia_cutoff:
            return False
        else:
            Clock.schedule_once(self.inertial_incr_sv_idx,
                                dt * self._inertia_slowdown)

    def inertial_decr_sv_idx(self, dt):
        # if its already zoomed all the way in, cancel the inertial zoom
        if self.sv_idx == 0:
            return False
        self.sv_idx -= 1
        self.recolor_wheel()
        if dt * self._inertia_slowdown > self._inertia_cutoff:
            return False
        else:
            Clock.schedule_once(self.inertial_decr_sv_idx,
                                dt * self._inertia_slowdown)

    def on_touch_down(self, touch):
        r = self._get_touch_r(touch.pos)
        if r > self._radius:
            return False

        # code is still set up to allow pinch to zoom, but this is
        # disabled for now since it was fiddly with small wheels.
        # Comment out these lines and  adjust on_touch_move to reenable
        # this.
        if self._num_touches != 0:
            return False

        touch.grab(self)
        self._num_touches += 1
        touch.ud['anchor_r'] = r
        touch.ud['orig_sv_idx'] = self.sv_idx
        touch.ud['orig_time'] = Clock.get_time()

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return
        r = self._get_touch_r(touch.pos)
        goal_sv_idx = (touch.ud['orig_sv_idx'] -
                       int((r - touch.ud['anchor_r']) /
                            (float(self._radius) / self._piece_divisions)))

        if (
            goal_sv_idx != self.sv_idx and
            goal_sv_idx >= 0 and
            goal_sv_idx <= len(self.sv_s) - self._piece_divisions
        ):
            # this is a pinch to zoom
            self._pinch_flag = True
            self.sv_idx = goal_sv_idx
            self.recolor_wheel()

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return
        touch.ungrab(self)
        self._num_touches -= 1
        if self._pinch_flag:
            if self._num_touches == 0:
                # user was pinching, and now both fingers are up. Return
                # to normal
                if self.sv_idx > touch.ud['orig_sv_idx']:
                    Clock.schedule_once(
                        self.inertial_incr_sv_idx,
                        (Clock.get_time() - touch.ud['orig_time']) /
                        (self.sv_idx - touch.ud['orig_sv_idx']))

                if self.sv_idx < touch.ud['orig_sv_idx']:
                    Clock.schedule_once(
                        self.inertial_decr_sv_idx,
                        (Clock.get_time() - touch.ud['orig_time']) /
                        (self.sv_idx - touch.ud['orig_sv_idx']))

                self._pinch_flag = False
                return
            else:
                # user was pinching, and at least one finger remains. We
                # don't want to treat the remaining fingers as touches
                return
        else:
            r, theta = rect_to_polar(self._origin, *touch.pos)
            # if touch up is outside the wheel, ignore
            if r >= self._radius:
                return
            # compute which ColorArc is being touched (they aren't
            # widgets so we don't get collide_point) and set
            # _hsv based on the selected ColorArc
            piece = int((theta / (2 * pi)) * self._pieces_of_pie)
            division = int((r / self._radius) * self._piece_divisions)
            hsva = list(
                self.arcs[self._pieces_of_pie * division + piece].color)
            self.color = list(hsv_to_rgb(*hsva[:3])) + hsva[-1:]

    def _get_touch_r(self, pos):
        return distance(pos, self._origin)


class _ColorArc(InstructionGroup):
    def __init__(self, r_min, r_max, theta_min, theta_max,
                 color=(0, 0, 1, 1), origin=(0, 0), **kwargs):
        super(_ColorArc, self).__init__(**kwargs)
        self.origin = origin
        self.r_min = r_min
        self.r_max = r_max
        self.theta_min = theta_min
        self.theta_max = theta_max
        self.color = color
        self.color_instr = Color(*color, mode='hsv')
        self.add(self.color_instr)
        self.mesh = self.get_mesh()
        self.add(self.mesh)

    def __str__(self):
        return "r_min: %s r_max: %s theta_min: %s theta_max: %s color: %s" % (
            self.r_min, self.r_max, self.theta_min, self.theta_max, self.color
        )

    def get_mesh(self):
        v = []
        # first calculate the distance between endpoints of the inner
        # arc, so we know how many steps to use when calculating
        # vertices
        end_point_inner = polar_to_rect(
            self.origin, self.r_min, self.theta_max)

        d_inner = d_outer = 3.
        theta_step_inner = (self.theta_max - self.theta_min) / d_inner

        end_point_outer = polar_to_rect(
            self.origin, self.r_max, self.theta_max)

        if self.r_min == 0:
            theta_step_outer = (self.theta_max - self.theta_min) / d_outer
            for x in range(int(d_outer)):
                v += (polar_to_rect(self.origin, 0, 0) * 2)
                v += (polar_to_rect(
                    self.origin, self.r_max,
                    self.theta_min + x * theta_step_outer) * 2)
        else:
            for x in range(int(d_inner + 2)):
                v += (polar_to_rect(
                    self.origin, self.r_min - 1,
                    self.theta_min + x * theta_step_inner) * 2)
                v += (polar_to_rect(
                    self.origin, self.r_max + 1,
                    self.theta_min + x * theta_step_inner) * 2)

        v += (end_point_inner * 2)
        v += (end_point_outer * 2)

        return Mesh(vertices=v, indices=range(int(len(v) / 4)),
                    mode='triangle_strip')

    def change_color(self, color=None, color_delta=None, sv=None, a=None):
        self.remove(self.color_instr)
        if color is not None:
            self.color = color
        elif color_delta is not None:
            self.color = [self.color[i] + color_delta[i] for i in range(4)]
        elif sv is not None:
            self.color = (self.color[0], sv[0], sv[1], self.color[3])
        elif a is not None:
            self.color = (self.color[0], self.color[1], self.color[2], a)
        self.color_instr = Color(*self.color, mode='hsv')
        self.insert(0, self.color_instr)


class ColorPicker(RelativeLayout):
    '''
    See module documentation.
    '''

    font_name = StringProperty('data/fonts/RobotoMono-Regular.ttf')
    '''Specifies the font used on the ColorPicker.

    :attr:`font_name` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'data/fonts/RobotoMono-Regular.ttf'.
    '''

    color = ListProperty((1, 1, 1, 1))
    '''The :attr:`color` holds the color currently selected in rgba format.

    :attr:`color` is a :class:`~kivy.properties.ListProperty` and defaults to
    (1, 1, 1, 1).
    '''

    def _get_hsv(self):
        return rgb_to_hsv(*self.color[:3])

    def _set_hsv(self, value):
        if self._updating_clr:
            return
        self.set_color(value)

    hsv = AliasProperty(_get_hsv, _set_hsv, bind=('color', ))
    '''The :attr:`hsv` holds the color currently selected in hsv format.

    :attr:`hsv` is a :class:`~kivy.properties.ListProperty` and defaults to
    (1, 1, 1).
    '''
    def _get_hex(self):
        return get_hex_from_color(self.color)

    def _set_hex(self, value):
        if self._updating_clr:
            return
        self.set_color(get_color_from_hex(value)[:4])

    hex_color = AliasProperty(_get_hex, _set_hex, bind=('color',), cache=True)
    '''The :attr:`hex_color` holds the currently selected color in hex.

    :attr:`hex_color` is an :class:`~kivy.properties.AliasProperty` and
    defaults to `#ffffffff`.
    '''

    wheel = ObjectProperty(None)
    '''The :attr:`wheel` holds the color wheel.

    :attr:`wheel` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    _update_clr_ev = _update_hex_ev = None

    # now used only internally.
    foreground_color = ListProperty((1, 1, 1, 1))

    def _trigger_update_clr(self, mode, clr_idx, text):
        if self._updating_clr:
            return
        self._updating_clr = True
        self._upd_clr_list = mode, clr_idx, text
        ev = self._update_clr_ev
        if ev is None:
            ev = self._update_clr_ev = Clock.create_trigger(self._update_clr)
        ev()

    def _update_clr(self, dt):
        # to prevent interaction between hsv/rgba, we work internaly using rgba
        mode, clr_idx, text = self._upd_clr_list
        try:
            text = min(255, max(0, float(text)))
            if mode == 'rgb':
                self.color[clr_idx] = float(text) / 255.
            else:
                hsv = list(self.hsv[:])
                hsv[clr_idx] = float(text) / 255.
                self.color[:3] = hsv_to_rgb(*hsv)
        except ValueError:
            Logger.warning('ColorPicker: invalid value : {}'.format(text))
        finally:
            self._updating_clr = False

    def _update_hex(self, dt):
        try:
            if len(self._upd_hex_list) != 9:
                return
            self._updating_clr = False
            self.hex_color = self._upd_hex_list
        finally:
            self._updating_clr = False

    def _trigger_update_hex(self, text):
        if self._updating_clr:
            return
        self._updating_clr = True
        self._upd_hex_list = text
        ev = self._update_hex_ev
        if ev is None:
            ev = self._update_hex_ev = Clock.create_trigger(self._update_hex)
        ev()

    def set_color(self, color):
        self._updating_clr = True
        if len(color) == 3:
            self.color[:3] = color
        else:
            self.color = color
        self._updating_clr = False

    def __init__(self, **kwargs):
        self._updating_clr = False
        super(ColorPicker, self).__init__(**kwargs)


if __name__ in ('__android__', '__main__'):
    from kivy.app import App

    class ColorPickerApp(App):
        def build(self):
            cp = ColorPicker(pos_hint={'center_x': .5, 'center_y': .5},
                             size_hint=(1, 1))
            return cp
    ColorPickerApp().run()
