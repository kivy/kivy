'''
Monitor module
==============

Monitor module is a toolbar that show activity of your current application :

* FPS
* Graph of input event

'''

from kivy.uix.label import Label
from kivy.graphics import Rectangle, Color
from kivy.clock import Clock
from kivy.input.postproc import kivy_postproc_modules
from functools import partial

_statsinput = 0
_maxinput = -1


def update_fps(ctx, *largs):
    ctx.label.text = 'FPS: %f' % Clock.get_fps()
    ctx.rectangle.texture = ctx.label.texture
    ctx.rectangle.size = ctx.label.texture_size


def update_stats(ctx, *largs):
    global _statsinput
    ctx.stats = ctx.stats[1:] + [_statsinput]
    _statsinput = 0
    m = max(1., _maxinput)
    for index, x in enumerate(ctx.stats):
        ctx.statsr[index].size = (4, ctx.stats[index] / m * 20)


class StatsInput(object):

    def process(self, events):
        global _statsinput, _maxinput
        _statsinput += len(events)
        if _statsinput > _maxinput:
            _maxinput = float(_statsinput)
        return events


kivy_postproc_modules['fps'] = StatsInput()


def start(win, ctx):
    global _ctx
    ctx.label = Label(text='FPS: 0.0')
    ctx.inputstats = 0
    ctx.stats = []
    ctx.statsr = []
    with win.canvas.after:
        ctx.color = Color(1, 0, 0, .5)
        ctx.rectangle = Rectangle(pos=(0, win.height - 25),
                                  size=(win.width, 25))
        ctx.color = Color(1, 1, 1)
        ctx.rectangle = Rectangle(pos=(5, win.height - 20))
        ctx.color = Color(1, 1, 1, .5)
        for x in xrange(64):
            ctx.stats.append(0)
            ctx.statsr.append(
                Rectangle(pos=(win.width - 64 * 4 + x * 4, win.height - 25),
                          size=(4, 0)))
    Clock.schedule_interval(partial(update_fps, ctx), .5)
    Clock.schedule_interval(partial(update_stats, ctx), 1 / 60.)


def stop(win, ctx):
    win.canvas.remove(ctx.label)
