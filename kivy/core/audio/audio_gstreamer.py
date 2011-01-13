'''
AudioGstreamer: implementation of Sound with GStreamer
'''

try:
    import pygst
    if not hasattr(pygst, '_gst_already_checked'):
        pygst.require('0.10')
        pygst._gst_already_checked = True
    import gst
except:
    raise

from . import Sound, SoundLoader
import os
import sys
from kivy.logger import Logger

# install the gobject iteration
from kivy.support import install_gobject_iteration
install_gobject_iteration()


class SoundGstreamer(Sound):

    @staticmethod
    def extensions():
        return ('wav', 'ogg', 'mp3', )

    def __init__(self, **kwargs):
        self._data = None
        super(SoundGstreamer, self).__init__(**kwargs)

    def __del__(self):
        if self._data is not None:
            self._data.set_state(gst.STATE_NULL)

    def _on_gst_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self._data.set_state(gst.STATE_NULL)
            self.stop()
        elif t == gst.MESSAGE_ERROR:
            self._data.set_state(gst.STATE_NULL)
            err, debug = message.parse_error()
            Logger.error('AudioGstreamer: %s' % err)
            Logger.debug(str(debug))
            self.stop()

    def play(self):
        if not self._data:
            return
        self._data.set_state(gst.STATE_PLAYING)
        super(SoundGstreamer, self).play()

    def stop(self):
        if not self._data:
            return
        self._data.set_state(gst.STATE_NULL)
        super(SoundGstreamer, self).stop()

    def load(self):
        self.unload()
        fn = self.filename
        if fn is None:
            return

        slash = ''
        if sys.platform in ('win32', 'cygwin'):
            slash = '/'

        if fn[0] == '/':
            filepath = 'file://' + slash + fn
        else:
            filepath = 'file://' + slash + os.path.join(os.getcwd(), fn)

        self._data = gst.element_factory_make('playbin2', 'player')
        fakesink = gst.element_factory_make('fakesink', 'fakesink')
        self._data.set_property('video-sink', fakesink)
        bus = self._data.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self._on_gst_message)

        self._data.set_property('uri', filepath)
        self._data.set_state(gst.STATE_READY)

    def unload(self):
        self.stop()
        self._data = None

    def seek(self, position):
        if self._data is None:
            return
        self._data.seek_simple(gst.FORMAT_TIME, gst.SEEK_FLAG_SKIP,
                               position / 1000000000.)

    def _get_volume(self):
        if self._data is not None:
            self._volume = self._data.get_property('volume')
        return super(SoundGstreamer, self)._get_volume()

    def _set_volume(self, volume):
        if self._data is not None:
            self._data.set_property('volume', volume)
        return super(SoundGstreamer, self)._set_volume(volume)

SoundLoader.register(SoundGstreamer)
