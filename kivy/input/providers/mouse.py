'''
Mouse provider implementation
=============================

On linux systems, the mouse provider can be annoying when used with another
multitouch provider (hidinput or mtdev). The Mouse can conflict with them: a
single touch can generate one event from the mouse provider and another
from the multitouch provider.

To avoid this behavior, you can activate the "disable_on_activity" token in
the mouse configuration. Then, if any touches are created by another
provider, the mouse event will be discarded. Add this to your configuration::

    [input]
    mouse = mouse,disable_on_activity

Using multitouch interaction with the mouse
-------------------------------------------

.. versionadded:: 1.3.0

By default, the middle and right mouse buttons, as well as a combination of
ctrl + left mouse button are used for multitouch emulation.
If you want to use them for other purposes, you can disable this behavior by
activating the "disable_multitouch" token::

   [input]
   mouse = mouse,disable_multitouch

.. versionchanged:: 1.9.0

You can now selectively control whether a click initiated as described above
will emulate multi-touch. If the touch has been initiated in the above manner
(e.g. right mouse button), a `multitouch_sim` value will be added to the
touch's profile, and a `multitouch_sim` property will be added to the touch.
By default, `multitouch_sim` is True and multitouch will be emulated for that
touch. If, however, `multitouch_on_demand` is added to the config::

   [input]
   mouse = mouse,multitouch_on_demand

then `multitouch_sim` defaults to `False`. In that case, if `multitouch_sim`
is set to True before the mouse is released (e.g. in on_touch_down/move), the
touch will simulate a multi-touch event. For example::

    if 'multitouch_sim' in touch.profile:
        touch.multitouch_sim = True

Following is a list of the supported values for the
:attr:`~kivy.input.motionevent.MotionEvent.profile` property list.

================ ==========================================================
Profile value    Description
---------------- ----------------------------------------------------------
button           Mouse button (one of `left`, `right`, `middle`, `scrollup`
                 or `scrolldown`). Accessed via the 'button' property.
pos              2D position. Also reflected in the
                 :attr:`~kivy.input.motionevent.MotionEvent.x`,
                 :attr:`~kivy.input.motionevent.MotionEvent.y`
                 and :attr:`~kivy.input.motionevent.MotionEvent.pos`
                 properties.
multitouch_sim   Specifies whether multitouch is simulated or not. Accessed
                 via the 'multitouch_sim' property.
================ ==========================================================

'''

__all__ = ('MouseMotionEventProvider', )

from kivy.base import EventLoop
from collections import deque
from kivy.logger import Logger
from kivy.input.provider import MotionEventProvider
from kivy.input.factory import MotionEventFactory
from kivy.input.motionevent import MotionEvent

# late binding
Color = Ellipse = None


class MouseMotionEvent(MotionEvent):

    def __init__(self, *args, **kwargs):
        self.multitouch_sim = False
        super().__init__(*args, **kwargs)

    def depack(self, args):
        self.sx, self.sy = args[:2]
        profile = self.profile
        if self.is_touch:
            # don't overwrite previous profile
            if not profile:
                profile.extend(('pos', 'button'))
            if len(args) >= 3:
                self.button = args[2]
            if len(args) == 4:
                self.multitouch_sim = args[3]
                profile.append('multitouch_sim')
        else:
            if not profile:
                profile.append('pos')
        super().depack(args)

    #
    # Create automatically touch on the surface.
    #

    def update_graphics(self, win, create=False):
        global Color, Ellipse
        de = self.ud.get('_drawelement', None)
        if de is None and create:
            if Color is None:
                from kivy.graphics import Color, Ellipse
            with win.canvas.after:
                de = (
                    Color(.8, .2, .2, .7),
                    Ellipse(size=(20, 20), segments=15))
            self.ud._drawelement = de
        if de is not None:
            self.push()

            # use same logic as WindowBase.on_motion() so we get correct
            # coordinates when _density != 1
            w, h = win._get_effective_size()

            self.scale_for_screen(w, h, rotation=win.rotation)

            de[1].pos = self.x - 10, self.y - 10
            self.pop()

    def clear_graphics(self, win):
        de = self.ud.pop('_drawelement', None)
        if de is not None:
            win.canvas.after.remove(de[0])
            win.canvas.after.remove(de[1])


class MouseMotionEventProvider(MotionEventProvider):
    __handlers__ = {}

    def __init__(self, device, args):
        super(MouseMotionEventProvider, self).__init__(device, args)
        self.waiting_event = deque()
        self.touches = {}
        self.counter = 0
        self.current_drag = None
        self.alt_touch = None
        self.disable_on_activity = False
        self.disable_multitouch = False
        self.multitouch_on_demand = False
        self.hover_event = None
        # split arguments
        args = args.split(',')
        for arg in args:
            arg = arg.strip()
            if arg == '':
                continue
            elif arg == 'disable_on_activity':
                self.disable_on_activity = True
            elif arg == 'disable_multitouch':
                self.disable_multitouch = True
            elif arg == 'multitouch_on_demand':
                self.multitouch_on_demand = True
            else:
                Logger.error('Mouse: unknown parameter <%s>' % arg)

    def start(self):
        '''Start the mouse provider'''
        if not EventLoop.window:
            return
        fbind = EventLoop.window.fbind
        fbind('on_mouse_down', self.on_mouse_press)
        fbind('on_mouse_move', self.on_mouse_motion)
        fbind('on_mouse_up', self.on_mouse_release)
        fbind('mouse_pos', self.begin_or_update_hover_event)
        fbind('system_size', self.update_hover_event)
        fbind('on_cursor_enter', self.begin_hover_event)
        fbind('on_cursor_leave', self.end_hover_event)
        fbind('on_close', self.end_hover_event)
        fbind('on_rotate', self.update_hover_event)

    def stop(self):
        '''Stop the mouse provider'''
        if not EventLoop.window:
            return
        funbind = EventLoop.window.funbind
        funbind('on_mouse_down', self.on_mouse_press)
        funbind('on_mouse_move', self.on_mouse_motion)
        funbind('on_mouse_up', self.on_mouse_release)
        funbind('mouse_pos', self.begin_or_update_hover_event)
        funbind('system_size', self.update_hover_event)
        funbind('on_cursor_enter', self.begin_hover_event)
        funbind('on_cursor_leave', self.end_hover_event)
        funbind('on_close', self.end_hover_event)
        funbind('on_rotate', self.update_hover_event)

    def test_activity(self):
        if not self.disable_on_activity:
            return False
        # trying to get if we currently have other touch than us
        # discard touches generated from kinetic
        touches = EventLoop.touches
        for touch in touches:
            # discard all kinetic touch
            if touch.__class__.__name__ == 'KineticMotionEvent':
                continue
            # not our instance, stop mouse
            if touch.__class__ != MouseMotionEvent:
                return True
        return False

    def find_touch(self, x, y):
        factor = 10. / EventLoop.window.system_size[0]
        for t in self.touches.values():
            if abs(x - t.sx) < factor and abs(y - t.sy) < factor:
                return t
        return False

    def create_event_id(self):
        self.counter += 1
        return self.device + str(self.counter)

    def create_touch(self, rx, ry, is_double_tap, do_graphics, button):
        event_id = self.create_event_id()
        args = [rx, ry, button]
        if do_graphics:
            args += [not self.multitouch_on_demand]
        self.current_drag = cur = MouseMotionEvent(
            self.device, event_id, args,
            is_touch=True
        )
        cur.is_double_tap = is_double_tap
        self.touches[event_id] = cur
        if do_graphics:
            # only draw red circle if multitouch is not disabled, and
            # if the multitouch_on_demand feature is not enable
            # (because in that case, we wait to see if multitouch_sim
            # is True or not before doing the multitouch)
            create_flag = (
                (not self.disable_multitouch) and
                (not self.multitouch_on_demand)
            )
            cur.update_graphics(EventLoop.window, create_flag)
        self.waiting_event.append(('begin', cur))
        return cur

    def remove_touch(self, cur):
        if cur.id not in self.touches:
            return
        del self.touches[cur.id]
        cur.update_time_end()
        self.waiting_event.append(('end', cur))
        cur.clear_graphics(EventLoop.window)

    def create_hover(self, etype, win):
        x_max, y_max = win.system_size[0] - 1, win.system_size[1] - 1
        args = (
            win.mouse_pos[0] / win._density / x_max if x_max > 0 else 0.0,
            win.mouse_pos[1] / win._density / y_max if y_max > 0 else 0.0
        )
        hover = self.hover_event
        if hover:
            hover.move(args)
        else:
            self.hover_event = hover = MouseMotionEvent(
                self.device,
                self.create_event_id(),
                args
            )
        if etype == 'end':
            hover.update_time_end()
            self.hover_event = None
        self.waiting_event.append((etype, hover))

    def on_mouse_motion(self, win, x, y, modifiers):
        x_max, y_max = win.system_size[0] - 1.0, win.system_size[1] - 1.0
        rx = x / x_max if x_max > 0 else 0.0
        ry = 1.0 - (y / y_max if y_max > 0 else 0.0)
        if self.current_drag:
            cur = self.current_drag
            cur.move([rx, ry])
            cur.update_graphics(win)
            self.waiting_event.append(('update', cur))
        elif self.alt_touch is not None and 'alt' not in modifiers:
            # alt just released ?
            is_double_tap = 'shift' in modifiers
            cur = self.create_touch(rx, ry, is_double_tap, True, [])
        return True

    def on_mouse_press(self, win, x, y, button, modifiers):
        if self.test_activity():
            return
        x_max, y_max = win.system_size[0] - 1.0, win.system_size[1] - 1.0
        rx = x / x_max if x_max > 0 else 0.0
        ry = 1.0 - (y / y_max if y_max > 0 else 0.0)
        new_me = self.find_touch(rx, ry)
        if new_me:
            self.current_drag = new_me
        else:
            is_double_tap = 'shift' in modifiers
            do_graphics = (not self.disable_multitouch) and (
                button != 'left' or 'ctrl' in modifiers)
            cur = self.create_touch(rx, ry, is_double_tap, do_graphics, button)
            if 'alt' in modifiers:
                self.alt_touch = cur
                self.current_drag = None
        return True

    def on_mouse_release(self, win, x, y, button, modifiers):
        # special case, if button is all, then remove all the current mouses.
        if button == 'all':
            for cur in list(self.touches.values())[:]:
                self.remove_touch(cur)
            self.current_drag = None

        cur = self.current_drag
        if cur:
            not_right = button in (
                'left',
                'scrollup', 'scrolldown',
                'scrollleft', 'scrollright'
            )
            not_ctrl = not ('ctrl' in modifiers)
            not_multi = (
                self.disable_multitouch or
                'multitouch_sim' not in cur.profile or
                not cur.multitouch_sim
            )

            if (not_right and not_ctrl or not_multi):
                self.remove_touch(cur)
                self.current_drag = None
            else:
                cur.update_graphics(EventLoop.window, True)

        if self.alt_touch:
            self.remove_touch(self.alt_touch)
            self.alt_touch = None
        return True

    def begin_or_update_hover_event(self, win, *args):
        etype = 'update' if self.hover_event else 'begin'
        self.create_hover(etype, win)

    def begin_hover_event(self, win, *args):
        if not self.hover_event:
            self.create_hover('begin', win)

    def update_hover_event(self, win, *args):
        if self.hover_event:
            self.create_hover('update', win)

    def end_hover_event(self, win, *args):
        if self.hover_event:
            self.create_hover('end', win)

    def update(self, dispatch_fn):
        '''Update the mouse provider (pop event from the queue)'''
        try:
            while True:
                event = self.waiting_event.popleft()
                dispatch_fn(*event)
        except IndexError:
            pass


# registers
MotionEventFactory.register('mouse', MouseMotionEventProvider)
