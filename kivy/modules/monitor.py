'''
Monitor module
==============

The Monitor module is a toolbar that shows the activity of your current
application :

* FPS
* Graph of input events

Usage
-----

For normal module usage, please see the :mod:`~kivy.modules` documentation.

'''

__all__ = ('start', 'stop')

from kivy.uix.label import Label
from kivy.graphics import Rectangle, Color
from kivy.metrics import dp
from kivy.clock import Clock
from functools import partial

_statsinput = 0
_maxinput = -1


def update_fps(ctx, *largs):
    ctx.label.text = 'FPS: %f' % Clock.get_fps()
    ctx.rectangle.texture = ctx.label.texture
    ctx.rectangle.size = ctx.label.texture_size


def update_stats(win, ctx, *largs):
    global _statsinput
    ctx.stats = ctx.stats[1:] + [_statsinput]
    _statsinput = 0
    m = max(1., _maxinput)
    for i, x in enumerate(ctx.stats):
        ctx.statsr[i].size = (dp(4), ctx.stats[i] / m * dp(20))
        ctx.statsr[i].pos = (
            win.width - dp(64 * 4) + i * dp(4), win.height - dp(25))


def _update_monitor_canvas(win, ctx, *largs):
    with win.canvas.after:
        ctx.overlay.pos = (0, win.height - dp(25))
        ctx.overlay.size = (win.width, dp(25))
        ctx.rectangle.pos = (dp(5), win.height - dp(20))


class StatsInput(object):
    def process(self, events):
        global _statsinput, _maxinput
        _statsinput += len(events)
        if _statsinput > _maxinput:
            _maxinput = float(_statsinput)
        return events


def start(win, ctx):
    # late import to avoid breaking module loading
    from kivy.input.postproc import kivy_postproc_modules
    kivy_postproc_modules['fps'] = StatsInput()
    global _ctx
    ctx.label = Label(text='FPS: 0.0')
    ctx.inputstats = 0
    ctx.stats = []
    ctx.statsr = []
    with win.canvas.after:
        ctx.color = Color(1, 0, 0, .5)
        ctx.overlay = Rectangle(pos=(0, win.height - dp(25)),
                                size=(win.width, dp(25)))
        ctx.color = Color(1, 1, 1)
        ctx.rectangle = Rectangle(pos=(dp(5), win.height - dp(20)))
        ctx.color = Color(1, 1, 1, .5)
        for i in range(64):
            ctx.stats.append(0)
            ctx.statsr.append(Rectangle(
                pos=(win.width - dp(64 * 4) + i * dp(4), win.height - dp(25)),
                size=(dp(4), 0)))
    win.bind(size=partial(_update_monitor_canvas, win, ctx))
    Clock.schedule_interval(partial(update_fps, ctx), .5)
    Clock.schedule_interval(partial(update_stats, win, ctx), 1 / 60.)


def stop(win, ctx):
    win.canvas.remove(ctx.label)
