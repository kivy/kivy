'''
Image mipmap
============

Difference between a mipmapped image and no mipmap image.
The lower image is normal, and the top image is mipmapped.
'''

import kivy
kivy.require('1.0.7')

from kivy.app import App
from kivy.uix.scatter import ScatterPlane
from kivy.uix.image import Image
from os.path import join

class LabelMipmapTest(App):
    def build(self):
        s = ScatterPlane(scale=.5)
        filename = join(kivy.kivy_data_dir, 'logo', 'kivy-icon-256.png')
        l1 = Image(source=filename, pos=(400, 100), size=(256, 256))
        l2 = Image(source=filename, pos=(400, 356), size=(256, 256),
                   mipmap=True)
        s.add_widget(l1)
        s.add_widget(l2)
        return s

if __name__ in ('__main__', '__android__'):
    LabelMipmapTest().run()
