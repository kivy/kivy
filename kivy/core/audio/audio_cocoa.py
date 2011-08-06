from kivy.core.audio import Sound, SoundLoader


try:
    from Cocoa import NSSound
except:
    raise


class SoundCocoa(Sound):
    @staticmethod
    def extensions():
        '''
        As per NSSound.soundUnfilteredTypes().
        Listing only the commonly used.
        '''
        return ('aiff', 'aifc', 'wav', 'mp3', 'm4a')

    def __init__(self, **kwargs):
        self._sound = None
        super(SoundCocoa, self).__init__(**kwargs)

    def load(self):
        self._sound = NSSound.alloc().initWithContentsOfFile_byReference_(
            unicode(self.filename), False)

    def unload(self):
        self._sound = None

    def play(self):
        '''Play the file'''
        self._set_status('play')
        self._sound.play()

    def stop(self):
        self._set_status('stop')
        self._sound.stop()

    def seek(self, position):
        assert position < self._sound.duration()
        self._sound.setCurrentTime(position)


SoundLoader.register(SoundCocoa)
