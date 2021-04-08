'''
Video
=====

The :class:`Video` widget is used to display video files and streams.
Depending on your Video core provider, platform, and plugins, you will
be able to play different formats. For example, the pygame video
provider only supports MPEG1 on Linux and OSX. GStreamer is more
versatile, and can read many video containers and codecs such as MKV,
OGV, AVI, MOV, FLV (if the correct gstreamer plugins are installed). Our
:class:`~kivy.core.video.VideoBase` implementation is used under the
hood.

Video loading is asynchronous - many properties are not available until
the video is loaded (when the texture is created)::

    def on_position_change(instance, value):
        print('The position in the video is', value)

    def on_duration_change(instance, value):
        print('The duration of the video is', value)

    video = Video(video_source='PandaSneezes.avi')
    video.bind(
        position=on_position_change,
        duration=on_duration_change
    )

One can define a preview image which gets displayed until the video is
started/loaded by passing ``preview_image`` to the constructor::

    video = Video(
        video_source='PandaSneezes.avi',
        preview_source='PandaSneezes_preview.png'
    )

One can display the placeholder image when the video stops by reacting on eos::

    def on_eos_change(self, inst, val):
        if val and self.preview_source:
            self.set_texture_from_resource(self.preview_source)

    video.bind(eos=on_eos_change)
'''

__all__ = ('Video', )

from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.core.video import Video as CoreVideo
from kivy.resources import resource_find
from kivy.properties import (BooleanProperty, NumericProperty, ObjectProperty,
                             OptionProperty, StringProperty)


class Video(Image):
    '''Video class. See module documentation for more information.
    '''

    source = StringProperty(None, allownone=True)
    '''Filename / source of your video.

    :attr:`source` is a :class:`~kivy.properties.StringProperty` and
    defaults to None.

    .. versionchanged:: 2.1.0
        While the use of :attr:`source` is the historical way for defining
        video source and stays supported for backward compatibility, it is
        recommended to use :attr:`video_source` instead.
    '''

    video_source = StringProperty(None, allownone=True)
    '''Filename / source of your video.

    :attr:`video_source` is a :class:`~kivy.properties.StringProperty` and
    defaults to None.

    Internally the widget uses :attr:`video_source` for referencing the video
    source.

    B/C compatibility to :attr:`source` is kept by setting :attr:`video_source`
    when :attr:`source` gets set, thus also keeps the behavior with reloading
    the video sane if this attribute gets changed on an instance of this class

    .. versionadded:: 2.1.0
    '''

    preview_source = StringProperty(None, allownone=True)
    '''Filename / source of a preview image displayed before video starts.

    :attr:`preview_source` is a :class:`~kivy.properties.StringProperty` and
    defaults to None.

    If set, it gets displayed until the video is loaded/started.

    .. versionadded:: 2.1.0
    '''

    state = OptionProperty('stop', options=('play', 'pause', 'stop'))
    '''String, indicates whether to play, pause, or stop the video::

        # start playing the video at creation
        video = Video(video_source='movie.mkv', state='play')

        # create the video, and start later
        video = Video(video_source='movie.mkv')
        # and later
        video.state = 'play'

    :attr:`state` is an :class:`~kivy.properties.OptionProperty` and defaults
    to 'stop'.
    '''

    play = BooleanProperty(False, deprecated=True)
    '''
    .. deprecated:: 1.4.0
        Use :attr:`state` instead.

    Boolean, indicates whether the video is playing or not.
    You can start/stop the video by setting this property::

        # start playing the video at creation
        video = Video(video_source='movie.mkv', play=True)

        # create the video, and start later
        video = Video(video_source='movie.mkv')
        # and later
        video.play = True

    :attr:`play` is a :class:`~kivy.properties.BooleanProperty` and defaults to
    False.

    .. deprecated:: 1.4.0
        Use :attr:`state` instead.
    '''

    eos = BooleanProperty(False)
    '''Boolean, indicates whether the video has finished playing or not
    (reached the end of the stream).

    :attr:`eos` is a :class:`~kivy.properties.BooleanProperty` and defaults to
    False.
    '''

    loaded = BooleanProperty(False)
    '''Boolean, indicates whether the video is loaded and ready for playback
    or not.

    .. versionadded:: 1.6.0

    :attr:`loaded` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    position = NumericProperty(-1)
    '''Position of the video between 0 and :attr:`duration`. The position
    defaults to -1 and is set to a real position when the video is loaded.

    :attr:`position` is a :class:`~kivy.properties.NumericProperty` and
    defaults to -1.
    '''

    duration = NumericProperty(-1)
    '''Duration of the video. The duration defaults to -1, and is set to a real
    duration when the video is loaded.

    :attr:`duration` is a :class:`~kivy.properties.NumericProperty` and
    defaults to -1.
    '''

    volume = NumericProperty(1.)
    '''Volume of the video, in the range 0-1. 1 means full volume, 0
    means mute.

    :attr:`volume` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 1.
    '''

    options = ObjectProperty({})
    '''Options to pass at Video core object creation.

    .. versionadded:: 1.0.4

    :attr:`options` is an :class:`kivy.properties.ObjectProperty` and defaults
    to {}.
    '''

    _video_load_event = None

    def __init__(self, **kwargs):
        # Case source is given. Use it as video_source if not present
        if kwargs.get('source') and not kwargs.get('video_source'):
            kwargs['video_source'] = kwargs['source']

        self._video = None
        super(Video, self).__init__(**kwargs)

        # Unbind texture_update on superclass to prevent updating texture
        # automatically once source gets set on instance of this class.
        self.funbind('source', self.texture_update)

        # Bind video loading if video_source or source property gets set.
        self.fbind('video_source', self._trigger_video_load)
        self.fbind('source', self._bc_video_load)

        if "eos" in kwargs:
            self.options["eos"] = kwargs["eos"]
        if self.video_source:
            self._trigger_video_load()

    def seek(self, percent, precise=True):
        '''Change the position to a percentage (strictly, a proportion)
           of duration.

        :Parameters:
            `percent`: float or int
                Position to seek as a proportion of the total duration,
                must be between 0-1.
            `precise`: bool, defaults to True
                Precise seeking is slower, but seeks to exact requested
                percent.

        .. warning::
            Calling seek() before the video is loaded has no effect.

        .. versionadded:: 1.2.0

        .. versionchanged:: 1.10.1
            The `precise` keyword argument has been added.
        '''
        if self._video is None:
            raise Exception('Video not loaded.')
        self._video.seek(percent, precise=precise)

    def _bc_video_load(self, inst, val):
        # B/C video loading behavior if source gets set on instance

        # Since we unbound the ``update_texture`` function from ``Image``
        # on ``source`` change, we need to update the texture manually to
        # ensure corrent B/C behavior when setting ``source`` property on
        # instance.
        self.set_texture_from_resource(val)
        self.video_source = val

    def _trigger_video_load(self, *largs):
        # Display preview image if set
        if self.preview_source:
            self.set_texture_from_resource(self.preview_source)
        ev = self._video_load_event
        if ev is None:
            ev = self._video_load_event = Clock.schedule_once(
                self._do_video_load, -1)
        ev()

    def _do_video_load(self, *largs):
        if CoreVideo is None:
            return
        self.unload()
        if not self.video_source:
            self._video = None
            self.texture = None
        else:
            filename = self.video_source
            # Check if filename is not url
            if '://' not in filename:
                filename = resource_find(filename)
            self._video = CoreVideo(filename=filename, **self.options)
            self._video.volume = self.volume
            self._video.bind(on_load=self._on_load,
                             on_frame=self._on_video_frame,
                             on_eos=self._on_eos)
            if self.state == 'play' or self.play:
                self._video.play()
            self.duration = 1.
            self.position = 0.

    def on_play(self, instance, value):
        value = 'play' if value else 'stop'
        return self.on_state(instance, value)

    def on_state(self, instance, value):
        if not self._video:
            return
        if value == 'play':
            if self.eos:
                self._video.stop()
                self._video.position = 0.
            self.eos = False
            self._video.play()
        elif value == 'pause':
            self._video.pause()
        else:
            self._video.stop()
            self._video.position = 0

    def _on_video_frame(self, *largs):
        video = self._video
        if not video:
            return
        self.duration = video.duration
        self.position = video.position
        self.texture = video.texture
        self.canvas.ask_update()

    def _on_eos(self, *largs):
        if self._video.eos != 'loop':
            self.state = 'stop'
            self.eos = True

    def _on_load(self, *largs):
        self.loaded = True
        self._on_video_frame(largs)

    def on_volume(self, instance, value):
        if self._video:
            self._video.volume = value

    def unload(self):
        '''Unload the video. The playback will be stopped.

        .. versionadded:: 1.8.0
        '''
        if self._video:
            self._video.stop()
            self._video.unload()
            self._video = None
        self.loaded = False


if __name__ == '__main__':
    from kivy.app import App
    import sys

    if len(sys.argv) != 2:
        print("usage: %s file" % sys.argv[0])
        sys.exit(1)

    class VideoApp(App):
        def build(self):
            self.v = Video(source=sys.argv[1], state='play')
            self.v.bind(state=self.replay)
            return self.v

        def replay(self, *args):
            if self.v.state == 'stop':
                self.v.state = 'play'

    VideoApp().run()
