
"""
Label textsize
============

This example shows how to size a Label to its content (texture_size) and how
setting text_size controls text wrapping.
"""
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, BooleanProperty

# Copied from https://en.wikipedia.org/wiki/A_Tale_of_Two_Cities
# Published in 1859 and public domain.
# The newline after the title will help demonstrate halign
_example_title_text = 'A Tale of Two Cities, by Charles Dickens\n'
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

# Note: Many of the Widgets (StackLayout, ToggleButton, Spinner) have
# defaults set at the bottom of the KV, where  DemoLabel and HeadingLabel
# are also defined.
_kv_code = """
BoxLayout:
    orientation: 'vertical'

    HeadingLabel:
        text: 'These modify all demonstration Labels'

    StackLayout:
        # Button is a subclass of Label and can be sized to text in the same way

        Button:
            text: 'Reset'
            on_press: app.reset_words()

        ToggleButton:
            text: 'Shorten'
            on_state:
                app.shorten=self.state=='down'

        ToggleButton:
            text: 'max_lines=3'
            on_state:
                app.max_lines=3 if self.state=='down' else 0

        Spinner:
            text: 'bottom'
            values: 'bottom', 'middle', 'top'
            on_text: app.valign=self.text

        Spinner:
            text: 'left'
            values: 'left', 'center', 'right', 'justify'
            on_text: app.halign=self.text

    GridLayout:
        id: grid_layout
        cols: 2
        height: cm(6)
        size_hint_y: None

        HeadingLabel:
            text: "Default, no text_size set"

        HeadingLabel:
            text: 'text_size bound to size'

        DemoLabel:
            id: left_content
            disabled_color: 0, 0, 0, 0

        DemoLabel:
            id: right_content
            text_size: self.size
            padding: dp(6), dp(6)

    ToggleButton:
        text: 'Disable left'
        on_state:
            left_content.disabled=self.state=='down'

    # Need one Widget without size_hint_y: None, so that BoxLayout fills
    # available space.
    HeadingLabel:
        text: 'text_size width set, size bound to texture_size'
        text_size: self.size
        size_hint_y: 1

    DemoLabel:
        id: bottom_content
        # This Label wraps and expands its height to fit the text because
        # only text_size width is set and the Label size binds to texture_size.
        text_size: self.width, None
        size: self.texture_size
        padding: mm(4), mm(4)
        size_hint_y: None

# The column heading labels have their width set by the parent,
# but determine their height from the text.
<HeadingLabel@Label>:
    bold: True
    padding: dp(6), dp(4)
    valign: 'bottom'
    height: self.texture_size[1]
    text_size: self.width, None
    size_hint_y: None

<ToggleButton,Button>:
    padding: dp(10), dp(8)
    size_hint: None, None
    size: self.texture_size

# This inherits Button and the modifications above, so reset size
<Spinner>:
    size: sp(68), self.texture_size[1]

<DemoLabel@Label>:
    halign: app.halign
    valign: app.valign
    shorten: app.shorten
    max_lines: app.max_lines

    canvas:
        Color:
            rgb: 68/255.0, 164/255.0, 201/255.0
        Line:
            rectangle: self.x, self.y, self.width, self.height

<StackLayout>:
    size_hint_y: None
    spacing: dp(6)
    padding: dp(6), dp(4)
    height: self.minimum_height
"""


class LabelTextureSizeExample(App):
    # All Labels use these properties, set to Label defaults
    valign = StringProperty('bottom')
    halign = StringProperty('left')
    shorten = BooleanProperty(False)
    max_lines = NumericProperty(0)

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
            content_widget.text = _example_title_text
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
