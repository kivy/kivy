'''
Image
=====
'''

__all__ = ('Image', )

from kivy.uix.widget import Widget
from kivy.core.image import Image as CoreImage
from kivy.resources import resource_find
from kivy.properties import StringProperty, ObjectProperty, ListProperty


class Image(Widget):

    #: Filename of the image
    source = StringProperty(None)

    #: Texture of the label
    texture = ObjectProperty(None, allownone=True)

    #: Texture size of the label
    texture_size = ListProperty([0, 0])

    def on_source(self, instance, value):
        if not value:
            self.texture = None
        else:
            filename = resource_find(value)
            image = CoreImage(filename)
            self.texture = image.texture
            self.texture_size = list(self.texture.size)
