'''
Video
=====

The :class:`Video` widget is used to display video files and streams.
Depending on your Video core provider, platform, and plugins, you will
be able to play different formats. For example, gstreamer is more
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

    video = Video(source='PandaSneezes.avi')
    video.bind(
        position=on_position_change,
        duration=on_duration_change
    )

One can define a preview image which gets displayed until the video is
started/loaded by passing ``preview`` to the constructor::

    video = Video(
        source='PandaSneezes.avi',
        preview='PandaSneezes_preview.png'
    )

One can display the placeholder image when the video stops by reacting on eos::

    def on_eos_change(self, inst, val):
        if val and self.preview:
            self.set_texture_from_resource(self.preview)

    video.bind(eos=on_eos_change)

.. versionadded:: 3.0.0

An observable :attr:`buffering` boolean for loading-overlay UX and a
provider-specific :attr:`options` dict were added in 3.0.0::

    video = Video(
        source='movie.mp4',
        state='play',
        # Provider-specific options forwarded opaquely; each provider
        # documents the keys it honors. AVFoundation example:
        options={'automatically_waits_to_minimize_stalling': False},
    )

    # Drive a loading overlay from a single rule that covers both the
    # initial wait and any mid-stream rebuffer:
    video.bind(
        loaded=lambda v, l: overlay.set_visible(
            not l or v.buffering),
        buffering=lambda v, b: overlay.set_visible(
            not v.loaded or b),
    )

Static thumbnails can be generated without instantiating a widget via
:meth:`Video.generate_thumbnail`::

    texture = Video.generate_thumbnail(
        'movie.mp4', time=5.0, size=(320, 180))
    if texture is not None:
        thumbnail_image.texture = texture
'''

__all__ = ('Video', )

from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.core.video import Video as CoreVideo, VideoBase
from kivy.resources import resource_find
from kivy.properties import (BooleanProperty, DictProperty, NumericProperty,
                             OptionProperty, StringProperty)


class Video(Image):
    '''Video class. See module documentation for more information.
    '''

    preview = StringProperty(None, allownone=True)
    '''Filename / source of a preview image displayed before video starts.

    :attr:`preview` is a :class:`~kivy.properties.StringProperty` and
    defaults to None.

    If set, it gets displayed until the video is loaded/started.

    .. versionadded:: 2.1.0
    '''

    state = OptionProperty('stop', options=('play', 'pause', 'stop'))
    '''String, indicates whether to play, pause, or stop the video::

        # start playing the video at creation
        video = Video(source='movie.mkv', state='play')

        # create the video, and start later
        video = Video(source='movie.mkv')
        # and later
        video.state = 'play'

    :attr:`state` is an :class:`~kivy.properties.OptionProperty` and defaults
    to 'stop'.
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

    options = DictProperty(rebind=False, allownone=True)
    '''Provider-specific options forwarded to the underlying core video
    at construction. Each video provider documents the keys it honors on
    its own class (the canonical reference for behavior and defaults);
    the per-provider summary below is a quick lookup for the keys most
    apps reach for.

    Unknown keys for the selected provider are logged as a warning and
    otherwise left untouched in this dict (so apps that stash extra
    metadata in ``options`` keep working across Kivy / provider
    upgrades).

    **Providers that consume options:**

    * AVFoundation (macOS / iOS) -- see
      :class:`~kivy.core.video.video_avfoundation.VideoAVFoundation` for
      full detail:

      - ``automatically_waits_to_minimize_stalling`` (``bool``,
        default ``True``) -- forwards to the ``AVPlayer`` property of
        the same name. The default matches AVPlayer's own and favors
        uninterrupted playback at the cost of start-up latency. Set to
        ``False`` for snappier start (playback begins as soon as the
        first decodable frame is available rather than buffering
        ahead).
      - ``force_cpu_copy`` (``bool``, default ``False``) -- bypass the
        zero-copy IOSurface texture path and always use the CPU
        ``memcpy`` fallback. Useful for A/B testing and debugging.

    Other providers (GStreamer, FFmpeg / ffpyplayer) currently expose no
    documented ``options`` keys: unknown kwargs in ``options`` are also
    unpacked as keyword arguments to the core video for back-compat with
    apps that put well-known kwargs (e.g. ``eos='loop'``) in this dict.

    Example::

        video = Video(
            source='clip.mp4',
            state='play',
            options={'automatically_waits_to_minimize_stalling': False},
        )

    .. versionadded:: 1.0.4

    .. versionchanged:: 3.0.0
        In addition to being unpacked as keyword arguments (as before),
        the full dict is also forwarded to the core video as a single
        ``options=`` kwarg, giving providers a clean, introspectable
        place to look for provider-specific keys. Documented keys for
        the AVFoundation provider added in 3.0.0; see above.

        Reclassified from :class:`~kivy.properties.ObjectProperty` to
        :class:`~kivy.properties.DictProperty` (with ``allownone=True``)
        so the property now validates that the assigned value is either
        a ``dict`` or ``None``, each instance gets its own dict (no
        shared mutable default), and top-level mutations
        (``video.options['k'] = v``) dispatch ``on_options`` instead of
        only full reassignment.

    :attr:`options` is a :class:`~kivy.properties.DictProperty` and
    defaults to ``{}``. ``None`` is accepted (treated as an empty dict
    by the core video).
    '''

    buffering = BooleanProperty(False)
    '''Whether playback is currently delayed/stalled while trying to
    satisfy ``state='play'``. Mirrors
    :attr:`kivy.core.video.VideoBase.buffering` -- ``True`` covers both
    the initial pre-playback wait and any mid-stream rebuffer; always
    ``False`` while paused or stopped. Providers that cannot detect
    stalls leave it ``False``.

    For a single-rule loading overlay::

        overlay.visible = not video.loaded or video.buffering

    .. versionadded:: 3.0.0

    :attr:`buffering` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to ``False``.
    '''

    _video_load_event = None

    def __init__(self, **kwargs):
        self._video = None
        super(Video, self).__init__(**kwargs)
        self.fbind('source', self._trigger_video_load)

        if "eos" in kwargs:
            self.options["eos"] = kwargs["eos"]
        if self.source:
            self._trigger_video_load()

    def texture_update(self, *largs):
        if self.preview:
            self.set_texture_from_resource(self.preview)
        else:
            self.set_texture_from_resource(self.source)

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

    def _trigger_video_load(self, *largs):
        ev = self._video_load_event
        if ev is None:
            ev = self._video_load_event = Clock.schedule_once(
                self._do_video_load, -1)
        ev()

    def _do_video_load(self, *largs):
        if CoreVideo is None:
            return
        self.unload()
        if not self.source:
            self._video = None
            self.texture = None
        else:
            filename = self.source
            # Check if filename is not url
            if '://' not in filename:
                filename = resource_find(filename)
            # Forward both the dict (for providers that introspect
            # self._options) and the unpacked kwargs (back-compat with
            # apps that put well-known kwargs like 'eos' in options).
            # ``options`` accepts None as a legal value -- normalize it
            # to {} here so the rest of the stack only sees a dict.
            options = self.options if self.options is not None else {}
            core_kwargs = dict(options)
            self._video = CoreVideo(
                filename=filename,
                options=options,
                **core_kwargs)
            self._video.volume = self.volume
            self._video.bind(on_load=self._on_load,
                             on_frame=self._on_video_frame,
                             on_eos=self._on_eos,
                             on_buffering=self._on_buffering)
            if self.state == 'play':
                self._video.play()
            self.duration = 1.
            self.position = 0.

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
        if not self._video or self._video.eos != 'loop':
            self.state = 'stop'
            self.eos = True

    def _on_load(self, *largs):
        self.loaded = True
        self._on_video_frame(largs)

    def _on_buffering(self, instance, value):
        self.buffering = bool(value)

    def on_volume(self, instance, value):
        if self._video:
            self._video.volume = value

    @classmethod
    def generate_thumbnail(cls, filename, time, size=None):
        '''Generate a thumbnail :class:`~kivy.graphics.texture.Texture`
        from the given video file at the given timestamp, without
        instantiating a :class:`Video` widget or starting playback.
        Delegates to the currently selected core video provider.

        :Parameters:
            `filename`: str
                Path or URI to the video. Resolved through
                :func:`~kivy.resources.resource_find` when it does not
                look like a URL.
            `time`: float
                Timestamp in seconds at which to grab the thumbnail.
            `size`: tuple of (int, int), optional
                Target ``(width, height)``. When ``None`` the source
                video's native frame size is used.

        :Returns:
            A :class:`~kivy.graphics.texture.Texture`, or ``None`` if no
            provider could generate the thumbnail.

        .. versionadded:: 3.0.0
        '''
        if CoreVideo is None:
            return None
        resolved = filename
        if resolved and '://' not in resolved:
            resolved = resource_find(resolved) or resolved
        # CoreVideo here is a provider class (subclass of VideoBase),
        # so its classmethod is the provider-specific implementation.
        try:
            return CoreVideo.generate_thumbnail(resolved, time, size=size)
        except Exception:
            # Fall back to the base implementation (returns None and logs)
            return VideoBase.generate_thumbnail(resolved, time, size=size)

    def unload(self):
        '''Unload the video. The playback will be stopped.

        .. versionadded:: 1.8.0
        '''
        if self._video:
            self._video.stop()
            self._video.unload()
            self._video = None
        self.loaded = False
        self.buffering = False


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
