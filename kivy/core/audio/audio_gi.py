'''
Audio Gi
========

Implementation of Sound with Gi. Gi is both compatible with Python 2 and 3.
'''

from gi.repository import Gst
from kivy.core.audio import Sound, SoundLoader
from kivy.logger import Logger
from kivy.support import install_gobject_iteration
import os
import sys

# initialize the audio/gi. if the older version is used, don't use audio_gi.
Gst.init(None)
version = Gst.version()
if version < (1, 0, 0, 0):
    raise Exception('Cannot use audio_gi, Gstreamer < 1.0 is not supported.')
Logger.info('AudioGi: Using Gstreamer {}'.format(
    '.'.join(['{}'.format(x) for x in Gst.version()])))
install_gobject_iteration()


class SoundGi(Sound):

    @staticmethod
    def extensions():
        return ('wav', 'ogg', 'mp3', )

    def __init__(self, **kwargs):
        self._data = None
        super(SoundGi, self).__init__(**kwargs)

    def __del__(self):
        if self._data is not None:
            self._data.set_state(Gst.State.NULL)

    def _on_gst_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self._data.set_state(Gst.State.NULL)
            if self.loop:
                self.play()
            else:
                self.stop()
        elif t == Gst.MessageType.ERROR:
            self._data.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            Logger.error('AudioGi: %s' % err)
            Logger.debug(str(debug))
            self.stop()

    def play(self):
        if not self._data:
            return
        self._data.props.volume = self.volume
        self._data.set_state(Gst.State.PLAYING)
        super(SoundGi, self).play()

    def stop(self):
        if not self._data:
            return
        self._data.set_state(Gst.State.NULL)
        super(SoundGi, self).stop()

    def load(self):
        self.unload()
        fn = self.filename
        if fn is None:
            return

        slash = ''
        if sys.platform in ('win32', 'cygwin'):
            slash = '/'

        if fn[0] == '/':
            uri = 'file://' + slash + fn
        else:
            uri = 'file://' + slash + os.path.join(os.getcwd(), fn)

        self._data = Gst.ElementFactory.make('playbin', '')
        fakesink = Gst.ElementFactory.make('fakesink', '')
        self._data.props.video_sink = fakesink
        bus = self._data.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self._on_gst_message)
        self._data.props.uri = uri
        self._data.set_state(Gst.State.READY)

    def unload(self):
        self.stop()
        self._data = None

    def seek(self, position):
        if self._data is None:
            return
        self._data.seek_simple(
            Gst.Format.TIME, Gst.SeekFlags.SKIP, position * Gst.SECOND)

    def get_pos(self):
        if self._data is not None:
            if self._data.get_state()[1] == Gst.State.PLAYING:
                try:
                    ret, value = self._data.query_position(Gst.Format.TIME)
                    if ret:
                        return value / float(Gst.SECOND)
                except:
                    pass
        return 0

    def on_volume(self, instance, volume):
        if self._data is not None:
            self._data.set_property('volume', volume)

    def _get_length(self):
        if self._data is not None:
            if self._data.get_state()[1] != Gst.State.PLAYING:
                volume_before = self._data.get_property('volume')
                self._data.set_property('volume', 0)
                self._data.set_state(Gst.State.PLAYING)
                try:
                    self._data.get_state()
                    ret, value = self._data.query_duration(Gst.Format.TIME)
                    if ret:
                        return value / float(Gst.SECOND)
                finally:
                    self._data.set_state(Gst.State.NULL)
                    self._data.set_property('volume', volume_before)
            else:
                ret, value = self._data.query_duration(Gst.Format.TIME)
                if ret:
                    return value / float(Gst.SECOND)
        return super(SoundGi, self)._get_length()

SoundLoader.register(SoundGi)
