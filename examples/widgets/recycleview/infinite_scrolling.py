"""
A constantly appending log, using recycleview.
- use variable size widgets using the key_size property to cache texture_size
- keeps current position in scroll when new data is happened, unless the view
  is at the very bottom, in which case it follows the log
- works well with mouse scrolling, but less nicely when using swipes,
  improvements welcome.
"""

from random import sample
from string import printable
from time import asctime

from kivy.app import App
from kivy.uix.recycleview import RecycleView
from kivy.lang import Builder
from kivy.properties import NumericProperty, ListProperty
from kivy.clock import Clock


KV = """
#:import rgba kivy.utils.rgba

<LogLabel@RelativeLayout>:
    # using a boxlayout here allows us to have better control of the text
    # position
    text: ''
    index: None
    Label:
        y: 0
        x: 5
        size_hint: None, None
        size: self.texture_size
        padding: dp(5), dp(5)
        color: rgba("#3f3e36")
        text: root.text
        on_texture_size: app.update_size(root.index, self.texture_size)

        canvas.before:
            Color:
                rgba: rgba("#dbeeff")
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: dp(5), dp(5)

BoxLayout:
    orientation: 'vertical'
    spacing: dp(2)

    # a label to help understand what's happening with the scrolling
    Label:
        size_hint_y: None
        height: self.texture_size[1]
        text:
            '''height: {height}
            scrollable_distance: {scrollable_distance}
            distance_to_top: {distance_to_top}
            scroll_y: {scroll_y}
            '''.format(
            height=rv.height,
            scrollable_distance=rv.scrollable_distance,
            distance_to_top=rv.distance_to_top,
            scroll_y=rv.scroll_y,
            )

        canvas.before:
            Color:
                rgba: rgba("#77b4ff")
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: dp(5), dp(5)

    FixedRecycleView:
        id: rv
        data: app.data
        viewclass: 'LogLabel'
        scrollable_distance: box.height - self.height

        RecycleBoxLayout:
            id: box
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            default_size: 0, 48
            default_size_hint: 1, None
            spacing: dp(1)
            key_size: 'cached_size'
"""


class FixedRecycleView(RecycleView):
    distance_to_top = NumericProperty()
    scrollable_distance = NumericProperty()

    def on_scrollable_distance(self, *args):
        """This method maintains the position in scroll, by using the saved
        distance_to_top property to adjust the scroll_y property. Only if we
        are currently scrolled back.
        """
        if self.scroll_y > 0:
            self.scroll_y = (
                (self.scrollable_distance - self.distance_to_top)
                / self.scrollable_distance
            )

    def on_scroll_y(self, *args):
        """Save the distance_to_top everytime we scroll.
        """
        self.distance_to_top = (1 - self.scroll_y) * self.scrollable_distance


class Application(App):
    data = ListProperty()

    def build(self):
        Clock.schedule_interval(self.add_log, .1)
        return Builder.load_string(KV)

    def add_log(self, dt):
        """Produce random text to append in the log, with the date, we don't
        want to forget when we babbled incoherently.
        """
        self.data.append({
            'index': len(self.data),
            'text': f"[{asctime()}]: {''.join(sample(printable, 50))}",
            'cached_size': (0, 0)
        })

    def update_size(self, index, size):
        """Maintain the size data for a log entry, so recycleview can adjust
        the size computation.
        As a log entry needs to be displayed to compute its size, it's by
        default considered to be (0, 0) which is a good enough approximation
        for such a small widget, but you might want do give a better default
        value if that doesn't fit your needs.
        """
        self.data[index]['cached_size'] = size


if __name__ == '__main__':
    Application().run()
