"""Detecting and acting upon "Pull down actions" in a RecycleView
- When using overscroll or being at the to, a "pull down to refresh" message
  appears
- if the user pulls down far enough, then a refresh is triggered, which adds
  new elements at the top of the list.

"""
from threading import Thread
from time import sleep
from datetime import datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ListProperty, BooleanProperty
from kivy.metrics import dp
from kivy.clock import mainthread


KV = r'''
FloatLayout:
    Label:
        opacity: 1 if app.refreshing or rv.scroll_y > 1 else 0
        size_hint_y: None
        pos_hint: {'top': 1}
        text: 'Refreshing…' if app.refreshing else 'Pull down to refresh'

    RecycleView:
        id: rv
        data: app.data
        viewclass: 'Row'
        do_scroll_y: True
        do_scroll_x: False
        on_scroll_y: app.check_pull_refresh(self, grid)

        RecycleGridLayout:
            id: grid
            cols: 1
            size_hint_y: None
            height: self.minimum_height
            default_size: 0, 36
            default_size_hint: 1, None


<Row@Label>:
    _id: 0
    text: ''
    canvas:
        Line:
            rectangle: self.pos + self.size
            width: 0.6
'''


class Application(App):
    data = ListProperty([])
    refreshing = BooleanProperty()

    def build(self):
        self.refresh_data()
        return Builder.load_string(KV)

    def check_pull_refresh(self, view, grid):
        """Check the amount of overscroll to decide if we want to trigger the
        refresh or not.
        """
        max_pixel = dp(200)
        to_relative = max_pixel / (grid.height - view.height)
        if view.scroll_y <= 1.0 + to_relative or self.refreshing:
            return

        self.refresh_data()

    def refresh_data(self):
        # using a Thread to do a potentially long operation without blocking
        # the UI.
        self.refreshing = True
        Thread(target=self._refresh_data).start()

    def _refresh_data(self):
        sleep(2)
        update_time = datetime.now().strftime("%H:%M:%S")

        self.prepend_data([
            {'_id': i, 'text': '[{}] hello {}'.format(update_time, i)}
            for i in range(len(self.data) + 10, len(self.data), -1)
        ])

    @mainthread
    def prepend_data(self, data):
        self.data = data + self.data
        self.refreshing = False


if __name__ == "__main__":
    Application().run()
