from kivy.base import KivyEventLoop
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty
from kivy.clock import Clock
from random import sample
from string import printable
from time import sleep
import asyncio
import logging
logging.basicConfig(level=logging.DEBUG)

KV = '''
#:import cos math.cos
#:import sin math.sin
#:import asyncio asyncio

BoxLayout:
    Label:
        id: label
        text: 'test'
        canvas.before:
            Line:
                width: 5
                ellipse:
                    (
                    self.center_x - cos(app.time) * 100 - 30,
                    self.center_y - sin(app.time) * 100 - 30,
                    30, 30
                    )

    Button:
        text: 'push me'
        on_press:
            app.do_slow_stuff()
'''


def generate_text():
    print("called")
    return ''.join(sample(printable, 10))


class MyApp(App):
    time = NumericProperty()

    def build(self):
        Clock.schedule_interval(self.update_time, 0)
        return Builder.load_string(KV)

    def do_slow_stuff(self):
        ev.run_in_executor(None, self._do_slow_stuff)

    def _do_slow_stuff(self):
        label = self.root.ids.label
        label.text = ''
        for i in range(10):
            sleep(.1)
            label.text += generate_text()

    def update_time(self, dt):
        self.time += dt


if __name__ == '__main__':
    ev = KivyEventLoop(MyApp())
    ev.set_debug(True)
    ev.mainloop()
