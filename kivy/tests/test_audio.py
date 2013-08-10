'''
Audio tests
===========
'''

import unittest
import os

SAMPLE_FILE = os.path.join(os.path.dirname(__file__), 'sample1.ogg')
SAMPLE_LENGTH = 1.402
SAMPLE_LENGTH_MIN = SAMPLE_LENGTH * 0.99
SAMPLE_LENGTH_MAX = SAMPLE_LENGTH * 1.01


class AudioTestCase(unittest.TestCase):

    def get_sound(self):
        import os
        assert os.path.exists(SAMPLE_FILE)
        from kivy.core import audio
        return audio.SoundLoader.load(SAMPLE_FILE)

    def test_length_simple(self):
        sound = self.get_sound()
        volume = sound.volume = 0.75
        length = sound.length
        assert SAMPLE_LENGTH_MIN <= length <= SAMPLE_LENGTH_MAX
        # ensure that the gstreamer play/stop doesn't mess up the volume
        assert volume == sound.volume

    def test_length_playing(self):
        import time
        sound = self.get_sound()
        sound.play()
        try:
            time.sleep(0.1)
            length = sound.length
            assert SAMPLE_LENGTH_MIN <= length <= SAMPLE_LENGTH_MAX
        finally:
            sound.stop()

    def test_length_stopped(self):
        import time
        sound = self.get_sound()
        sound.play()
        try:
            time.sleep(0.1)
        finally:
            sound.stop()
        length = sound.length
        assert SAMPLE_LENGTH_MIN <= length <= SAMPLE_LENGTH_MAX


class AudioGstreamerTestCase(AudioTestCase):

    def make_sound(self, source):
        from kivy.core.audio import audio_gstreamer
        return audio_gstreamer.SoundGstreamer(source)


class AudioPygameTestCase(AudioTestCase):

    def make_sound(self, source):
        from kivy.core.audio import audio_pygame
        return audio_pygame.SoundPygame(source)


