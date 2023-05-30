'''
FBO Canvas
==========

This demonstrates a layout using an FBO (Frame Buffer Off-screen)
instead of a plain canvas. You should see a black canvas with a
button labelled 'FBO' in the bottom left corner. Clicking it
animates the button moving right to left.
'''

__all__ = ('FboFloatLayout', )

from kivy.graphics import Color, Rectangle, Canvas, ClearBuffers, ClearColor
from kivy.graphics.fbo import Fbo
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty, NumericProperty
from kivy.app import App
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.factory import Factory


class FboFloatLayout(FloatLayout):

    texture = ObjectProperty(None, allownone=True)

    alpha = NumericProperty(1)

    def __init__(self, **kwargs):
        self.canvas = Canvas()
        with self.canvas:
            self.fbo = Fbo(size=self.size)
            self.fbo_color = Color(1, 1, 1, 1)
            self.fbo_rect = Rectangle()

        with self.fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()

        # wait that all the instructions are in the canvas to set texture
        self.texture = self.fbo.texture
        super(FboFloatLayout, self).__init__(**kwargs)

    def add_widget(self, *args, **kwargs):
        # trick to attach graphics instruction to fbo instead of canvas
        canvas = self.canvas
        self.canvas = self.fbo
        ret = super(FboFloatLayout, self).add_widget(*args, **kwargs)
        self.canvas = canvas
        return ret

    def remove_widget(self, *args, **kwargs):
        canvas = self.canvas
        self.canvas = self.fbo
        super(FboFloatLayout, self).remove_widget(*args, **kwargs)
        self.canvas = canvas

    def on_size(self, instance, value):
        self.fbo.size = value
        self.texture = self.fbo.texture
        self.fbo_rect.size = value

    def on_pos(self, instance, value):
        self.fbo_rect.pos = value

    def on_texture(self, instance, value):
        self.fbo_rect.texture = value

    def on_alpha(self, instance, value):
        self.fbo_color.rgba = (1, 1, 1, value)


class ScreenLayerApp(App):
    def build(self):

        f = FboFloatLayout()
        b = Factory.Button(text="FBO", size_hint=(None, None))
        f.add_widget(b)

        def anim_btn(*args):
            if b.pos[0] == 0:
                Animation(x=f.width - b.width).start(b)
            else:
                Animation(x=0).start(b)
        b.bind(on_press=anim_btn)

        return f


if __name__ == "__main__":
    ScreenLayerApp().run()
