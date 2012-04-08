#!/usr/bin/env python
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.lang import Builder

Builder.load_string('''
<AppOptions>:
    cols: 3
    size_hint_x: 1
    spacing: 30
    padding: 10
    row_default_height: 100
    cols_minimum: {0: 400, 1: 500, 2: 50}''')

# Local libraries
import touchanalyzer as TA

__all__ = ('AppOptions',)


class AppOptions(GridLayout):
    def __init__(self, **kwargs):
        super(AppOptions, self).__init__(**kwargs)
        self._setup_maxstrokes()
        self._setup_temporal()
        self._setup_resulttime()

    def _setup_maxstrokes(self):
        txt = "Maximum number of strokes? (0=disable)\n"
        txt += "Causes the sample to be dispatched for recognition when\n"
        txt += "the gesture reaches a specific number of strokes"
        self.add_widget(Label(text=txt, size_hint=(None, None)))

        sl = Slider(min=0, max=20, size_hint=(None, None),
            value=TA.MAX_STROKES, size=(200, 50))
        lbl = Label(text=str(TA.MAX_STROKES), size_hint=(None, None),
                    size=(100, 50))

        def upd_slider(*l):
            TA.MAX_STROKES = int(sl.value)
            lbl.text = str(int(sl.value))
        sl.bind(value=upd_slider)

        self.add_widget(sl)
        self.add_widget(lbl)

    def _setup_temporal(self):
        txt = "Temporal Window\n"
        txt += "How long should we wait from a touch up event before\n"
        txt += "attempting to recognize the gesture?"
        self.add_widget(Label(text=txt, size_hint=(None, None)))

        sl = Slider(min=0, max=20, size_hint=(None, None),
            value=TA.TEMPORAL_WINDOW, size=(200, 50))
        lbl = Label(text=str(round(TA.TEMPORAL_WINDOW, 1)),
                    size_hint=(None, None), size=(100, 50))

        def upd_slider(*l):
            TA.TEMPORAL_WINDOW = sl.value
            lbl.text = str(round(sl.value, 1))
        sl.bind(value=upd_slider)

        self.add_widget(sl)
        self.add_widget(lbl)

    def _setup_resulttime(self):
        txt = "Result Timeout\n"
        txt += "How long should the result display on screen?\n"
        self.add_widget(Label(text=txt, size_hint=(None, None)))

        sl = Slider(min=1, max=60, size_hint=(None, None),
            value=TA.RESULT_TIMEOUT, size=(200, 50))
        lbl = Label(text=str(round(TA.RESULT_TIMEOUT, 1)),
                    size_hint=(None, None), size=(100, 50))

        def upd_slider(*l):
            TA.RESULT_TIMEOUT = sl.value
            lbl.text = str(round(sl.value, 1))
        sl.bind(value=upd_slider)
        self.add_widget(sl)
        self.add_widget(lbl)
