'''
Video
=====
'''

__all__ = ('Video', )

from kivy.uix.widget import Widget
from kivy.core.video import Video as CoreVideo
from kivy.resources import resource_find
from kivy.properties import StringProperty, ObjectProperty, \
        ListProperty, BooleanProperty, NumericProperty

class Video(Widget):

    #: Filename of the Video
    source = StringProperty(None)

    #: Texture of the label
    texture = ObjectProperty(None, allownone=True)

    #: Texture size of the label
    texture_size = ListProperty([0, 0])

    #: Playing
    play = BooleanProperty(False)

    #: Position
    position = NumericProperty(0)

    #: Duration
    duration = NumericProperty(0)

    #: Volume
    volume = NumericProperty(1.)

    def __init__(self, **kwargs):
        self._video = None
        super(Video, self).__init__(**kwargs)

    def on_source(self, instance, value):
        if not value:
            self._video = None
            self.texture = None
        else:
            filename = resource_find(value)
            self._video = CoreVideo(filename=filename)
            self._video.bind(on_load=self._on_video_load,
                             on_frame=self._on_video_frame)
            if self.play:
                self._video.play()

    def on_play(self, instance, value):
        if not self._video:
            return
        if value:
            self._video.play()
        else:
            self._video.stop()

    def _on_video_frame(self, *largs):
        self.duration = self._video.duration
        self.position = self._video.position

    def _on_video_load(self, *largs):
        self.texture = self._video.texture
        self.texture_size = list(self.texture.size)

