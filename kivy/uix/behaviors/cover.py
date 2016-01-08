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
    """Behavior for covering image data inside a widget.

    Supposed to be used as mixin on Image or Video deriving objects.

    Example with Video as base class::

        class CoveredVideo(CoverBehavior, Video):

            def _on_video_frame(self, *largs):
                video = self._video
                if not video:
                    return
                texture = video.texture
                self.cover_origin_size = texture.size
                self.calculate_cover()
                self.duration = video.duration
                self.position = video.position
                self.texture = texture
                self.canvas.ask_update()
    """
    cover_size = ListProperty([0, 0])
    cover_pos = ListProperty([0, 0])

    def __init__(self, **kwargs):
        # original size
        self.cover_origin_size = None
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
        # return if no frame size yet
        if self.cover_origin_size is None:
            return
        origin_size = self.cover_origin_size
        size = self.size
        origin_appr = self._aspect_ratio_approximate(origin_size)
        crop_appr = self._aspect_ratio_approximate(size)
        # same aspect ratio
        if origin_appr == crop_appr:
            self.cover_size = self.size
            self.cover_pos = (0, 0)
            return
        # scale x
        if origin_appr < crop_appr:
            crop_size = self._scale_size(origin_size, (size[0], None))
            offset = (0, ((crop_size[1] - size[1]) / 2) * -1)
        # scale y
        if origin_appr > crop_appr:
            crop_size = self._scale_size(origin_size, (None, size[1]))
            offset = (((crop_size[0] - size[0]) / 2) * -1, 0)
        # set background size and position
        self.cover_size = crop_size
        self.cover_pos = offset
