from kivy.base import KivyEventLoop
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty, BooleanProperty
from kivy.clock import Clock
from random import sample
from string import printable
from time import sleep
import asyncio
import aiohttp
import logging
logging.basicConfig(level=logging.DEBUG)

KV = '''
#:import cos math.cos
#:import sin math.sin
#:import asyncio asyncio

BoxLayout:
    orientation: 'vertical'
    TextInput:
        text: 'http://www.sphinx-doc.org/en/stable/_sources/rest.txt'
        multiline: False
        size_hint_y: None
        height: self.minimum_height
        disabled: app.loading
        on_text_validate:
            app.load_page(self.text)

    RstDocument:
        id: viewer
        text: ''
        w1: app.time % 100
        w2: (app.time + 33) % 100
        w3: (app.time + 66) % 100
        canvas.after:
            Color:
                rgba: 1, 1, 1, 1 - (self.w1 if app.loading else 100) / 100
            Line:
                width: 4
                ellipse:
                    (
                    self.center_x - (self.w1 or 0) / 2,
                    self.center_y - (self.w1 or 0) / 2,
                    self.w1 or 0, self.w1 or 0
                    ) if app.time else (0, 0, 0, 0)
            Color:
                rgba: 1, 1, 1, 1 - (self.w2 if app.loading else 100) / 100
            Line:
                width: 4
                ellipse:
                    (
                    self.center_x - (self.w2 or 0) / 2,
                    self.center_y - (self.w2 or 0) / 2,
                    self.w2 or 0, self.w2 or 0
                    ) if app.time else (0, 0, 0, 0)
            Color:
                rgba: 1, 1, 1, 1 - (self.w3 if app.loading else 100) / 100
            Line:
                width: 4
                ellipse:
                    (
                    self.center_x - (self.w3 or 0) / 2,
                    self.center_y - (self.w3 or 0) / 2,
                    self.w3 or 0, self.w3 or 0
                    ) if app.time else (0, 0, 0, 0)
            Color:
                rgba: 1, 1, 1, 1

'''  # noqa


async def fetch_page(session, url):
    print("fetch page")
    with aiohttp.Timeout(10):
        print("timeout context")
        async with session.get(url) as response:
            print("response")
            if response.status == 200:
                print("200")
                return await response.read()
            else:
                print("error")
                return 'error: {}'.format(response.status)
    print("end timeout context")


class DebugTask(asyncio.Task):
    def _wakeup(self, future):
        print("woke up", self)
        super()._wakeup(future)
        print("after wakeup", self)


class MyApp(App):
    '''XXX
    '''
    time = NumericProperty()
    loading = BooleanProperty(False)

    def build(self):
        Clock.schedule_interval(self.update_time, 0)
        return Builder.load_string(KV)

    def update_time(self, deltatime):
        self.time += deltatime * 10

    def load_page(self, url):
        self.loading = True
        print("load page")
        with aiohttp.ClientSession(loop=ev) as session:
            print("session")
            try:
                content = ev.run_until_complete(
                    DebugTask(fetch_page(session, url)))
            except asyncio.TimeoutError:
                content = "timeout!"

            self.root.ids.viewer.text = content
            self.loading = False
        self.loading = False

if __name__ == '__main__':
    ev = KivyEventLoop(MyApp())
    ev.set_debug(True)
    ev.mainloop()
