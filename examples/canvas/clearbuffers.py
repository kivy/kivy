__all__ = ('FboFloatLayout', )


from kivy.graphics import Color, Rectangle, Canvas, ClearBuffers, ClearColor
from kivy.graphics.fbo import Fbo
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty, NumericProperty

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
            ClearColor(0,0,0,0)
            ClearBuffers()

        # wait that all the instructions are in the canvas to set texture
        self.texture = self.fbo.texture
        super(FboFloatLayout, self).__init__(**kwargs)

    def add_widget(self, *largs):
        # trick to attach graphics instructino to fbo instead of canvas
        canvas = self.canvas
        self.canvas = self.fbo
        ret = super(FboFloatLayout, self).add_widget(*largs)
        self.canvas = canvas
        return ret

    def remove_widget(self, *largs):
        canvas = self.canvas
        self.canvas = self.fbo
        super(FboFloatLayout, self).remove_widget(*largs)
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



from kivy.app import App
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.factory import Factory as F

class ScreenLayerApp(App):
    def build(self):

        f = FboFloatLayout()
        b = F.Button(text="FBO", size_hint=(None, None))
        f.add_widget(b)

        def anim_btn(*args):
            Animation(x=f.width-b.width).start(b)
        b.bind(on_press=anim_btn)

        #before this or calback instruction was only way...
        #so no way to avoid going into python instead of stayingin c
        #def clear_fb(*args):
        #    f.fbo.bind()
        #    f.fbo.clear_buffer()
        #    f.fbo.release()
        #Window.bind(on_draw=clear_fb)

        return f


if __name__ == "__main__":
    ScreenLayerApp().run()
