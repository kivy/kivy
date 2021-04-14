'''
Benchmark
=========

This script performs and displays the results of a set of benchmarks. These
provide a set of metrics mainly aimed at gauging the OpenGL performance of your
system.

It also provides more specs regarding your graphics card setup together with
more comprehensive system information.
'''

from __future__ import print_function

benchmark_version = '1'

import os
import sys
import json
import kivy
import gc
from time import clock, time, ctime
from random import randint

from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import RenderContext
from kivy.input.motionevent import MotionEvent
from kivy.cache import Cache
from kivy.clock import Clock
from kivy.compat import PY2

if not PY2:
    xrange = range

clockfn = time
if sys.platform == 'win32':
    clockfn = clock


class FakeMotionEvent(MotionEvent):
    pass


class bench_widget_creation:
    '''Widget: creation (10000 Widget)'''

    def run(self):
        o = []
        for x in range(10000):
            o.append(Widget())


class bench_widget_creation_with_root:
    '''Widget: creation (10000 Widget + 1 root)'''

    def run(self):
        o = Widget()
        for x in range(10000):
            o.add_widget(Widget())


class bench_widget_draw:
    '''Widget: empty drawing (10000 Widget + 1 root)'''

    def __init__(self):
        self.ctx = RenderContext()
        self.root = root = Widget()
        for x in range(10000):
            root.add_widget(Widget())
        self.ctx.add(self.root.canvas)

    def run(self):
        self.ctx.draw()


class bench_widget_dispatch:
    '''Widget: event dispatch (1000 on_update in 10*1000 Widget)'''

    def __init__(self):
        root = Widget()
        for x in range(10):
            parent = Widget()
            for y in range(1000):
                parent.add_widget(Widget())
            root.add_widget(parent)
        self.root = root

    def run(self):
        touch = FakeMotionEvent('fake', 1, [])
        self.root.dispatch('on_touch_down', touch)
        self.root.dispatch('on_touch_move', touch)
        self.root.dispatch('on_touch_up', touch)


class bench_label_creation:
    '''Core: label creation (10000 * 10 a-z)'''

    def __init__(self):
        labels = []
        for x in range(10000):
            label = [chr(randint(ord('a'), ord('z'))) for x in range(10)]
            labels.append(''.join(label))
        self.labels = labels

    def run(self):
        o = []
        for x in self.labels:
            o.append(Label(text=x))


class bench_button_creation:
    '''Core: button creation (10000 * 10 a-z)'''

    def __init__(self):
        labels = []
        for x in xrange(10000):
            button = map(lambda x: chr(randint(ord('a'), ord('z'))),
                         xrange(10))
            labels.append(''.join(button))
        self.labels = labels

    def run(self):
        o = []
        for x in self.labels:
            o.append(Button(text=x))


class bench_label_creation_with_tick:
    '''Core: label creation (10000 * 10 a-z), with Clock.tick'''

    def __init__(self):
        labels = []
        for x in range(10000):
            label = [chr(randint(ord('a'), ord('z'))) for x in range(10)]
            labels.append(''.join(label))
        self.labels = labels

    def run(self):
        o = []
        for x in self.labels:
            o.append(Label(text=x))
        # tick for texture creation
        Clock.tick()


class bench_button_creation_with_tick:
    '''Core: button creation (10000 * 10 a-z), with Clock.tick'''

    def __init__(self):
        labels = []
        for x in xrange(10000):
            button = map(lambda x: chr(randint(ord('a'), ord('z'))),
                         xrange(10))
            labels.append(''.join(button))
        self.labels = labels

    def run(self):
        o = []
        for x in self.labels:
            o.append(Button(text=x))
        # tick for texture creation
        Clock.tick()


if __name__ == '__main__':

    report = []
    report_newline = True
    Clock.start_clock()

    def log(s, newline=True):
        global report_newline
        if not report_newline:
            report[-1] = '%s %s' % (report[-1], s)
        else:
            report.append(s)
        if newline:
            print(s)
            report_newline = True
        else:
            print(s, end=' ')
            report_newline = False
        sys.stdout.flush()

    clock_total = 0
    benchs = list(globals().keys())
    benchs.sort()
    benchs = [globals()[x] for x in benchs if x.startswith('bench_')]

    log('')
    log('=' * 70)
    log('Kivy Benchmark v%s' % benchmark_version)
    log('=' * 70)
    log('')
    log('System information')
    log('-------------------')

    log('OS platform     : %s' % sys.platform)
    log('Python EXE      : %s' % sys.executable)
    log('Python Version  : %s' % sys.version)
    log('Python API      : %s' % sys.api_version)
    log('Kivy Version    : %s' % kivy.__version__)
    log('Install path    : %s' % os.path.dirname(kivy.__file__))
    log('Install date    : %s' % ctime(os.path.getctime(kivy.__file__)))

    log('')
    log('OpenGL information')
    log('-------------------')

    from kivy.core.gl import glGetString, GL_VENDOR, GL_RENDERER, GL_VERSION
    log('GL Vendor: %s' % glGetString(GL_VENDOR))
    log('GL Renderer: %s' % glGetString(GL_RENDERER))
    log('GL Version: %s' % glGetString(GL_VERSION))
    log('')

    log('Benchmark')
    log('---------')

    for x in benchs:
        # clean cache to prevent weird case
        for cat in Cache._categories:
            Cache.remove(cat)

        # force gc before next test
        gc.collect()

        log('%2d/%-2d %-60s' % (benchs.index(x) + 1,
            len(benchs), x.__doc__), False)
        try:
            sys.stderr.write('.')
            test = x()
        except Exception as e:
            log('failed %s' % str(e))
            import traceback
            traceback.print_exc()
            continue

        clock_start = clockfn()

        try:
            sys.stderr.write('.')
            test.run()
            clock_end = clockfn() - clock_start
            log('%.6f' % clock_end)
        except Exception as e:
            log('failed %s' % str(e))
            continue

        clock_total += clock_end

    log('')
    log('Result: %.6f' % clock_total)
    log('')
    Clock.stop_clock()

try:
    reply = input(
        'Do you want to send benchmark to gist.github.com (Y/n) : ')
except EOFError:
    sys.exit(0)

if reply.lower().strip() in ('', 'y'):
    print('Please wait while sending the benchmark...')

    try:
        import requests
    except ImportError:
        print("`requests` module not found, no benchmark posted.")
        sys.exit(1)

    payload = {
        'public': True, 'files': {
            'benchmark.txt': {
                'content': '\n'.join(report)}}}

    r = requests.post('https://api.github.com/gists', data=json.dumps(payload))

    print()
    print()
    print('REPORT posted at {0}'.format(r.json['html_url']))
    print()
    print()
else:
    print('No benchmark posted.')
