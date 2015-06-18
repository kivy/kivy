
"""
Label textsize
============

This example shows how to size a Label to its content (texture_size) and how
setting text_size controls text wrapping.
"""
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder

# Copied from https://en.wikipedia.org/wiki/A_Tale_of_Two_Cities
# Published in 1859 and public domain.
_example_text = """It was the best of times, it was the worst of times,
it was the age of wisdom, it was the age of foolishness, it was the epoch of
belief, it was the epoch of incredulity, it was the season of Light, it was
the season of Darkness, it was the spring of hope, it was the winter of despair,
we had everything before us, we had nothing before us, we were all going
direct to Heaven, we were all going direct the other way - in short,
the period was so far like the present period, that some of its noisiest
authorities insisted on its being received, for good or for evil, in the
superlative degree of comparison only.
"""

_kv_code = """
# Note: StackLayout, ToggleButton, and HeadingLabel are defined at the bottom.
Widget:
    GridLayout:
        id: grid_layout
        cols: 2
        top: root.top
        width: root.width
        height: cm(6)

        HeadingLabel:
            text: "GridLayout (1st column): Default, no text_size set"

        HeadingLabel:
            text: 'GridLayout: (2nd column): text_size bound to size'

        Label:
            id: left_content
            canvas:
                Color:
                    rgb: 68/255.0, 164/255.0, 201/255.0
                Line:
                    rectangle: self.x, self.y, self.width, self.height

        Label:
            id: right_content
            text_size: self.size
            padding: dp(6), dp(6)

            canvas:
                Color:
                    rgb: 68/255.0, 164/255.0, 201/255.0
                Line:
                    rectangle: self.x, self.y, self.width, self.height

        StackLayout:

            ToggleButton:
                text: 'Disable'
                on_state:
                    left_content.disabled=self.state=='down'

        StackLayout:

            ToggleButton:
                text: 'Shorten'
                on_state:
                    right_content.shorten=self.state=='down'

            ToggleButton:
                text: 'max_lines=3'
                on_state:
                    right_content.max_lines=3 if self.state=='down' else 0

            Spinner:
                text: 'bottom'
                values: 'bottom', 'middle', 'top'
                on_text: right_content.valign=self.text
                size_hint: None, None
                height: self.texture_size[1]
                padding: dp(10), dp(8)

    Label:
        # This Label will not wrap because text_size is not specified.
        id: title
        text: 'A Tale of Two Cities, by Charles Dickens'
        font_size: '20sp'
        y: bottom_content.top
        padding: mm(4), mm(4)
        # Binding size to texture_size is still required for padding to work.
        size: self.texture_size

    Label:
        id: bottom_content
        size: self.texture_size
        # This Label wraps because text_size width is set.
        text_size: root.width, None
        padding: mm(4), mm(4)

        # Outline Label size
        canvas:
            Color:
                rgb: 68/255.0, 164/255.0, 201/255.0
            Line:
                rectangle: self.x, self.y, self.width, self.height

    Button:
        # Button is a subclass of Label and can be sized to text in the same way
        text: 'Reset'
        padding: mm(6), mm(3)
        size: self.texture_size
        # Align to right side and vertically align-middle with title
        # Note: These calculations make the property dependencies explicit, see:
        # http://kivy.org/docs/api-kivy.uix.widget.html#usage-of-widget-center-widget-right-and-widget-top
        x: root.right - self.width - dp(4)
        y: title.center_y - self.height / 2.0
        on_press: app.reset_words()

# The column heading labels have their width set by the parent,
# but determine their height from the text.
<HeadingLabel@Label>:
    bold: True
    padding: dp(4), dp(4)
    height: self.texture_size[1]
    text_size: self.width, None
    size_hint_y: None

<ToggleButton>:
    padding: dp(10), dp(8)
    size_hint: None, None
    size: self.texture_size

<StackLayout>:
    size_hint_y: None
    spacing: dp(6)
    padding: dp(6), dp(4)
    height: self.minimum_height
"""


class LabelTextureSizeExample(App):

    def build(self):
        return Builder.load_string(_kv_code)

    def on_start(self):
        widget_ids = self.root.ids
        self.text_content_widgets = (widget_ids.left_content,
                                     widget_ids.right_content,
                                     widget_ids.bottom_content)
        self.reset_words()

    def reset_words(self):
        Clock.unschedule(self.add_word)
        for content_widget in self.text_content_widgets:
            content_widget.text = ''
        # initialize words generator
        self.words = (word for word in _example_text.split())
        self.add_word()

    def add_word(self, dt=None):
        try:
            word = next(self.words)
        except StopIteration:
            return

        for content_widget in self.text_content_widgets:
            content_widget.text += word + ' '

        pause_time = 0.03 * len(word)
        if word.endswith(','):
            pause_time += 0.6

        Clock.schedule_once(self.add_word, pause_time)

if __name__ == '__main__':
    LabelTextureSizeExample().run()
