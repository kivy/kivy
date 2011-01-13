'''
Sleep: reduce FPS when no activity is detected.

Temporary solution to sleep any Kivy application if nobody touch the screen.
This could have a bad impact when reading video or audio. It's not suitable for
everyone, it's just a temporary solution.

Sleep module check every frame if they are any touches activities. When no
activity is made from an amount of time, sleep module will introduce a sleep()
call after each frame renderer. More the sleep will be high, more the FPS will
decrease, more your CPU will be not used.

Sleep module need 2 lists: ramp and sleep. For example ::

    [modules]
    sleep = ramp=5:10:20:30:60:180,sleep=.03:.1:.2:.5:1.:5.

For a ramp of 5s, 10s, 20s, 30s, 50s, 180s, the sleep time will be .03s, .1s,
.2s, .5s, 1., 5.
With this default ramp/sleep, after 5s of inactivity, FPS will be 1/0.03 =
33 FPS. After 10s, FPS will be 1/.1 = 10 FPS...

During the sleep phase, touch cannot wake up the module. But the module will be
reseted.
'''

from kivy.logger import Logger
from time import time, sleep


class Sleep(object):

    def __init__(self, config, win):
        super(Sleep, self).__init__()
        self.timer_no_activity = time()
        self.win = win
        self.step = -1

        # take configuration
        ramp = config.get('ramp').split(':')
        sleep = config.get('sleep').split(':')
        if len(ramp) != len(sleep):
            raise ValueError('Sleep: Invalid ramp/sleep: list size is not the same')
        self.ramp = map(float, ramp)
        self.sleep = map(float, sleep)
        Logger.debug('Sleep: ramp is %s' % str(self.ramp))
        Logger.debug('Sleep: sleep is %s' % str(self.sleep))

    def start(self):
        win = self.win
        win.connect('on_touch_down', self.got_activity)
        win.connect('on_touch_move', self.got_activity)
        win.connect('on_touch_up', self.got_activity)
        win.connect('on_flip', self.do_check)

    def stop(self):
        win = self.win
        win.remove_handler('on_touch_down', self.got_activity)
        win.remove_handler('on_touch_move', self.got_activity)
        win.remove_handler('on_touch_up', self.got_activity)
        win.remove_handler('on_flip', self.do_check)

    def got_activity(self, *largs, **kwargs):
        self.timer_no_activity = time()

    def do_check(self, *largs, **kwargs):
        timer = time() - self.timer_no_activity
        step = -1
        for x in self.ramp:
            if timer >= x:
                step += 1
        if self.step != step:
            if step == -1:
                Logger.info('Sleep: activity detected, wake up.')
            else:
                Logger.info('Sleep: %ds inactivity detected. Reduce FPS to '
                            '%.4f' % (self.ramp[step], 1. / float(self.sleep[step])))
            self.step = step
        if step >= 0:
            sleep(self.sleep[step])


def start(win, ctx):
    ctx.config.setdefault('ramp', '5:10:20:30:60:180')
    ctx.config.setdefault('sleep', '.03:.1:.2:.5:1.:5.')
    ctx.sleep = Sleep(ctx.config, win)
    ctx.sleep.start()


def stop(win, ctx):
    ctx.sleep.stop()
    del ctx.sleep
