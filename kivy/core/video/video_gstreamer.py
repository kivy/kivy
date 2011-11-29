'''
VideoGStreamer: implementation of VideoBase with GStreamer
'''
#
# Important notes: you must take care of glib event + python. If you connect()
# directly an event to a python object method, the object will be ref, and will
# be never unref.
# To prevent memory leak, you must connect() to a func, and you might want to
# pass the referenced object with weakref()
#

try:
    import pygst
    if not hasattr(pygst, '_gst_already_checked'):
        pygst.require('0.10')
        pygst._gst_already_checked = True
    import gst
except:
    raise

from os import path
from threading import Lock
from urllib import pathname2url
from kivy.graphics.texture import Texture
from kivy.logger import Logger
from functools import partial
from weakref import ref
from . import VideoBase

# install the gobject iteration
from kivy.support import install_gobject_iteration
install_gobject_iteration()


_VIDEO_CAPS = ','.join([
    'video/x-raw-rgb',
    'red_mask=(int)0xff0000',
    'green_mask=(int)0x00ff00',
    'blue_mask=(int)0x0000ff'])


def _gst_new_buffer(obj, appsink):
    obj = obj()
    if not obj:
        return
    with obj._buffer_lock:
        obj._buffer = obj._videosink.emit('pull-buffer')


def _on_gst_message(bus, message):
    Logger.trace('gst-bus: %s' % str(message))
    # log all error messages
    if message.type == gst.MESSAGE_ERROR:
        error, debug = map(str, message.parse_error())
        Logger.error('gstreamer_video: %s'%error)
        Logger.debug('gstreamer_video: %s'%debug)


def _on_gst_eos(obj, *largs):
    obj = obj()
    if not obj:
        return
    obj._do_eos()


class VideoGStreamer(VideoBase):

    def __init__(self, **kwargs):
        self._buffer_lock = Lock()
        self._buffer = None
        self._texture = None
        self._gst_init()
        super(VideoGStreamer, self).__init__(**kwargs)

    def _gst_init(self):
        # self._videosink will receive the buffers so we can upload them to GPU
        self._videosink = gst.element_factory_make('appsink', 'videosink')
        self._videosink.set_property('caps', gst.Caps(_VIDEO_CAPS))
        self._videosink.set_property('async', True)
        self._videosink.set_property('drop', True)
        self._videosink.set_property('emit-signals', True)
        self._videosink.connect('new-buffer', partial(
            _gst_new_buffer, ref(self)))

        # playbin, takes care of all, loading, playing, etc.
        # XXX playbin2 have some issue when playing some video or streaming :/
        #self._playbin = gst.element_factory_make('playbin2', 'playbin')
        self._playbin = gst.element_factory_make('playbin', 'playbin')
        self._playbin.set_property('video-sink', self._videosink)

        # gstreamer bus, to attach and listen to gst messages
        self._bus = self._playbin.get_bus()
        self._bus.add_signal_watch()
        self._bus.connect('message', _on_gst_message)
        self._bus.connect('message::eos', partial(
            _on_gst_eos, ref(self)))

    def _update_texture(self, buf):
        # texture will be updated with newest buffer/frame
        caps = buf.get_caps()[0]
        size = caps['width'], caps['height']
        if not self._texture:
            # texture is not allocated yet, so create it first
            self._texture = Texture.create(size=size, colorfmt='rgb')
            self._texture.flip_vertical()
        # upload texture data to GPU
        self._texture.blit_buffer(buf.data, size=size, colorfmt='rgb')

    def _update(self, dt):
        with self._buffer_lock:
            if self._buffer is not None:
                self._update_texture(self._buffer)
                self._buffer = None
                self.dispatch('on_frame')

    def unload(self):
        self._playbin.set_state(gst.STATE_NULL)
        self._buffer = None
        self._texture = None

    def load(self):
        Logger.debug('gstreamer_video: Load <%s>'% self._filename)
        self._playbin.set_state(gst.STATE_NULL)
        self._playbin.set_property('uri', self._get_uri())
        self._playbin.set_state(gst.STATE_READY)

    def stop(self):
        self._state = ''
        self._playbin.set_state(gst.STATE_PAUSED)

    def play(self):
        self._state = 'playing'
        self._playbin.set_state(gst.STATE_PLAYING)

    def seek(self, percent):
        seek_t = percent * self._get_duration() * 10e8
        seek_format = gst.FORMAT_TIME
        seek_flags = gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_KEY_UNIT
        self._playbin.seek_simple(seek_format, seek_flags, seek_t)

        #if pipeline is not playing, we need to pull pre-roll to update frame
        if not self._state == 'playing':
            with self._buffer_lock:
                self._buffer = self._videosink.emit('pull-preroll')

    def _get_uri(self):
        uri = self.filename
        if not uri:
            return
        if uri.split(':')[0] not in (
                'http', 'https', 'file', 'udp', 'rtp', 'rtsp'):
            uri = 'file:' + pathname2url(path.realpath(uri))
        return uri

    def _do_eos(self, *args):
        self.seek(0)
        self.dispatch('on_eos')
        super(VideoGStreamer, self)._do_eos()

    def _get_position(self):
        try:
            value, fmt = self._videosink.query_position(gst.FORMAT_TIME)
            return value / 10e8
        except:
            return -1

    def _get_duration(self):
        try:
            return self._playbin.query_duration(gst.FORMAT_TIME)[0] / 10e8
        except:
            return -1

    def _get_volume(self):
        self._volume = self._playbin.get_property('volume')
        return self._volume

    def _set_volume(self, volume):
        self._playbin.set_property('volume', volume)
        self._volume = volume

