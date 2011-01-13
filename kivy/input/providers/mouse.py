'''
Mouse provider implementation
=============================

On linux system, mouse provider can be annoying when used with another
multitouch provider (hidinput or mtdev.). Mouse can conflict with them: a single
touch can generate one event from mouse provider and from multitouch provider.

To avoid this behavior, you can activate the "disable_on_activity" token in
mouse. Then, if they are any touch active from another provider, the mouse will
be discarded. Put in your configuration ::

    [input]
    mouse = mouse,disable_on_activity

'''

__all__ = ('MouseTouchProvider', )

import kivy.base
from collections import deque
from kivy.logger import Logger
from kivy.input.provider import TouchProvider
from kivy.input.factory import TouchFactory
from kivy.input.touch import Touch

class MouseTouch(Touch):
    def depack(self, args):
        self.sx, self.sy = args
        super(MouseTouch, self).depack(args)

class MouseTouchProvider(TouchProvider):
    __handlers__ = {}

    def __init__(self, device, args):
        super(MouseTouchProvider, self).__init__(device, args)
        self.waiting_event = deque()
        self.window = None
        self.touches = {}
        self.counter = 0
        self.current_drag = None
        self.alt_touch = None
        self.disable_on_activity = False

        # split arguments
        args = args.split(',')
        for arg in args:
            if arg == '':
                continue
            elif arg == 'disable_on_activity':
                self.disable_on_activity = True
            else:
                Logger.error('Mouse: unknown parameter <%s>' % arg)

    def start(self):
        '''Start the mouse provider'''
        pass

    def stop(self):
        '''Stop the mouse provider'''
        pass

    def test_activity(self):
        if not self.disable_on_activity:
            return False
        # trying to get if we currently have other touch than us
        # discard touches generated from kinetic
        touches = kivy.base.getCurrentTouches()
        for touch in touches:
            # discard all kinetic touch
            if touch.__class__.__name__ == 'KineticTouch':
                continue
            # not our instance, stop mouse
            if touch.__class__ != MouseTouch:
                return True
        return False

    def find_touch(self, x, y):
        factor = 10. / self.window.system_size[0]
        for t in self.touches.itervalues():
            if abs(x-t.sx) < factor and abs(y-t.sy) < factor:
                return t
        return False

    def create_touch(self, rx, ry, is_double_tap):
        self.counter += 1
        id = 'mouse' + str(self.counter)
        self.current_drag = cur = MouseTouch(self.device, id=id, args=[rx, ry])
        cur.is_double_tap = is_double_tap
        self.touches[id] = cur
        self.waiting_event.append(('down', cur))
        return cur

    def remove_touch(self, cur):
        if cur.id not in self.touches:
            return
        del self.touches[cur.id]
        self.waiting_event.append(('up', cur))

    def on_mouse_motion(self, win, x, y, modifiers):
        width, height = self.window.system_size
        rx = x / float(width)
        ry = 1. - y / float(height)
        if self.current_drag:
            cur = self.current_drag
            cur.move([rx, ry])
            self.waiting_event.append(('move', cur))
        elif self.alt_touch is not None and 'alt' not in modifiers:
            # alt just released ?
            is_double_tap = 'shift' in modifiers
            self.create_touch(rx, ry, is_double_tap)
        return True

    def on_mouse_press(self, win, x, y, button, modifiers):
        if self.test_activity():
            return
        width, height = self.window.system_size
        rx = x / float(width)
        ry = 1. - y / float(height)
        newTouch = self.find_touch(rx, ry)
        if newTouch:
            self.current_drag = newTouch
        else:
            is_double_tap = 'shift' in modifiers
            cur = self.create_touch(rx, ry, is_double_tap)
            if 'alt' in modifiers:
                self.alt_touch = cur
                self.current_drag = None
        return True

    def on_mouse_release(self, win, x, y, button, modifiers):
        width, height = self.window.system_size
        rx = x / float(width)
        ry = 1. - y / float(height)
        cur = self.find_touch(rx, ry)
        if button == 'left' and cur and not ('ctrl' in modifiers):
            self.remove_touch(cur)
            self.current_drag = None
        if self.alt_touch:
            self.remove_touch(self.alt_touch)
            self.alt_touch = None
        return True

    def update(self, dispatch_fn):
        '''Update the mouse provider (pop event from the queue)'''
        if not self.window:
            from kivy.core.window import Window
            self.window = Window
            if self.window:
                Window.bind(
                    on_mouse_move=self.on_mouse_motion,
                    on_mouse_down=self.on_mouse_press,
                    on_mouse_up=self.on_mouse_release)
        if not self.window:
            return
        try:
            while True:
                event = self.waiting_event.popleft()
                dispatch_fn(*event)
        except Exception, e:
            pass

# registers
TouchFactory.register('mouse', MouseTouchProvider)
