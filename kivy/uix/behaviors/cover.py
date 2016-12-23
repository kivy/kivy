'''
Cover Behavior
==============

The :class:`~kivy.uix.behaviors.cover.CoverBehavior`
`mixin <https://en.wikipedia.org/wiki/Mixin>`_ is intended for rendering
textures to full widget size keeping the aspect ratio of the original texture.

Use cases are i.e. rendering full size background images or video content in
a dynamic layout.

For an overview of behaviors, please refer to the :mod:`~kivy.uix.behaviors`
documentation.

Example
-------

The following example adds cover behavior to an image::

    from kivy.app import App
    from kivy.uix.behaviors import CoverBehavior
    from kivy.uix.image import Image


    class CoverImage(CoverBehavior, Image):

        def __init__(self, **kwargs):
            super(CoverImage, self).__init__(**kwargs)
            texture = self._coreimage.texture
            self.reference_size = texture.size
            self.texture = texture


    class MainApp(App):

        def build(self):
            return CoverImage(source='image.jpg')

    MainApp().run()

See :class:`~kivy.uix.behaviors.cover.CoverBehavior` for details.
'''

__all__ = ('CoverBehavior', )

from decimal import Decimal
from kivy.lang import Builder
from kivy.properties import ListProperty


Builder.load_string("""
<-CoverBehavior>:
    canvas.before:
        StencilPush
        Rectangle:
            pos: self.pos
            size: self.size
        StencilUse
    canvas:
        Rectangle:
            texture: self.texture
            size: self.cover_size
            pos: self.cover_pos
    canvas.after:
        StencilUnUse
        Rectangle:
            pos: self.pos
            size: self.size
        StencilPop
""")


class CoverBehavior(object):
    '''The CoverBehavior `mixin <https://en.wikipedia.org/wiki/Mixin>`_
    provides rendering a texture covering full widget size keeping aspect ratio
    of the original texture.

    .. versionadded:: 1.10.0
    '''

    reference_size = ListProperty([])
    '''Reference size used for aspect ratio approximation calculation.

    :attr:`reference_size` is a :class:`~kivy.properties.ListProperty` and
    defaults to `[]`.
    '''

    cover_size = ListProperty([0, 0])
    '''Size of the aspect ratio aware texture. Gets calculated in
    ``CoverBehavior.calculate_cover``.

    :attr:`cover_size` is a :class:`~kivy.properties.ListProperty` and
    defaults to `[0, 0]`.
    '''

    cover_pos = ListProperty([0, 0])
    '''Position of the aspect ratio aware texture. Gets calculated in
    ``CoverBehavior.calculate_cover``.

    :attr:`cover_pos` is a :class:`~kivy.properties.ListProperty` and
    defaults to `[0, 0]`.
    '''

    def __init__(self, **kwargs):
        super(CoverBehavior, self).__init__(**kwargs)
        # bind covering
        self.bind(
            size=self.calculate_cover,
            pos=self.calculate_cover
        )

    def _aspect_ratio_approximate(self, size):
        # return a decimal approximation of an aspect ratio.
        return Decimal('%.2f' % (float(size[0]) / size[1]))

    def _scale_size(self, size, sizer):
        # return scaled size based on sizer, where sizer (n, None) scales x
        # to n and (None, n) scales y to n
        size_new = list(sizer)
        i = size_new.index(None)
        j = i * -1 + 1
        size_new[i] = (size_new[j] * size[i]) / size[j]
        return tuple(size_new)

    def calculate_cover(self, *args):
        # return if no reference size yet
        if not self.reference_size:
            return
        size = self.size
        origin_appr = self._aspect_ratio_approximate(self.reference_size)
        crop_appr = self._aspect_ratio_approximate(size)
        # same aspect ratio
        if origin_appr == crop_appr:
            crop_size = self.size
            offset = (0, 0)
        # scale x
        elif origin_appr < crop_appr:
            crop_size = self._scale_size(self.reference_size, (size[0], None))
            offset = (0, ((crop_size[1] - size[1]) / 2) * -1)
        # scale y
        else:
            crop_size = self._scale_size(self.reference_size, (None, size[1]))
            offset = (((crop_size[0] - size[0]) / 2) * -1, 0)
        # set background size and position
        self.cover_size = crop_size
        self.cover_pos = offset
