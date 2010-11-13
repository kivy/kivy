'''
Video widget
'''

__all__ = ('Video', )

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.core.video import Video as CoreVideo
from kivy.resources import resource_find
from kivy.c_ext.properties import StringProperty, ObjectProperty, \
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
        Clock.unschedule(self._trigger_video_update)
        if not value:
            self._video = None
            self.texture = None
        else:
            filename = resource_find(value)
            self._video = CoreVideo(filename=filename)
            self._video.bind(on_load=self._video_loaded)
            if self.play:
                self._video.play()
            Clock.schedule_interval(self._trigger_video_update, 1 / 30.)

    def _video_loaded(self, *largs):
        self.texture = self._video.texture
        self.texture_size = list(self.texture.size)

    def on_play(self, instance, value):
        if not self._video:
            return
        if value:
            self._video.play()
        else:
            self._video.stop()

    def _trigger_video_update(self, *largs):
        if not self._video:
            Clock.unschedule(self._trigger_video_update)
            return
        self._video.update()
        self.duration = self._video.duration
        self.position = self._video.position
        #self.canvas.trigger()
