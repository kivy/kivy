'''
Use keyboard to do some action
'''

__all__ = ('start', 'stop')

import sys
import logging
from kivy.cache import Cache
from kivy.clock import Clock
from kivy.base import getWindow
from kivy.graphx import drawRectangle, drawLabel, set_color, drawLine, drawCircle
from kivy.logger import kivy_logger_history, Logger
from kivy.ui.colors import css_reload
from kivy.ui.widgets import *

_toggle_state = ''

def toggle(id):
    global _toggle_state
    if _toggle_state == id:
        _toggle_state = ''
    else:
        _toggle_state = id
    if _toggle_state == '':
        return

def _can_fullscreen():
    return sys.platform not in ('win32', 'darwin', 'cygwin', 'freebsd7')

def _screenshot():
    import os
    import pygame
    from kivy.core.gl import glReadBuffer, glReadPixels, GL_RGB, GL_UNSIGNED_BYTE, GL_FRONT
    win = getWindow()
    glReadBuffer(GL_FRONT)
    data = glReadPixels(0, 0, win.width, win.height, GL_RGB, GL_UNSIGNED_BYTE)
    surface = pygame.image.fromstring(str(buffer(data)), win.size, 'RGB', True)
    filename = None
    for i in xrange(9999):
        path = os.path.join(os.getcwd(), 'screenshot%04d.jpg' % i)
        if not os.path.exists(path):
            filename = path
            break
    if filename:
        try:
            pygame.image.save(surface, filename)
            Logger.info('KeyBinding: Screenshot saved at %s' % filename)
        except:
            Logger.exception('KeyBinding: Unable to take a screenshot')
    else:
        Logger.warning('KeyBinding: Unable to take screenshot, no more slot available')

def _on_draw():
    global _toggle_state
    if _toggle_state == '':
        return

    win = getWindow()

    #
    # Show HELP screen
    #
    if _toggle_state == 'help':

        # draw the usual window
        win.on_draw()

        # make background more black
        set_color(0, 0, 0, .8)
        drawRectangle(size=win.size)

        # prepare calculation
        w2 = win.width / 2.
        h2 = win.height / 2.
        y = 0
        k = {'font_size': 20}
        ydiff = 25

        # draw help
        drawLabel('Kivy Keybinding',
                  pos=(w2, win.height - 100), font_size=40)
        drawLabel('Press F1 to leave help',
                  pos=(w2, win.height - 160), font_size=12)
        drawLabel('FPS is %.3f' % Clock.get_fps(),
                  pos=(w2, win.height - 180), font_size=12)
        drawLabel('F1 - Show Help',
                  pos=(w2, h2), **k)
        y += ydiff
        drawLabel('F2 - Show FPS (%s)' % str(win.show_fps),
                  pos=(w2, h2 - y), **k)
        y += ydiff
        drawLabel('F3 - Show Cache state',
                  pos=(w2, h2 - y), **k)
        y += ydiff
        drawLabel('F4 - Show Calibration screen',
                  pos=(w2, h2 - y), **k)
        if _can_fullscreen():
            y += ydiff
            drawLabel('F5 - Toggle fullscreen',
                      pos=(w2, h2 - y), **k)
        y += ydiff
        drawLabel('F6 - Show log',
                  pos=(w2, h2 - y), **k)
        y += ydiff
        drawLabel('F7 - Reload CSS',
                  pos=(w2, h2 - y), **k)
        y += ydiff
        drawLabel('F8 - Show widget tree',
                  pos=(w2, h2 - y), **k)
        y += ydiff
        drawLabel('F9 - Rotate the screen (%d)' % win.rotation,
                  pos=(w2, h2 - y), **k)
        y += ydiff
        drawLabel('F12 - Screenshot',
                  pos=(w2, h2 - y), **k)

        return True

    #
    # Draw cache state
    #
    elif _toggle_state == 'cachestat':
        # draw the usual window
        win.on_draw()

        # make background more black
        set_color(0, 0, 0, .8)
        drawRectangle(size=win.size)

        y = 0
        for x in Cache._categories:
            y += 25
            cat = Cache._categories[x]
            count = 0
            usage = '-'
            limit = cat['limit']
            timeout = cat['timeout']
            try:
                count = len(Cache._objects[x])
            except:
                pass
            try:
                usage = 100 * count / limit
            except:
                pass
            args = (x, usage, count, limit, timeout)
            drawLabel('%s: usage=%s%% count=%d limit=%s timeout=%s' % args,
                      pos=(20, 20 + y), font_size=20, center=False, nocache=True)

        return True

    #
    # Draw calibration screen
    #
    elif _toggle_state == 'calibration':
        step = 8
        ratio = win.height / float(win.width)
        stepx = win.width / step
        stepy = win.height / int(step * ratio)

        # draw black background
        set_color(0, 0, 0)
        drawRectangle(size=win.size)

        # draw lines
        set_color(1, 1, 1)
        for x in xrange(0, win.width, stepx):
            drawLine((x, 0, x, win.height))
        for y in xrange(0, win.height, stepy):
            drawLine((0, y, win.width, y))

        # draw circles
        drawCircle(pos=(win.width / 2., win.height / 2.),
                   radius=win.width / step, linewidth = 2.)
        drawCircle(pos=(win.width / 2., win.height / 2.),
                   radius=(win.width / step) * 2, linewidth = 2.)
        drawCircle(pos=(win.width / 2., win.height / 2.),
                   radius=(win.width / step) * 3, linewidth = 2.)

        return True


    #
    # Draw calibration screen 2 (colors)
    #
    elif _toggle_state == 'calibration2':

        # draw black background
        set_color(0, 0, 0)
        drawRectangle(size=win.size)

        # gray
        step = 25
        stepx = (win.width - 100) / step
        stepy = stepx * 2
        sizew = stepx * step
        sizeh = stepy * step
        w2 = win.width / 2.
        h2 = win.height / 2.
        for _x in xrange(step):
            x = w2 - sizew / 2. + _x * stepx
            drawLabel(chr(65+_x), pos=(x + stepx / 2., h2 + 190))
            c = _x / float(step)

            # grey
            set_color(c, c, c)
            drawRectangle(pos=(x, h2 + 100), size=(stepx, stepy))

            # red
            set_color(c, 0, 0)
            drawRectangle(pos=(x, h2 + 80 - stepy), size=(stepx, stepy))

            # green
            set_color(0, c, 0)
            drawRectangle(pos=(x, h2 + 60 - stepy * 2), size=(stepx, stepy))

            # blue
            set_color(0, 0, c)
            drawRectangle(pos=(x, h2 + 40 - stepy * 3), size=(stepx, stepy))
        return True


    #
    # Draw log screen
    #
    elif _toggle_state == 'log':

        # draw the usual window
        win.on_draw()

        # make background more black
        set_color(0, 0, 0, .8)
        drawRectangle(size=win.size)


        # calculation
        w2 = win.width / 2.
        h2 = win.height / 2.
        k = {'font_size': 11, 'center': False}
        y = win.height - 20
        y = h2
        max = int((h2 / 20))
        levels = {
            logging.DEBUG: ('DEBUG', (.4, .4, 1)),
            logging.INFO: ('INFO', (.4, 1, .4)),
            logging.WARNING: ('WARNING', (1, 1, .4)),
            logging.ERROR: ('ERROR', (1, .4, .4)),
            logging.CRITICAL: ('CRITICAL', (1, .4, .4)), }

        # draw title
        drawLabel('Kivy logger',
                  pos=(w2, win.height - 100), font_size=40)

        # draw logs
        for log in reversed(kivy_logger_history.history[:max]):
            levelname, color = levels[log.levelno]
            msg = log.message.split('\n')[0]
            x = 10
            s = drawLabel('[', pos=(x, y), **k)
            x += s[0]
            s = drawLabel(levelname, pos=(x, y), color=color, **k)
            x += s[0]
            s = drawLabel(']', pos=(x, y), **k)
            x += s[0]
            drawLabel(msg, pos=(100, y), **k)
            y -= 20
        return True



class SceneGraphNode(MTBoxLayout):
    def __init__(self, **kwargs):
        kwargs['invert'] = True
        super(SceneGraphNode, self).__init__(**kwargs)

        self.widget = kwargs['node']
        self.selected = False

        self.child_layout = MTBoxLayout(size_hint=(None, None), spacing=10, orientation="vertical")
        for c in self.widget.children:
            self.child_layout.add_widget(SceneGraphNode(node=c, size_hint=(None, None)))
        self.add_widget(self.child_layout)

        self.node_btn = MTToggleButton(label=str(self.widget.__class__.__name__), size=(150, 30))
        self.title = MTAnchorLayout(size_hint=(None, None), size=(200, self.child_layout.height))
        self.title.add_widget(self.node_btn)
        self.add_widget(self.title)

        self.node_btn.connect('on_release', self.select)

    def draw(self):
        if self.selected:
            set_color(1, 0, 0, 0.3)
            drawRectangle(self.to_widget(*self.widget.pos), self.widget.size)

        set_color(1, .3, 0)
        for c in self.child_layout.children:
            drawLine((self.node_btn.centerright, c.node_btn.centerleft), width=2)

    def select(self, *args):
        self.selected = not self.selected

    def add_new_widget(self, *args):
        new_widget = MTButton(label="I'm new!!!")
        self.widget.add_widget(new_widget)
        self.child_layout.add_widget(SceneGraphNode(node=new_widget, size_hint=(None, None)))
        self.title.size=(200, self.child_layout.height)

    def print_props(self, *args):
        for prop in self.widget.__dict__:
            if not prop.startswith("_"):
                print prop, ":", getattr(self.widget, prop)


_scene_graph_modal_layover = None
def toggle_scene_graph():
    global _scene_graph_modal_layover
    win = getWindow()
    if _scene_graph_modal_layover:
        win.remove_widget(_scene_graph_modal_layover)
        _scene_graph_modal_layover = None
        return
    else:
        scene_graph = SceneGraphNode(node=win.children[0], size_hint=(None, None))
        plane = MTScatterPlane(do_rotation=False)
        plane.add_widget(scene_graph)
        _scene_graph_modal_layover = MTModalWindow()
        _scene_graph_modal_layover.add_widget(plane)
        win.add_widget(_scene_graph_modal_layover)


def _on_keyboard_handler(key, scancode, unicode):
    if key is None:
        return
    win = getWindow()
    if key == 282: # F1
        toggle('help')
    elif key == 283: # F2
        win.show_fps = not win.show_fps
    elif key == 284: # F3
        toggle('cachestat')
    elif key == 285: # F4
        # rotating between calibration screen
        if _toggle_state == 'calibration':
            toggle('calibration2')
        elif _toggle_state == 'calibration2':
            toggle('')
        else:
            toggle('calibration')
    elif key == 286 and _can_fullscreen(): # F5
        win.toggle_fullscreen()
    elif key == 287: # F6
        toggle('log')
    elif key == 288: # F7
        css_reload()
    elif key == 289: # F8
        toggle_scene_graph()
    elif key == 290: # F9
        win.rotation = win.rotation + 90
    elif key == 293:
        _screenshot()


def start(win, ctx):
    win.push_handlers(on_keyboard=_on_keyboard_handler)
    win.push_handlers(on_draw=_on_draw)

def stop(win, ctx):
    win.remove_handlers(on_keyboard=_on_keyboard_handler)
    win.remove_handlers(on_draw=_on_draw)
