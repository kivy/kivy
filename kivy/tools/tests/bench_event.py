'''
Bench event

This bench was used to found bottleneck in our Scene Graph, and accelerate our
event dispatching method.

With Python 2.6.5 (r265:79063, Apr 16 2010, 13:57:41) [GCC 4.4.3] on linux2

The test case is constructed like this :
  - A tree with 10 children having each 100 children (1001 widgets in total)
  - dispatch 1000x a event through the root widget, walking on the tree

Event 'on_update' -> just dispatch on_update
Event 'on_touch_*' -> dispatch down/move/up event

Current master :
    MTWidget: on_update : Time=4.265, FPS=234.483
    MTWidget: on_touch_*: Time=11.815, FPS=84.635
    MTLabel: on_update : Time=12.925, FPS=77.367
    MTLabel: on_touch_*: Time=29.559, FPS=33.830
    MTScatterWidget: on_update : Time=4.286, FPS=233.303
    MTScatterWidget: on_touch_*: Time=20.192, FPS=49.525

Core optimization :
    MTWidget: on_update : Time=1.067, FPS=937.621
    MTWidget: on_touch_*: Time=5.531, FPS=180.815
    MTLabel: on_update : Time=1.110, FPS=900.846
    MTLabel: on_touch_*: Time=5.817, FPS=171.899
    MTScatterWidget: on_update : Time=1.143, FPS=874.883
    MTScatterWidget: on_touch_*: Time=17.059, FPS=58.621

Core optimization + accelerate module :
    MTWidget: on_update : Time=0.614, FPS=1629.753
    MTWidget: on_touch_*: Time=5.048, FPS=198.104
    MTLabel: on_update : Time=0.676, FPS=1479.345
    MTLabel: on_touch_*: Time=5.198, FPS=192.376
    MTScatterWidget: on_update : Time=0.691, FPS=1447.955
    MTScatterWidget: on_touch_*: Time=16.999, FPS=58.828

'''


import timeit

stmt_setup = '''
import kivy

# fake touch class
class TestTouch(kivy.Touch):
    pass

# fake touch instance
touch = TestTouch(0, 'unknown', (150, 150))

# override widget
TestWidget = kivy.%s
root = TestWidget()
for x in xrange(10):
    m = TestWidget()
    for x in xrange(100):
        m.add_widget(TestWidget())
    root.add_widget(m)
'''

stmt_on_update = '''
root.dispatch_event('on_update')
'''

stmt_on_touch_all = '''
root.dispatch_event('on_touch_down', touch)
root.dispatch_event('on_touch_move', touch)
root.dispatch_event('on_touch_up', touch)
'''

frames = 1000

for x in ('MTWidget', 'MTLabel', 'MTScatterWidget',):
    t = timeit.Timer(stmt_on_update, stmt_setup % x).timeit(number=frames)
    print '%s: on_update : Time=%.3f, FPS=%.3f' % (x, t, frames / t)
    t = timeit.Timer(stmt_on_touch_all, stmt_setup % x).timeit(number=frames)
    print '%s: on_touch_*: Time=%.3f, FPS=%.3f' % (x, t, frames / t)
