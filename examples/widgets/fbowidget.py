'''
FBO example
===========

This is an example of how to use FBO (Frame Buffer Object) to speedup graphics.
An Fbo is like a texture that you can draw on it.

By default, all the children are added in the canvas of the parent.
When you are displaying thousand of widget, you'll do thousands of graphics
instructions each frame.
The idea is to do this drawing only one time in a Fbo, and then, draw the Fbo
every frame instead of all children's graphics instructions.

We created a FboFloatLayout that create his canvas, and a Fbo.
After the Fbo is created, we are adding Color and Rectangle instruction to
display the texture of the Fbo itself.
The overload of on_pos/on_size are here to update size of Fbo if needed, and
adapt the position/size of the rectangle too.

Then, when a child is added or removed, we are redirecting addition/removal of
graphics instruction to our Fbo. This is why add_widget/remove_widget are
overloaded too.

.. note::

    This solution can be helpful but not ideal. Multisampling are not available
    in Framebuffer. We will work to add the support of it if the hardware is
    capable of, but it could be not the same.

'''


# needed to create Fbo, must be resolved in future kivy version
from kivy.core.window import Window

from kivy.graphics import Color, Rectangle, Canvas
from kivy.graphics.fbo import Fbo
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty


class FboFloatLayout(FloatLayout):

    texture = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.canvas = Canvas()
        with self.canvas:
            self.fbo = Fbo(size=self.size)
            Color(1, 1, 1)
            self.fbo_rect = Rectangle()

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


if __name__ == '__main__':
    from kivy.uix.button import Button
    from kivy.app import App

    class TestFboApp(App):
        def build(self):

            # test with FboFloatLayout or FloatLayout
            # comment/uncomment to test it
            root = FboFloatLayout()
            #root = FloatLayout()

            # this part of creation can be slow. try to optimize the loop a
            # little bit.
            s = 30
            size = (s, s)
            sh = (None, None)
            add = root.add_widget
            print('Creating 5000 widgets...')
            for i in range(5000):
                x = (i % 40) * s
                y = int(i / 40) * s
                add(Button(text=str(i), pos=(x, y), size_hint=sh, size=size))
                if i % 1000 == 1000 - 1:
                    print(5000 - i - 1, 'left...')

            return root

    TestFboApp().run()

