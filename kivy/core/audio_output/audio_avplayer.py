'''
AVFoundation audio provider
===========================

Implementation of Sound using AVFoundation's AVAudioPlayer through
`rubicon-objc <https://github.com/beeware/rubicon-objc>`_. Works on macOS
and iOS.

Kivy's provider order puts ``sdl3`` first, so this provider plays the
formats SDL3_mixer can't decode, such as m4a, aac and caf.

.. note::

    :attr:`~kivy.core.audio_output.Sound.pitch` is a time-stretch here:
    it changes the speed but keeps the pitch, and AVAudioPlayer clamps it to
    0.5-2.0. The ``sdl3`` provider changes both speed and pitch.

.. versionchanged:: 3.0.0
    Uses rubicon-objc instead of pyobjus. Added support for
    :attr:`~kivy.core.audio_output.Sound.loop` and
    :attr:`~kivy.core.audio_output.Sound.pitch`;
    :meth:`~kivy.core.audio_output.Sound.stop` now rewinds to the start.
'''

__all__ = ('SoundAvplayer', )

import importlib.util
from functools import cache

from kivy.clock import Clock
from kivy.core.audio_output import Sound, SoundLoader
from kivy.logger import Logger

if importlib.util.find_spec('rubicon') is None:
    raise ImportError('AudioAvplayer: rubicon-objc is not installed')


@cache
def _objc():
    # Importing rubicon-objc takes about 100 ms on iOS. Deferring it to the
    # first load keeps it off app startup for apps that never use avplayer.
    from rubicon.objc import (
        NSObject, ObjCClass, ObjCProtocol, objc_method, objc_property)
    from rubicon.objc.runtime import load_library

    load_library('AVFoundation')

    class _AVAudioPlayerDelegate(
            NSObject, protocols=[ObjCProtocol('AVAudioPlayerDelegate')],
            auto_rename=True):

        sound = objc_property(object, weak=True)

        @objc_method
        def audioPlayerDidFinishPlaying_successfully_(
                self, player, flag: bool) -> None:
            sound = self.sound
            if sound is not None:
                Clock.schedule_once(lambda dt: sound._on_finished())

    return (ObjCClass('AVAudioPlayer'), ObjCClass('NSURL'),
            _AVAudioPlayerDelegate)


class SoundAvplayer(Sound):
    _provider_name = 'avplayer'

    @staticmethod
    def extensions():
        # taken from https://goo.gl/015kvU
        return ("aac", "adts", "aif", "aiff", "aifc", "caf", "mp3", "mp4",
                "m4a", "snd", "au", "sd2", "wav", "flac")

    def __init__(self, **kwargs):
        self._avplayer = None
        self._delegate = None
        super(SoundAvplayer, self).__init__(**kwargs)

    def load(self):
        self.unload()
        if not self.source:
            return
        AVAudioPlayer, NSURL, delegate_class = _objc()
        url = NSURL.fileURLWithPath(self.source)
        player = AVAudioPlayer.alloc().initWithContentsOfURL(url, error=None)
        if player is None:
            Logger.warning(
                'AudioAvplayer: Unable to load {}'.format(self.source))
            return
        if self._delegate is None:
            # AVAudioPlayer.delegate is weak, so the Sound keeps it alive.
            self._delegate = delegate_class.alloc().init()
            self._delegate.sound = self
        # rate only works if enabled before prepareToPlay
        player.enableRate = True
        player.rate = float(self.pitch)
        player.volume = float(self.volume)
        player.numberOfLoops = -1 if self.loop else 0
        player.delegate = self._delegate
        player.prepareToPlay()
        self._avplayer = player

    def unload(self):
        self.stop()
        if self._avplayer is not None:
            self._avplayer.delegate = None
        self._avplayer = None

    def play(self):
        if not self._avplayer:
            return
        self.stop()
        if not self._avplayer.play():
            Logger.warning(
                'AudioAvplayer: Unable to play {}'.format(self.source))
            return
        super(SoundAvplayer, self).play()

    def stop(self):
        if not self._avplayer:
            return
        self._avplayer.stop()
        self._avplayer.currentTime = 0.0
        if self.state == 'play':
            super(SoundAvplayer, self).stop()

    def _on_finished(self):
        if self.state == 'play':
            super(SoundAvplayer, self).stop()

    def seek(self, position):
        if not self._avplayer:
            return
        self._avplayer.currentTime = float(position)

    def get_pos(self):
        if self._avplayer:
            return float(self._avplayer.currentTime)
        return super(SoundAvplayer, self).get_pos()

    def on_volume(self, instance, volume):
        if self._avplayer:
            self._avplayer.volume = float(volume)

    def on_pitch(self, instance, pitch):
        if self._avplayer:
            self._avplayer.rate = float(pitch)

    def on_loop(self, instance, loop):
        if self._avplayer:
            self._avplayer.numberOfLoops = -1 if loop else 0

    def _get_length(self):
        if self._avplayer:
            return float(self._avplayer.duration)
        return super(SoundAvplayer, self)._get_length()


SoundLoader.register(SoundAvplayer)
