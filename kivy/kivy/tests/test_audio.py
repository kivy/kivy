'''
Audio tests
===========
'''

import unittest
import os
import pytest
if os.environ.get('KIVY_TEST_AUDIO') == '0':
    pytestmark = pytest.mark.skip("Audio is not available")

SAMPLE_FILE = os.path.join(os.path.dirname(__file__), 'sample1.ogg')
SAMPLE_LENGTH = 1.402
DELTA = SAMPLE_LENGTH * 0.01
DELAY = 0.2


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
        self.assertAlmostEqual(SAMPLE_LENGTH, length, delta=DELTA)
        # ensure that the gstreamer play/stop doesn't mess up the volume
        assert volume == sound.volume

    def test_length_playing(self):
        import time
        sound = self.get_sound()
        sound.play()
        try:
            time.sleep(DELAY)
            length = sound.length
            self.assertAlmostEqual(SAMPLE_LENGTH, length, delta=DELTA)
        finally:
            sound.stop()
        self.assertAlmostEqual(SAMPLE_LENGTH, length, delta=DELTA)

    def test_length_stopped(self):
        import time
        sound = self.get_sound()
        sound.play()
        try:
            time.sleep(DELAY)
        finally:
            sound.stop()
        length = sound.length
        self.assertAlmostEqual(SAMPLE_LENGTH, length, delta=DELTA)


class AudioGstreamerTestCase(AudioTestCase):

    def make_sound(self, source):
        from kivy.core.audio import audio_gstreamer
        return audio_gstreamer.SoundGstreamer(source)


class AudioPygameTestCase(AudioTestCase):

    def make_sound(self, source):
        from kivy.core.audio import audio_pygame
        return audio_pygame.SoundPygame(source)
