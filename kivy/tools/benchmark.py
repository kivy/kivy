'''
Benchmark for Kivy Framework
'''

benchmark_version = '1'

import gc
import kivy
import sys
import os
import time
from kivy.core.gl import *
from random import randint, random
from kivy import *
from kivy.graphics import *
from time import clock, time, ctime

clockfn = time
if sys.platform == 'win32':
    clockfn = clock

try:
    window_size = getWindow().size
except:
    window_size = MTWindow().size

class bench_core_label:
    '''Core: label creation (10000 * 10 a-z)'''
    def __init__(self):
        labels = []
        for x in xrange(10000):
            label = map(lambda x: chr(randint(ord('a'), ord('z'))), xrange(10))
            labels.append(''.join(label))
        self.labels = labels
    def run(self):
        o = []
        for x in self.labels:
            o.append(Label(label=x))


class bench_widget_creation:
    '''Widget: creation (10000 MTWidget)'''
    def run(self):
        o = []
        for x in xrange(10000):
            o.append(MTWidget())

class bench_widget_dispatch:
    '''Widget: event dispatch (1000 on_update in 10*1000 MTWidget)'''
    def __init__(self):
        root = MTWidget()
        for x in xrange(10):
            parent = MTWidget()
            for y in xrange(1000):
                parent.add_widget(MTWidget())
            root.add_widget(parent)
        self.root = root
    def run(self):
        root = self.root
        for x in xrange(1000):
            root.dispatch('on_update')

class bench_graphx_line:
    '''Graphx: draw lines (5000 x/y) 1000 times'''
    def __init__(self):
        lines = []
        w, h = window_size
        for x in xrange(5000):
            lines.extend([random() * w, random() * h])
        self.lines = lines
    def run(self):
        lines = self.lines
        for x in xrange(1000):
            drawLine(lines)

class bench_graphics_line:
    '''Graphics: draw lines (5000 x/y) 1000 times'''
    def __init__(self):
        w, h = window_size
        self.canvas = Canvas()
        line = self.canvas.line()
        for x in xrange(5000):
            line.points += [random() * w, random() * h]
    def run(self):
        canvas = self.canvas
        for x in xrange(1000):
            canvas.draw()


class bench_graphx_rectangle:
    '''Graphx: draw rectangle (5000 rect) 1000 times'''
    def __init__(self):
        rects = []
        w, h = window_size
        for x in xrange(5000):
            rects.append(((random() * w, random() * h), (random() * w, random() * h)))
        self.rects = rects
    def run(self):
        rects = self.rects
        for x in xrange(1000):
            for pos, size in rects:
                drawRectangle(pos=pos, size=size)

class bench_graphics_rectangle:
    '''Graphics: draw rectangle (5000 rect) 1000 times'''
    def __init__(self):
        rects = []
        w, h = window_size
        canvas = Canvas()
        for x in xrange(5000):
            canvas.rectangle(random() * w, random() * h, random() * w, random() * h)
        self.canvas = canvas
    def run(self):
        canvas = self.canvas
        for x in xrange(1000):
            canvas.draw()

class bench_graphics_rectanglemesh:
    '''Graphics: draw rectangle in same mesh (5000 rect) 1000 times'''
    def __init__(self):
        rects = []
        w, h = window_size
        canvas = Canvas()
        mesh = canvas.graphicElement(format='vv', type='quads')
        vertex = []
        for x in xrange(50000):
            vertex.extend([random() * w, random() * h, random() * w, random() * h])
        mesh.data_v = vertex
        self.canvas = canvas
    def run(self):
        canvas = self.canvas
        for x in xrange(1000):
            canvas.draw()

class bench_graphx_roundedrectangle:
    '''Graphx: draw rounded rectangle (5000 rect) 1000 times'''
    def __init__(self):
        rects = []
        w, h = window_size
        for x in xrange(5000):
            rects.append(((random() * w, random() * h), (random() * w, random() * h)))
        self.rects = rects
    def run(self):
        rects = self.rects
        for x in xrange(1000):
            for pos, size in rects:
                drawRoundedRectangle(pos=pos, size=size)


class bench_graphics_roundedrectangle:
    '''Graphics: draw rounded rectangle (5000 rect) 1000 times'''
    def __init__(self):
        rects = []
        w, h = window_size
        canvas = Canvas()
        for x in xrange(5000):
            canvas.roundedRectangle(random() * w, random() * h, random() * w, random() * h)
        self.canvas = canvas
    def run(self):
        canvas = self.canvas
        for x in xrange(1000):
            canvas.draw()

class bench_graphx_paintline:
    '''Graphx: paint line (5000 x/y) 1000 times'''
    def __init__(self):
        lines = []
        w, h = window_size
        for x in xrange(500):
            lines.extend([random() * w, random() * h])
        self.lines = lines
        set_brush(os.path.join(kivy_data_dir, 'particle.png'))
    def run(self):
        lines = self.lines
        for x in xrange(100):
            paintLine(lines)

class bench_graphics_paintline:
    '''Graphics: paint lines (5000 x/y) 1000 times'''
    def __init__(self):
        w, h = window_size
        self.canvas = Canvas()
        texture = Image(os.path.join(kivy_data_dir, 'particle.png')).texture
        line = self.canvas.point(type='line_strip', texture=texture)
        for x in xrange(500):
            line.points += [random() * w, random() * h]
    def run(self):
        canvas = self.canvas
        for x in xrange(100):
            canvas.draw()


if __name__ == '__main__':
    report = []
    report_newline = True
    def log(s, newline=True):
        global report_newline
        if not report_newline:
            report[-1] = '%s %s' % (report[-1], s)
        else:
            report.append(s)
        if newline:
            print s
            report_newline = True
        else:
            print s,
            report_newline = False
        sys.stdout.flush()

    clock_total = 0
    benchs = locals().keys()
    benchs.sort()
    benchs = [locals()[x] for x in benchs if x.startswith('bench_')]

    log('')
    log('=' * 70)
    log('Kivy Benchmark v%s' % benchmark_version)
    log('=' * 70)
    log('')
    log('System informations')
    log('-------------------')

    log('OS platform     : %s' % sys.platform)
    log('Python EXE      : %s' % sys.executable)
    log('Python Version  : %s' % sys.version)
    log('Python API      : %s' % sys.api_version)
    try:
        log('Kivy Version    : %s' % kivy.__version__)
    except:
        log('Kivy Version    : unknown (too old)')
    log('Install path    : %s' % os.path.dirname(kivy.__file__))
    log('Install date    : %s' % ctime(os.path.getctime(kivy.__file__)))

    log('')
    log('OpenGL informations')
    log('-------------------')

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

        log('%2d/%-2d %-60s' % (benchs.index(x)+1, len(benchs), x.__doc__), False)
        try:
            sys.stderr.write('.')
            test = x()
        except Exception, e:
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
        except Exception, e:
            log('failed %s' % str(e))
            continue

        clock_total += clock_end

    log('')
    log('Result: %.6f' % clock_total)
    log('')

try:
    getWindow().close()
except:
    pass

try:
    reply = raw_input('Do you want to send benchmark to paste.pocoo.org (Y/n) : ')
except EOFError:
    sys.exit(0)

if reply.lower().strip() in ('', 'y'):
    print 'Please wait while sending the benchmark...'

    from xmlrpclib import ServerProxy
    s = ServerProxy('http://paste.pocoo.org/xmlrpc/')
    r = s.pastes.newPaste('text', '\n'.join(report))

    print
    print
    print 'REPORT posted at http://paste.pocoo.org/show/%s/' % r
    print
    print
else:
    print 'No benchmark posted.'
