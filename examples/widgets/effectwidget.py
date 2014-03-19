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

# from kivy.uix.effectwidget import (effect_monochrome,
#                                    effect_red,
#                                    effect_blue,
#                                    effect_green,
#                                    effect_invert,
#                                    effect_mix,
#                                    effect_blur_h,
#                                    effect_blur_v,
#                                    effect_postprocessing,
#                                    effect_pixelate,
#                                    effect_waterpaint,
#                                    effect_fxaa,
#                                    effect_plasma)

from kivy.uix.effectwidget import (MonochromeEffect,
                                   InvertEffect,
                                   ScanlinesEffect,
                                   ChannelMixEffect,
                                   ScanlinesEffect,
                                   FXAAEffect,
                                   PixelateEffect,
                                   HorizontalBlurEffect,
                                   VerticalBlurEffect)
                                   


class ComparisonWidget(EffectWidget):
    pass

class EffectSpinner(Spinner):
    pass

class SpinnerRow(BoxLayout):
    effectwidget = ObjectProperty()
    def update_effectwidget(self, *args):
        effects = []
        for child in self.children[::-1]:
            text = child.text
            if text == 'none':
                pass
            if text == 'fxaa':
                effects.append(FXAAEffect())
            if text == 'monochrome':
                effects.append(MonochromeEffect())
            if text == 'invert':
                effects.append(InvertEffect())
            if text == 'mix':
                effects.append(ChannelMixEffect())
            if text == 'flash':
                effects.append(FlashEffect())
            if text == 'blur_h':
                effects.append(HorizontalBlurEffect())
            if text == 'blur_v':
                effects.append(VerticalBlurEffect())
            if text == 'postprocessing':
                effects.append(ScanlinesEffect())
            if text == 'pixelate':
                effects.append(PixelateEffect())
        if self.effectwidget:
            self.effectwidget.effects = effects

example = Builder.load_string('''
#:import Vector kivy.vector.Vector
BoxLayout:
    orientation: 'vertical'
    BoxLayout:
        ComparisonWidget:
            id: effect1
        ComparisonWidget:
            id: effect2
    SpinnerRow:
        effectwidget: effect1
        text: 'left effects'
    SpinnerRow:
        effectwidget: effect2
        text: 'right effects'


<ComparisonWidget>:
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
                rgba: 0.5, 0.3, 0.8, 1
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
        ['none', 'fxaa', 'monochrome',
        'invert', 'mix',
        'blur_h', 'blur_v',
        'postprocessing', 'pixelate',]
        
''')


class EffectApp(App):
    def build(self):
        return example


EffectApp().run()
