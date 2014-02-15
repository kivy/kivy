'''
Example usage of the effectwidget.

Currently highly experimental.
'''

from kivy.app import App
from kivy.uix.effectwidget import EffectWidget
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatter import Scatter
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.properties import ObjectProperty

from kivy.uix.effectwidget import (effect_monochrome,
                                   effect_red,
                                   effect_blue,
                                   effect_green,
                                   effect_invert,
                                   effect_plasma)

class EffectSpinner(Spinner):
    pass

class SpinnerRow(BoxLayout):
    effectwidget = ObjectProperty()
    def update_effectwidget(self, *args):
        effects = []
        for child in self.children:
            text = child.text
            if text == 'none':
                pass
            if text == 'monochrome':
                effects.append(effect_monochrome)
            if text == 'red':
                effects.append(effect_red)
            if text == 'blue':
                effects.append(effect_blue)
            if text == 'green':
                effects.append(effect_green)
            if text == 'invert':
                effects.append(effect_invert)
            if text == 'plasma':
                effects.append(effect_plasma)
        if self.effectwidget:
            self.effectwidget.effects = effects

example = Builder.load_string('''
BoxLayout:
    orientation: 'vertical'
    BoxLayout:
        EffectWidget:
            id: effect1
            Image:
                size_hint: 1, 1
                pos_hint: {'x': 0, 'y': 0}
                source: 'colours.png'
                allow_stretch: True
                keep_ratio: False
            Button:
                text: 'Hello world'
                size_hint: None, None
                size: 150, 100
                pos_hint: {'center_x': 0.25, 'center_y': 0.5}
                on_press: print('Button pressed!')
        EffectWidget:
            id: effect2
            size: 100, 100
            Image:
                id: im
                pos: self.parent.pos
                size: self.parent.size
                source: 'colours2.png'
                allow_stretch: True
                keep_ratio: False
                on_touch_down: print(self.size, self.pos)
    SpinnerRow:
        effectwidget: effect1
        text: 'bg effects'
    SpinnerRow:
        effectwidget: effect2
        text: 'scatter effects'

<SpinnerRow>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(40)
    text: ''
    Label:
        text: root.text
    EffectSpinner:
        on_text: root.update_effectwidget()
    EffectSpinner:
        on_text: root.update_effectwidget()
    EffectSpinner:
        on_text: root.update_effectwidget()

<EffectSpinner>:
    text: 'none'
    values: ['none', 'monochrome', 'red', 'blue', 'green', 'invert', 'plasma']
        
''')

            


class EffectApp(App):
    def build(self):
        return example

EffectApp().run()
