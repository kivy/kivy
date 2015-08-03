'''
StrokeCanvas Demonstration
=======================================

This demonstrates the use of a StrokeCanvas, properties and behavior that can
be changed. It binds as well events produced for the StrokeCanvas.
Additionally, it shows the bounding box of a stroke with a fade rectangle.

'''

from kivy.app import App
from kivy.uix.inkcanvas import StrokeCanvasBehavior, Stroke, StrokeRect,\
        StrokePoint
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle
from functools import partial

from kivy.ext.mpl.backend_kivy import FigureCanvasKivy as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np


class StrokeFigureCanvas(StrokeCanvasBehavior, FigureCanvas):
    def __init__(self, figure, **kwargs):
        super(StrokeFigureCanvas, self).__init__(figure=figure, **kwargs)


class StrokeCanvasFloat(StrokeCanvasBehavior, FloatLayout):
    pass


class StrokeCanvasTest(App):
    title = 'InkCanvas'
    strokes_collected = []
    drawn = False
    fig, ax = None, None
    chart = None

    def callback(self, button, result, *args):
        if self.inkc.mode == 'draw':
            self.inkc.mode = 'erase'
            button.text = 'Erase Mode'
        elif self.inkc.mode == 'erase':
            self.inkc.mode = 'draw'
            button.text = 'Draw Mode'

    def stroke_collected(self, layout, stroke):
        # Just to visualize the bounding box
#         rect = stroke.get_bounds()
#         with self.inkc.canvas:
#             Color(1, 1, 0, 0.3)
#             Rectangle(pos=(rect.left, rect.bottom),
#                 size=(rect.right - rect.left, rect.top - rect.bottom))
        self.strokes_collected.append(stroke)
#         self.createGraph()
#         self.inkc.add_widget(self.chart)

    def createGraph(self):
        ax = self.ax
        N = 5
        menMeans = (20, 35, 30, 35, 27)
        menStd = (2, 3, 4, 1, 2)
        ind = np.arange(N)  # the x locations for the groups
        width = 0.35       # the width of the bars
        self.fig, ax = plt.subplots(figsize=(5, 5), dpi = 100)
        fig1 = plt.gcf()
        rects1 = ax.bar(ind, menMeans, width, color='r', yerr=menStd)
        womenMeans = (25, 32, 34, 20, 25)
        womenStd = (3, 5, 2, 3, 3)
        ax.set_ylabel('Scores')
        ax.set_xticks(ind + width)
        ax.set_xticklabels(('G1', 'G2', 'G3', 'G4', 'G5'))
        self.chart = StrokeFigureCanvas(self.fig)
        self.chart.draw()

    def stroke_removed(self, layout, strk):
        pass

    def mode_changed(self, instance, value):
        pass

    def build(self):
        self.layout = FloatLayout()
        self.inkc = inkc = StrokeCanvasFloat(size_hint=(1, .85))
        inkc.stroke_color = 'darkblue'
        inkc.stroke_width = 2.0
        inkc.stroke_visibility = True
        inkc.stroke_opacity = 0.8
        inkc.bind(size=self._update_rect, pos=self._update_rect)
        inkc.bind(on_stroke_added=self.stroke_collected)
        inkc.bind(on_stroke_removed=self.stroke_removed)
        inkc.bind(mode=self.mode_changed)
        btn = Button(text='Draw Mode', size_hint=(1, .15),
                     pos_hint={'top': 1.0})
        btn.bind(on_press=partial(self.callback, btn))
        with inkc.canvas.before:
            Color(1.0, 1.0, 1.0, 1.0)
            self.rect = Rectangle(size=inkc.size, pos=inkc.pos)
        self.layout.add_widget(inkc)
        self.layout.add_widget(btn)
        return self.layout

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_pause(self):
        return True

if __name__ == '__main__':
    StrokeCanvasTest().run()

