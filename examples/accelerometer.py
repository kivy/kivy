from kivy.app import App
from kivy.clock import Clock
from kivy.uxl import UxlBuilder
from threading import Thread
from collections import deque
from subprocess import Popen, PIPE

content = '''
Widget:
    canvas:
        Color:
            rgb: (1, 0, 1)
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
        Rectangle:
            pos: self.pos
'''

class AcceleratorApp(App):
    def build(self):
        root = UxlBuilder(content=content).root
        self.queue = deque()
        self.thread = Thread(target=self.read_accelerometer, args=(self.queue, ))
        self.thread.daemon = True
        self.thread.start()
        Clock.schedule_interval(self.pop_deque, 0)
        return root

    def pop_deque(self, *largs):
        print '=========+++++FPS+++++=============', Clock.get_fps()
        try:
            while True:
                axis, value = self.queue.pop()
                if axis == 'X':
                    self.root.x = value
                if axis == 'Y':
                    self.root.y = value
        except IndexError:
            return

    def read_accelerometer(self, q):
        process = Popen('sudo evtest /dev/input/event7', shell=True,
                       stdout=PIPE)
        while True:
            line = process.stdout.readline()
            line = line.split(' ')
            if len(line) != 11:
                continue
            if line[0] != 'Event:':
                continue
            axis = line[8]
            value = int(line[10].strip('\n'))
            q.appendleft((axis[1], value))


AcceleratorApp().run()
