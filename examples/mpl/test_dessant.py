from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

import numpy as np
import matplotlib.pyplot as plt
from kivy.ext.mpl.backend_kivy import FigureCanvas


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

    def get_fc(self):
        fig, ax = plt.subplots()
        x = np.linspace(0, 10)
        with plt.style.context('fivethirtyeight'):
            ax.plot(x, np.sin(x) + x + np.random.randn(50))
            ax.plot(x, np.sin(x) + 0.5 * x + np.random.randn(50))
            ax.plot(x, np.sin(x) + 2 * x + np.random.randn(50))
        return FigureCanvas(fig)

    def add_plot(self):
        self.add_widget(self.get_fc())
        self.add_widget(self.get_fc())


class TestApp(App):
    def build(self):
        return Test()

if __name__ == '__main__':
    TestApp().run()

