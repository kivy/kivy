'''
JoyCursor
=========

.. versionadded:: 1.10.0

The JoyCursor is a tool for navigating with a joystick as if using a mouse
or touch. Most of the actions that are possible for a mouse user are available
in this module.

For example:

    * left click
    * right click
    * double click (two clicks)
    * moving the cursor
    * holding the button (+ moving at the same time)
    * selecting
    * scrolling

There are some properties that can be edited live, such as intensity of the
JoyCursor movement and toggling mouse button holding.

Usage
-----

For normal module usage, please see the :mod:`~kivy.modules` documentation
and these bindings:

+------------------+--------------------+
| Event            | Joystick           |
+==================+====================+
| cursor move      | Axis 3, Axis 4     |
+------------------+--------------------+
| cursor intensity | Button 0, Button 1 |
+------------------+--------------------+
| left click       | Button 2           |
+------------------+--------------------+
| right click      | Button 3           |
+------------------+--------------------+
| scroll up        | Button 4           |
+------------------+--------------------+
| scroll down      | Button 5           |
+------------------+--------------------+
| hold button      | Button 6           |
+------------------+--------------------+
| joycursor on/off | Button 7           |
+------------------+--------------------+

The JoyCursor, like Inspector, can also be imported and used as a normal
python module. This has the added advantage of being able to activate and
deactivate the module programmatically::

    from kivy.lang import Builder
    from kivy.base import runTouchApp
    runTouchApp(Builder.load_string("""
    #:import jc kivy.modules.joycursor
    BoxLayout:
        Button:
            text: 'Press & activate with Ctrl+E or Button 7'
            on_release: jc.create_joycursor(root.parent, root)
        Button:
            text: 'Disable'
            on_release: jc.stop(root.parent, root)
    """))
'''

__all__ = ('start', 'stop', 'create_joycursor')

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.properties import (
    ObjectProperty,
    NumericProperty,
    BooleanProperty
)


class JoyCursor(Widget):
    win = ObjectProperty()
    activated = BooleanProperty(False)
    cursor_width = NumericProperty(1.1)
    cursor_hold = BooleanProperty(False)
    intensity = NumericProperty(4)
    dead_zone = NumericProperty(10000)
    offset_x = NumericProperty(0)
    offset_y = NumericProperty(0)

    def __init__(self, **kwargs):
        super(JoyCursor, self).__init__(**kwargs)
        self.avoid_bring_to_top = False
        self.size_hint = (None, None)
        self.size = (21, 21)
        self.set_cursor()

        # draw cursor
        with self.canvas:
            Color(rgba=(0.19, 0.64, 0.81, 0.5))
            self.cursor_ox = Line(
                points=self.cursor_pts[:4],
                width=self.cursor_width + 0.1
            )
            self.cursor_oy = Line(
                points=self.cursor_pts[4:],
                width=self.cursor_width + 0.1
            )
            Color(rgba=(1, 1, 1, 0.5))
            self.cursor_x = Line(
                points=self.cursor_pts[:4],
                width=self.cursor_width
            )
            self.cursor_y = Line(
                points=self.cursor_pts[4:],
                width=self.cursor_width
            )
        self.pos = [-i for i in self.size]

    def on_window_children(self, win, *args):
        # pull JoyCursor to the front when added
        # as a child directly to the window.
        if self.avoid_bring_to_top:
            return
        self.avoid_bring_to_top = True
        win.remove_widget(self)
        win.add_widget(self)
        self.avoid_bring_to_top = False

    def on_activated(self, instance, activated):
        # bind/unbind when JoyCursor's state is changed
        if activated:
            self.win.add_widget(self)
            self.move = Clock.schedule_interval(self.move_cursor, 0)
            self.win.fbind('on_joy_axis', self.check_cursor)
            self.win.fbind('on_joy_button_down', self.set_intensity)
            self.win.fbind('on_joy_button_down', self.check_dispatch)
            self.win.fbind('mouse_pos', self.stop_cursor)
            mouse_pos = self.win.mouse_pos
            self.pos = (
                mouse_pos[0] - self.size[0] / 2.0,
                mouse_pos[1] - self.size[1] / 2.0
            )
            Logger.info('JoyCursor: joycursor activated')
        else:
            self.pos = [-i for i in self.size]
            Clock.unschedule(self.move)
            self.win.funbind('on_joy_axis', self.check_cursor)
            self.win.funbind('on_joy_button_down', self.set_intensity)
            self.win.funbind('on_joy_button_down', self.check_dispatch)
            self.win.funbind('mouse_pos', self.stop_cursor)
            self.win.remove_widget(self)
            Logger.info('JoyCursor: joycursor deactivated')

    def set_cursor(self, *args):
        # create cursor points
        px, py = self.pos
        sx, sy = self.size
        self.cursor_pts = [
            px, py + round(sy / 2.0), px + sx, py + round(sy / 2.0),
            px + round(sx / 2.0), py, px + round(sx / 2.0), py + sy
        ]

    def check_cursor(self, win, stickid, axisid, value):
        # check axes and set offset if a movement is registered
        intensity = self.intensity
        dead = self.dead_zone

        if axisid == 3:
            if value < -dead:
                self.offset_x = -intensity
            elif value > dead:
                self.offset_x = intensity
            else:
                self.offset_x = 0
        elif axisid == 4:
            # invert Y axis to behave like mouse
            if value < -dead:
                self.offset_y = intensity
            elif value > dead:
                self.offset_y = -intensity
            else:
                self.offset_y = 0
        else:
            self.offset_x = 0
            self.offset_y = 0

    def set_intensity(self, win, stickid, buttonid):
        # set intensity of joycursor with joystick buttons
        intensity = self.intensity
        if buttonid == 0 and intensity > 2:
            intensity -= 1
        elif buttonid == 1:
            intensity += 1
        self.intensity = intensity

    def check_dispatch(self, win, stickid, buttonid):
        if buttonid == 6:
            self.cursor_hold = not self.cursor_hold
        if buttonid not in (2, 3, 4, 5, 6):
            return

        x, y = self.center
        # window event, correction necessary
        y = self.win.system_size[1] - y
        modifiers = []
        actions = {
            2: 'left',
            3: 'right',
            4: 'scrollup',
            5: 'scrolldown',
            6: 'left'
        }
        button = actions[buttonid]

        self.win.dispatch('on_mouse_down', x, y, button, modifiers)
        if not self.cursor_hold:
            self.win.dispatch('on_mouse_up', x, y, button, modifiers)

    def move_cursor(self, *args):
        # move joycursor as a mouse
        self.pos[0] += self.offset_x
        self.pos[1] += self.offset_y
        modifiers = []
        if self.cursor_hold:
            self.win.dispatch(
                'on_mouse_move',
                self.center[0],
                self.win.system_size[1] - self.center[1],
                modifiers
            )

    def stop_cursor(self, instance, mouse_pos):
        # pin the cursor to the mouse pos
        self.offset_x = 0
        self.offset_y = 0
        self.pos = (
            mouse_pos[0] - self.size[0] / 2.0,
            mouse_pos[1] - self.size[1] / 2.0
        )

    def on_pos(self, instance, new_pos):
        self.set_cursor()
        self.cursor_x.points = self.cursor_pts[:4]
        self.cursor_y.points = self.cursor_pts[4:]
        self.cursor_ox.points = self.cursor_pts[:4]
        self.cursor_oy.points = self.cursor_pts[4:]

    def keyboard_shortcuts(self, win, scancode, *args):
        modifiers = args[-1]
        if scancode == 101 and modifiers == ['ctrl']:
            self.activated = not self.activated
            return True
        elif scancode == 27:
            if self.activated:
                self.activated = False
                return True

    def joystick_shortcuts(self, win, stickid, buttonid):
        if buttonid == 7:
            self.activated = not self.activated
            if self.activated:
                self.pos = [round(i / 2.0) for i in win.size]


def create_joycursor(win, ctx, *args):
    '''Create a JoyCursor instance attached to the *ctx* and bound to the
    Window's :meth:`~kivy.core.window.WindowBase.on_keyboard` event for
    capturing the keyboard shortcuts.

        :Parameters:
            `win`: A :class:`Window <kivy.core.window.WindowBase>`
                The application Window to bind to.
            `ctx`: A :class:`~kivy.uix.widget.Widget` or subclass
                The Widget for JoyCursor to attach to.

    '''
    ctx.joycursor = JoyCursor(win=win)
    win.bind(children=ctx.joycursor.on_window_children,
             on_keyboard=ctx.joycursor.keyboard_shortcuts)
    # always listen for joystick input to open the module
    # (like a keyboard listener)
    win.fbind('on_joy_button_down', ctx.joycursor.joystick_shortcuts)


def start(win, ctx):
    Clock.schedule_once(lambda *t: create_joycursor(win, ctx))


def stop(win, ctx):
    '''Stop and unload any active JoyCursors for the given *ctx*.
    '''
    if hasattr(ctx, 'joycursor'):
        ctx.joycursor.activated = False
        win.unbind(children=ctx.joycursor.on_window_children,
                   on_keyboard=ctx.joycursor.keyboard_shortcuts)
        win.funbind('on_joy_button_down', ctx.joycursor.joystick_shortcuts)
        win.remove_widget(ctx.joycursor)
        del ctx.joycursor
