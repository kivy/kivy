'''
VideoGStreamer: implementation of VideoBase with GStreamer
'''

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
from kivy.graphics.texture import Texture
from kivy.logger import Logger
from . import VideoBase

# install the gobject iteration
from kivy.support import install_gobject_iteration
install_gobject_iteration()


_VIDEO_CAPS = ",".join([
    'video/x-raw-rgb',
    'red_mask=(int)0xff0000',
    'green_mask=(int)0x00ff00',
    'blue_mask=(int)0x0000ff'
])


class VideoGStreamer(VideoBase):

    def __init__(self, **kwargs):
        self._buffer_lock = Lock()
        self._buffer = None
        self._texture = None
        self._gst_init()
        super(VideoGStreamer, self).__init__(**kwargs)

    def _gst_init(self):
        # self._videosink will receive the buffers so we can upload them to GPU
        self._videosink = gst.element_factory_make("appsink", "videosink")
        self._videosink.set_property('caps', gst.Caps(_VIDEO_CAPS))
        self._videosink.set_property('async', True)
        self._videosink.set_property('drop', True)
        self._videosink.set_property('emit-signals', True)
        self._videosink.connect('new-buffer', self._update_buffer)

        # playbin, takes care of all, loading, playing, etc.
        self._playbin = gst.element_factory_make("playbin2", "playbin")
        self._playbin.set_property('video-sink', self._videosink)

        # gstreamer bus, to attach and listen to gst messages
        self._bus = self._playbin.get_bus()
        self._bus.add_signal_watch()
        self._bus.connect("message", self._bus_message)
        self._bus.connect("message::eos", self._do_eos)

    def _bus_message(self, bus, message):
        Logger.trace("gst-bus:%s"%str(message))

        # log all error messages
        if message.type == gst.MESSAGE_ERROR: 
            error, debug = map(str, message.parse_error())
            Logger.error("gstreamer_video: %s"%error)
            Logger.debug("gstreamer_video: %s"%debug)

    def _update_buffer(self, appsink):
        # we have a new frame from sgtreamer, do thread safe pull
        with self._buffer_lock:
            self._buffer = self._videosink.emit('pull-buffer')
    
    def _update_texture(self, buffer):
        # texture will be updated with newest buffer/frame
        caps = buffer.get_caps()[0]
        size = caps['width'], caps['height']
        if not self._texture:
            # texture is not allocated yet, so create it first
            self._texture = Texture.create(size=size, colorfmt='rgb')
            self._texture.flip_vertical()
        # upload texture data to GPU
        self._texture.blit_buffer(self._buffer.data, size=size, colorfmt='rgb')

    def _update(self, dt):
        with self._buffer_lock:
            if self._buffer != None:
                self._update_texture(self._buffer)
                self._buffer = None
                self.dispatch('on_frame')

    def unload(self):
        self._playbin.set_state(gst.STATE_NULL)
        self._buffer = None
        self._texture = None

    def load(self):
        Logger.debug("gstreamer_video: Load <%s>"% self._filename)
        self._playbin.set_state(gst.STATE_NULL)
        self._playbin.set_property("uri", self._get_uri())
        self._playbin.set_state(gst.STATE_PLAYING)

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
        if ":" in self.filename:
            return self.filename
        return "file://"+path.abspath(self.filename)

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

