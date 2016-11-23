from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

import numpy as np
import matplotlib.pyplot as plt
from kivy.ext.mpl.backend_kivy import FigureCanvas


def enter_axes(event):
    print('enter_axes', event.inaxes)
    event.inaxes.patch.set_facecolor('yellow')
    event.canvas.draw()


def leave_axes(event):
    print('leave_axes', event.inaxes)
    event.inaxes.patch.set_facecolor('white')
    event.canvas.draw()


def enter_figure(event):
    print('enter_figure', event.canvas.figure)
    event.canvas.figure.patch.set_facecolor('red')
    event.canvas.draw()


def leave_figure(event):
    print('leave_figure', event.canvas.figure)
    event.canvas.figure.patch.set_facecolor('grey')
    event.canvas.draw()


kv = """
<Test>:
    orientation: 'vertical'
    Button:
        size_hint_y: None
        height: 40
"""

Builder.load_string(kv)


class Test(BoxLayout):
    def __init__(self, *args, **kwargs):
        super(Test, self).__init__(*args, **kwargs)
        self.add_plot()

    def get_fc(self, i):
        fig1 = plt.figure()
        fig1.suptitle('mouse hover over figure or axes to trigger events' +
                      str(i))
        ax1 = fig1.add_subplot(211)
        ax2 = fig1.add_subplot(212)
        wid = FigureCanvas(fig1)
        fig1.canvas.mpl_connect('figure_enter_event', enter_figure)
        fig1.canvas.mpl_connect('figure_leave_event', leave_figure)
        fig1.canvas.mpl_connect('axes_enter_event', enter_axes)
        fig1.canvas.mpl_connect('axes_leave_event', leave_axes)
        return wid

    def add_plot(self):
        self.add_widget(self.get_fc(1))
        self.add_widget(self.get_fc(2))


class TestApp(App):
    def build(self):
        return Test()

if __name__ == '__main__':
    TestApp().run()

