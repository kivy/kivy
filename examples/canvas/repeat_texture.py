'''
Demonstrate repeating textures
==============================

This was a test to fix an issue with repeating texture and window reloading.
'''

from kivy.app import App
from kivy.uix.image import Image
from kivy.properties import ObjectProperty
from kivy.lang import Builder

kv = '''
FloatLayout:
    canvas.before:
        Color:
            rgb: 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size
            texture: app.texture

    Label:
        text: '{} (try to resize the window)'.format(root.size)
'''


class RepeatTexture(App):

    texture = ObjectProperty()

    def build(self):
        self.texture = Image(source='mtexture1.png').texture
        self.texture.wrap = 'repeat'
        self.texture.uvsize = (8, 8)
        return Builder.load_string(kv)

RepeatTexture().run()
