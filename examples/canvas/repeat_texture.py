'''
Repeat Texture on Resize
========================

This examples repeats the letter 'K' (mtexture1.png) 64 times in a window.
You should see 8 rows and 8 columns of white K letters, along a label
showing the current size. As you resize the window, it stays an 8x8.
This example includes a label with a colored background.

Note the image mtexture1.png is a white 'K' on a transparent background, which
makes it hard to see.
'''

from kivy.app import App
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.properties import ObjectProperty, ListProperty
from kivy.lang import Builder

kv = '''
<LabelOnBackground>:
    canvas.before:
        Color:
            rgb: self.background
        Rectangle:
            pos: self.pos
            size: self.size

FloatLayout:
    canvas.before:
        Color:
            rgb: 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size
            texture: app.texture

    LabelOnBackground:
        text: '{} (try to resize the window)'.format(root.size)
        color: (0.4, 1, 1, 1)
        background: (.3, .3, .3)
        pos_hint: {'center_x': .5, 'center_y': .5 }
        size_hint: None, None
        height: 30
        width: 250

'''


class LabelOnBackground(Label):
    background = ListProperty((0.2, 0.2, 0.2))


class RepeatTexture(App):

    texture = ObjectProperty()

    def build(self):
        self.texture = Image(source='mtexture1.png').texture
        self.texture.wrap = 'repeat'
        self.texture.uvsize = (8, 8)
        return Builder.load_string(kv)


RepeatTexture().run()
