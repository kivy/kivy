'''
Video player
============

.. versionadded:: 1.1.2

The video player widget can be used to play video and let the user control the
play/pause, volume and seek. The widget cannot be customized a lot, due to the
complex assembly of lot of base widgets.

.. image:: images/videoplayer.jpg
    :align: center

'''

__all__ = ('VideoPlayer', )

from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, \
        NumericProperty
from kivy.animation import Animation
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.video import Video
from kivy.uix.video import Image
from kivy.factory import Factory


class VideoPlayerVolume(Image):
    video = ObjectProperty(None)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        touch.grab(self)
        # save the current volume and delta to it
        touch.ud[self.uid] = [self.video.volume, 0]
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return
        # calculate delta
        dy = abs(touch.y - touch.oy)
        if dy > 10:
            dy = min(dy - 10, 100)
            touch.ud[self.uid][1] = dy
            self.video.volume = dy / 100.
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return
        touch.ungrab(self)
        dy = abs(touch.y - touch.oy)
        if dy < 10:
            if self.video.volume > 0:
                self.video.volume = 0
            else:
                self.video.volume = 1.


class VideoPlayerPlayPause(Image):
    video = ObjectProperty(None)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.video.play = not self.video.play
            return True


class VideoPlayerProgressBar(ProgressBar):
    video = ObjectProperty(None)
    seek = NumericProperty(None, allownone=True)
    alpha = NumericProperty(1.)

    def __init__(self, **kwargs):
        super(VideoPlayerProgressBar, self).__init__(**kwargs)
        self.bubble = Factory.Bubble(size=(50, 44))
        self.bubble_label = Factory.Label(text='0:00')
        self.bubble.add_widget(self.bubble_label)
        self.add_widget(self.bubble)
        self.bind(pos=self._update_bubble,
            size=self._update_bubble,
            seek=self._update_bubble)

    def on_video(self, instance, value):
        self.video.bind(position=self._update_bubble, play=self._showhide_bubble)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return
        self._show_bubble()
        touch.grab(self)
        touch.ud[self.uid] = self._update_seek(touch.x)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return
        touch.ud[self.uid] = self._update_seek(touch.x)
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return
        touch.ungrab(self)
        self.video.seek(self.seek)
        self.seek = None
        self._hide_bubble()
        return True

    def _update_seek(self, x):
        if self.width == 0:
            return
        x = max(self.x, min(self.right, x)) - self.x
        self.seek = x / float(self.width)

    def _show_bubble(self):
        self.alpha = 1
        Animation.stop_all(self, 'alpha')

    def _hide_bubble(self):
        self.alpha = 1.
        Animation(alpha=0, d=4, t='in_out_expo').start(self)

    def on_alpha(self, instance, value):
        self.bubble.background_color = (1, 1, 1, value)
        self.bubble_label.color = (1, 1, 1, value)

    def _update_bubble(self, *l):
        seek = self.seek
        if self.seek is None:
            if self.video.duration == 0:
                seek = 0
            else:
                seek = self.video.position / self.video.duration
        # convert to minutes:seconds
        d = self.video.duration * seek
        minutes = int(d / 60)
        seconds = int(d - (minutes * 60))
        # fix bubble label & position
        self.bubble_label.text = '%d:%02d' % (minutes, seconds)
        self.bubble.center_x = self.x + seek * self.width
        self.bubble.y = self.top

    def _showhide_bubble(self, instance, value):
        if value:
            self._hide_bubble()
        else:
            self._show_bubble()


class VideoPlayerPreview(FloatLayout):
    source = ObjectProperty(None)
    video = ObjectProperty(None)
    click_done = BooleanProperty(False)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.click_done:
            self.click_done = True
            self.video.play = True
        return True


class VideoPlayer(GridLayout):
    '''VideoPlayer class, see module documentation for more information.
    '''

    source = StringProperty(None)
    '''Source of the video to read

    :data:`source` a :class:`~kivy.properties.StringProperty`, default to None.
    '''

    thumbnail = StringProperty(None)
    '''Thumbnail of the video to show. If None, it will try to search the thumbnail from the :data:`source` + .png.

    :data:`thumbnail` a :class:`~kivy.properties.StringProperty`, default to None.
    '''

    duration = NumericProperty(-1)
    '''Duration of the video. The duration is default to -1, and set to real
    duration when the video is loaded.

    :data:`duration` is a :class:`~kivy.properties.NumericProperty`, default to
    -1.
    '''

    position = NumericProperty(0)
    '''Position of the video between 0 and :data:`duration`. The position is
    default to -1, and set to real position when the video is loaded.

    :data:`position` is a :class:`~kivy.properties.NumericProperty`, default to
    -1.
    '''

    volume = NumericProperty(1.0)
    '''Volume of the video, in the range 0-1. 1 mean full volume, 0 mean mute.

    :data:`volume` is a :class:`~kivy.properties.NumericProperty`, default to
    1.
    '''

    play = BooleanProperty(False)
    '''Boolean, indicates if the video is playing.
    You can start/stop the video by setting this property. ::

        # start playing the video at creation
        video = VideoPlayer(source='movie.mkv', play=True)

        # create the video, and start later
        video = VideoPlayer(source='movie.mkv')
        # and later
        video.play = True

    :data:`play` is a :class:`~kivy.properties.BooleanProperty`, default to
    False.
    '''

    image_overlay_play = StringProperty('atlas://data/images/defaulttheme/player-play-overlay')
    '''Image filename used to show an "play" overlay when the video is not yet started.

    :data:`image_overlay_play` a :class:`~kivy.properties.StringProperty`
    '''

    image_loading = StringProperty('data/images/image-loading.gif')
    '''Image filename used when the video is loading.

    :data:`image_loading` a :class:`~kivy.properties.StringProperty`
    '''

    image_play = StringProperty('atlas://data/images/defaulttheme/media-playback-start')
    '''Image filename used for the "Play" button.

    :data:`image_loading` a :class:`~kivy.properties.StringProperty`
    '''

    image_pause = StringProperty('atlas://data/images/defaulttheme/media-playback-pause')
    '''Image filename used for the "Pause" button.

    :data:`image_pause` a :class:`~kivy.properties.StringProperty`
    '''

    image_volumehigh = StringProperty('atlas://data/images/defaulttheme/audio-volume-high')
    '''Image filename used for the volume icon, when the volume is high.

    :data:`image_volumehigh` a :class:`~kivy.properties.StringProperty`
    '''

    image_volumemedium = StringProperty('atlas://data/images/defaulttheme/audio-volume-medium')
    '''Image filename used for the volume icon, when the volume is medium.

    :data:`image_volumemedium` a :class:`~kivy.properties.StringProperty`
    '''

    image_volumelow = StringProperty('atlas://data/images/defaulttheme/audio-volume-low')
    '''Image filename used for the volume icon, when the volume is low.

    :data:`image_volumelow` a :class:`~kivy.properties.StringProperty`
    '''

    image_volumemuted = StringProperty('atlas://data/images/defaulttheme/audio-volume-muted')
    '''Image filename used for the volume icon, when the volume is muted.

    :data:`image_volumemuted` a :class:`~kivy.properties.StringProperty`
    '''

    # internals
    container = ObjectProperty(None)

    def __init__(self, **kwargs):
        self._video = None
        self._image = None
        super(VideoPlayer, self).__init__(**kwargs)
        self._load_thumbnail()

    def on_source(self, instance, value):
        # we got a value, try to see if we have an image for it
        self._load_thumbnail()

    def _load_thumbnail(self):
        if not self.container:
            return
        self.container.clear_widgets()
        # get the source, remove extension, and use png
        thumbnail = self.thumbnail
        if thumbnail is None:
            filename = self.source.rsplit('.', 1)
            thumbnail = filename[0] + '.png'
        self._image = VideoPlayerPreview(source=thumbnail, video=self)
        self.container.add_widget(self._image)

    def on_play(self, instance, value):
        if self._video is None:
            self._video = Video(source=self.source, play=True,
                    volume=self.volume)
            self._video.bind(texture=self._play_started,
                    duration=self.setter('duration'),
                    position=self.setter('position'),
                    volume=self.setter('volume'))
        self._video.play = value

    def on_volume(self, instance, value):
        if not self._video:
            return
        self._video.volume = value

    def seek(self, percent):
        '''Change the position to a percentage of duration. Percentage must be a
        value between 0-1.

        .. warning::

            Calling seek() before video is loaded have no impact.
        '''
        if not self._video:
            return
        self._video.seek(percent)

    def _play_started(self, instance, value):
        self.container.clear_widgets()
        self.container.add_widget(self._video)


if __name__ == '__main__':
    import sys
    from kivy.base import runTouchApp
    runTouchApp(VideoPlayer(source=sys.argv[1]))
