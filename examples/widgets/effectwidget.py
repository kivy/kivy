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
                                   effect_mix,
                                   effect_flash,
                                   effect_blur_h,
                                   effect_blur_v,
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
            if text == 'mix':
                effects.append(effect_mix)
            if text == 'flash':
                effects.append(effect_flash)
            if text == 'blur_h':
                effects.append(effect_blur_h)
            if text == 'blur_v':
                effects.append(effect_blur_v)
            if text == 'plasma':
                effects.append(effect_plasma)
        if self.effectwidget:
            self.effectwidget.effects = effects

example = Builder.load_string('''
#:import Vector kivy.vector.Vector
BoxLayout:
    orientation: 'vertical'
    BoxLayout:
        EffectWidget:
            id: effect1
            Widget:
                canvas:
                    Color:
                        rgba: 1, 0, 0, 1
                    Ellipse:
                        pos: Vector(self.pos) + 0.5*Vector(self.size)
                        size: 0.4*Vector(self.size)
                    Color:
                        rgba: 0, 1, 0.3, 1
                    Ellipse:
                        pos: Vector(self.pos) + 0.1*Vector(self.size)
                        size: 0.6*Vector(self.size)
                    Color:
                        rgba: 0.5, 0.5, 0.2, 1
                    Ellipse:
                        pos: Vector(self.pos) + Vector([0, 0.6])*Vector(self.size)
                        size: 0.4*Vector(self.size)
                    Color:
                        rgba: 1, 0.8, 0.1, 1
                    Ellipse:
                        pos: Vector(self.pos) + Vector([0.5, 0])*Vector(self.size)
                        size: 0.4*Vector(self.size)
                    Color:
                        rgba: 0, 0, 0.8, 1
                    Line:
                        points:
                            [self.x, self.y,
                            self.x + self.width, self.y + 0.3*self.height,
                            self.x + 0.2*self.width, self.y + 0.1*self.height,
                            self.x + 0.85*self.width, self.y + 0.72*self.height,
                            self.x + 0.31*self.width, self.y + 0.6*self.height,
                            self.x, self.top]
                        width: 1
                    Color:
                        rgba: 0, 0.9, 0.1, 1
                    Line:
                        points:
                            [self.x + self.width, self.y + self.height,
                            self.x + 0.35*self.width, self.y + 0.6*self.height,
                            self.x + 0.7*self.width, self.y + 0.15*self.height,
                            self.x + 0.2*self.width, self.y + 0.22*self.height,
                            self.x + 0.3*self.width, self.y + 0.92*self.height]
                        width: 2
        EffectWidget:
            id: effect2
            Widget:
                canvas:
                    Color:
                        rgba: 1, 0, 0, 1
                    Ellipse:
                        pos: Vector(self.pos) + 0.5*Vector(self.size)
                        size: 0.4*Vector(self.size)
                    Color:
                        rgba: 0, 1, 0.3, 1
                    Ellipse:
                        pos: Vector(self.pos) + 0.1*Vector(self.size)
                        size: 0.6*Vector(self.size)
                    Color:
                        rgba: 0.5, 0.5, 0.2, 1
                    Ellipse:
                        pos: Vector(self.pos) + Vector([0, 0.6])*Vector(self.size)
                        size: 0.4*Vector(self.size)
                    Color:
                        rgba: 1, 0.8, 0.1, 1
                    Ellipse:
                        pos: Vector(self.pos) + Vector([0.5, 0])*Vector(self.size)
                        size: 0.4*Vector(self.size)
                    Color:
                        rgba: 0, 0, 0.8, 1
                    Line:
                        points:
                            [self.x, self.y,
                            self.x + self.width, self.y + 0.3*self.height,
                            self.x + 0.2*self.width, self.y + 0.1*self.height,
                            self.x + 0.85*self.width, self.y + 0.72*self.height,
                            self.x + 0.31*self.width, self.y + 0.6*self.height,
                            self.x, self.top]
                        width: 1
                    Color:
                        rgba: 0, 0.9, 0.1, 1
                    Line:
                        points:
                            [self.x + self.width, self.y + self.height,
                            self.x + 0.35*self.width, self.y + 0.6*self.height,
                            self.x + 0.7*self.width, self.y + 0.15*self.height,
                            self.x + 0.2*self.width, self.y + 0.22*self.height,
                            self.x + 0.3*self.width, self.y + 0.92*self.height]
                        width: 2
                    
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
    values:
        ['none', 'monochrome',
        'invert', 'plasma', 'mix',
        'flash', 'blur_h', 'blur_v']
        
''')

            


class EffectApp(App):
    def build(self):
        return example

EffectApp().run()
