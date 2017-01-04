from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.base import runTouchApp
from kivy.uix.boxlayout import BoxLayout

import os

Builder.load_string('''
#:import Clipboard kivy.core.clipboard.Clipboard
<Clip>:
    orientation: 'vertical'
    GridLayout:
        cols: 3
        size_hint_y: None
        height: self.minimum_height
        Button:
            text: 'Paste raw'
            size_hint_y: None
            height: 60
            on_release: root.make_labels(Clipboard.paste())

        Button:
            text: 'Paste & format'
            size_hint_y: None
            height: 60
            on_release: root.make_pretty_labels(Clipboard.paste())

        Button:
            text: 'Remove widgets'
            size_hint_y: None
            height: 60
            on_release: container.clear_widgets()

    ScrollView:
        GridLayout:
            cols: 1
            id: container
            size_hint_y: None
            height: self.minimum_height
''')


class Clip(BoxLayout):
    def make_labels(self, values):
        """Creates widgets from raw clipboard i.e. for each character in the
        list that is provided by Clipboard.paste()
        """
        print(repr(values))
        for value in values:
            label = Label(text=value, size_hint_y=None, height=30)
            self.ids.container.add_widget(label)

    def make_pretty_labels(self, values):
        """Creates widgets from a list of values made by splitting clipboard
        by the default OS line separator. Useful when copying columns of data.
        """
        print(repr(values))
        for value in values.split(os.linesep):
            label = Label(text=value, size_hint_y=None, height=30)
            self.ids.container.add_widget(label)


runTouchApp(Clip())
