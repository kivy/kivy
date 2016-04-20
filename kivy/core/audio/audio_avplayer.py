'''
AudioAvplayer: implementation of Sound using pyobjus / AVFoundation.
Works on iOS / OSX.
'''

__all__ = ('SoundAvplayer', )

from kivy.core.audio import Sound, SoundLoader
from pyobjus import autoclass
from pyobjus.dylib_manager import load_framework, INCLUDE

load_framework(INCLUDE.AVFoundation)
AVAudioPlayer = autoclass("AVAudioPlayer")
NSURL = autoclass("NSURL")
NSString = autoclass("NSString")


class SoundAvplayer(Sound):
    @staticmethod
    def extensions():
        # taken from https://goo.gl/015kvU
        return ("aac", "adts", "aif", "aiff", "aifc", "caf", "mp3", "mp4",
                "m4a", "snd", "au", "sd2", "wav")

    def __init__(self, **kwargs):
        self._avplayer = None
        super(SoundAvplayer, self).__init__(**kwargs)

    def load(self):
        self.unload()
        fn = NSString.alloc().initWithUTF8String_(self.filename)
        url = NSURL.alloc().initFileURLWithPath_(fn)
        self._avplayer = AVAudioPlayer.alloc().initWithContentsOfURL_error_(
            url, None)

    def unload(self):
        self.stop()
        self._avplayer = None

    def play(self):
        if not self._avplayer:
            return
        self._avplayer.play()
        super(SoundAvplayer, self).play()

    def stop(self):
        if not self._avplayer:
            return
        self._avplayer.stop()
        super(SoundAvplayer, self).stop()

    def seek(self, position):
        if not self._avplayer:
            return
        self._avplayer.playAtTime_(float(position))

    def get_pos(self):
        if self._avplayer:
            return self._avplayer.currentTime
        return super(SoundAvplayer, self).get_pos()

    def on_volume(self, instance, volume):
        if self._avplayer:
            self._avplayer.volume = float(volume)

    def _get_length(self):
        if self._avplayer:
            return self._avplayer.duration
        return super(SoundAvplayer, self)._get_length()

SoundLoader.register(SoundAvplayer)
