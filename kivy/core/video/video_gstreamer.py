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
from kivy.compat import PY2
try:
    #import pygst
    #if not hasattr(pygst, '_gst_already_checked'):
    #    pygst.require('0.10')
    #    pygst._gst_already_checked = True
    if PY2:
        import gst
    else:
        import ctypes
        import gi
        from gi.repository import Gst as gst
except:
    raise

from os import path
from threading import Lock
if PY2:
    from urllib import pathname2url
else:
    from urllib.request import pathname2url
from kivy.graphics.texture import Texture
from kivy.logger import Logger
from functools import partial
from weakref import ref
from kivy.core.video import VideoBase

# install the gobject iteration
from kivy.support import install_gobject_iteration
install_gobject_iteration()

BUF_SAMPLE = 'buffer'
_VIDEO_CAPS = ','.join([
    'video/x-raw-rgb',
    'red_mask=(int)0xff0000',
    'green_mask=(int)0x00ff00',
    'blue_mask=(int)0x0000ff'])

if not PY2:
    gst.init(None)
    gst.STATE_NULL = gst.State.NULL
    gst.STATE_READY = gst.State.READY
    gst.STATE_PLAYING = gst.State.PLAYING
    gst.STATE_PAUSED = gst.State.PAUSED
    gst.FORMAT_TIME = gst.Format.TIME
    gst.SEEK_FLAG_FLUSH = gst.SeekFlags.KEY_UNIT
    gst.SEEK_FLAG_KEY_UNIT = gst.SeekFlags.KEY_UNIT
    gst.MESSAGE_ERROR = gst.MessageType.ERROR
    BUF_SAMPLE = 'sample'

    _VIDEO_CAPS = ','.join([
        'video/x-raw',
        'format=RGB',
        'red_mask=(int)0xff0000',
        'green_mask=(int)0x00ff00',
        'blue_mask=(int)0x0000ff'])


def _gst_new_buffer(obj, appsink):
    obj = obj()
    if not obj:
        return
    with obj._buffer_lock:
        obj._buffer = obj._videosink.emit('pull-' + BUF_SAMPLE)


def _on_gst_message(bus, message):
    Logger.trace('gst-bus: %s' % str(message))
    # log all error messages
    if message.type == gst.MESSAGE_ERROR:
        error, debug = list(map(str, message.parse_error()))
        Logger.error('gstreamer_video: %s' % error)
        Logger.debug('gstreamer_video: %s' % debug)


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
        if PY2:
            self._videosink = gst.element_factory_make('appsink', 'videosink')
            self._videosink.set_property('caps', gst.Caps(_VIDEO_CAPS))
        else:
            self._videosink = gst.ElementFactory.make('appsink', 'videosink')
            self._videosink.set_property('caps',
                 gst.caps_from_string(_VIDEO_CAPS))

        self._videosink.set_property('async', True)
        self._videosink.set_property('drop', True)
        self._videosink.set_property('qos', True)
        self._videosink.set_property('emit-signals', True)
        self._videosink.connect('new-' + BUF_SAMPLE, partial(
            _gst_new_buffer, ref(self)))

        # playbin, takes care of all, loading, playing, etc.
        # XXX playbin2 have some issue when playing some video or streaming :/
        #self._playbin = gst.element_factory_make('playbin2', 'playbin')
        if PY2:
            self._playbin = gst.element_factory_make('playbin', 'playbin')
        else:
            self._playbin = gst.ElementFactory.make('playbin', 'playbin')
        self._playbin.set_property('video-sink', self._videosink)

        # gstreamer bus, to attach and listen to gst messages
        self._bus = self._playbin.get_bus()
        self._bus.add_signal_watch()
        self._bus.connect('message', _on_gst_message)
        self._bus.connect('message::eos', partial(
            _on_gst_eos, ref(self)))

    def _update_texture(self, buf):
        # texture will be updated with newest buffer/frame
        caps = buf.get_caps()
        _s = caps.get_structure(0)
        data = size = None
        if PY2:
            size = _s['width'], _s['height']
        else:
            size = _s.get_int('width')[1], _s.get_int('height')[1]
        if not self._texture:
            # texture is not allocated yet, so create it first
            self._texture = Texture.create(size=size, colorfmt='rgb')
            self._texture.flip_vertical()
            self.dispatch('on_load')
        # upload texture data to GPU
        if not PY2:
            mapinfo = None
            try:
                mem = buf.get_buffer()
                #from pudb import set_trace; set_trace()
                result, mapinfo = mem.map(gst.MapFlags.READ)
                #result, mapinfo = mem.map_range(0, -1, gst.MapFlags.READ)

                # repr(mapinfo) will return <void at 0x1aa3530>
                # but there is no python attribute to get the address... so we
                # need to parse it.
                addr = int(repr(mapinfo.memory).split()[-1][:-1], 16)
                # now get the memory
                _size = mem.__sizeof__() + mapinfo.memory.__sizeof__()
                data = ctypes.string_at(addr + _size, mapinfo.size)
                #print('got data', len(data), addr)
            finally:
                if mapinfo is not None:
                    mem.unmap(mapinfo)
        else:
            data = buf.data

        self._texture.blit_buffer(data, size=size, colorfmt='rgb')

    def _update(self, dt):
        buf = None
        with self._buffer_lock:
            buf = self._buffer
            self._buffer = None
        if buf is not None:
            self._update_texture(buf)
            self.dispatch('on_frame')

    def unload(self):
        self._playbin.set_state(gst.STATE_NULL)
        self._buffer = None
        self._texture = None

    def load(self):
        Logger.debug('gstreamer_video: Load <%s>' % self._filename)
        self._playbin.set_state(gst.STATE_NULL)
        self._playbin.set_property('uri', self._get_uri())
        self._playbin.set_state(gst.STATE_READY)

    def stop(self):
        '''.. versionchanged:: 1.4.0'''
        self._state = ''
        self._playbin.set_state(gst.STATE_PAUSED)

    def pause(self):
        '''.. versionadded:: 1.4.0'''
        self._state = 'paused'
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
        if not '://' in uri:
            uri = 'file:' + pathname2url(path.realpath(uri))
        return uri

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

