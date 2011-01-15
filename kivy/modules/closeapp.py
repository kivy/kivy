'''
CloseApp: Close an application with one finger
'''

from kivy import MTWidget, getCurrentTouches, Vector, set_color
from kivy import stopTouchApp, gx_matrix, drawSemiCircle, Clock


class CloseApp(MTWidget):

    def __init__(self, **kwargs):
        super(CloseApp, self).__init__(**kwargs)
        self.dt = 0
        self.closetouches = {}

    def do_close(self):
        stopTouchApp()

    def on_update(self):
        self.bring_to_front()

    def draw(self):
        t = Clock.get_time()
        touches = getCurrentTouches()

        # draw closed touches
        to_delete = []
        ids = [touch.id for touch in touches]
        for id in self.closetouches:
            if not id in ids:
                to_delete.append(id)
                continue
            touch = self.closetouches[id]
            value = ((t - touch.time_start) - 1) / 2.
            if value > 1:
                self.do_close()
                return
            set_color(1, 1, 1, .7)
            drawSemiCircle(pos=(touch.x, touch.y), inner_radius=30,
                            outer_radius=50, slices=64, sweep_angle=value*360)

        # delete old touches
        for id in to_delete:
            del self.closetouches[id]

        # search
        for t in touches:
            if 'closeapp.invalid_for_close' in t.userdata:
                continue
            # distance < 20
            if Vector(t.osxpos, t.osypos).distance(Vector(t.sx, t.sy)) > 0.015:
                # flag
                t.userdata['closeapp.invalid_for_close'] = True
                if t.id in self.closetouches:
                    del self.closetouches[touch.id]
                return
            # 1s minimum
            if t - t.time_start < 1:
                if t.id in self.closetouches:
                    del self.closetouches[t.id]
                return
            # check corner screen
            if t.sx < .75 or t.sy < .75:
                if t.id in self.closetouches:
                    del self.closetouches[t.id]
                return
            # add touches to closed touches
            self.closetouches[t.id] = t


def start(win, ctx):
    ctx.w = CloseApp()
    win.add_widget(ctx.w)


def stop(win, ctx):
    win.remove_widget(ctx.w)

