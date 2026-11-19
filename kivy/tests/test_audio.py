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
        from kivy.core import audio_output
        return audio_output.SoundLoader.load(SAMPLE_FILE)

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
        from kivy.core.audio_output import audio_gstreamer
        return audio_gstreamer.SoundGstreamer(source)


class AudioSDL3TestCase(unittest.TestCase):

    def get_sound(self):
        from kivy.core import audio_output
        if 'sdl3' not in audio_output.SoundLoader.available_providers():
            self.skipTest('sdl3 audio provider is not available')
        return audio_output.SoundLoader.load(
            SAMPLE_FILE, audio_output_provider='sdl3')

    def record_events(self, sound):
        events = []
        sound.bind(on_play=lambda *args: events.append('on_play'),
                   on_stop=lambda *args: events.append('on_stop'))
        return events

    def test_play_from_stopped_does_not_dispatch_on_stop(self):
        sound = self.get_sound()
        events = self.record_events(sound)
        try:
            sound.play()
            assert events == ['on_play']
            sound.stop()
            sound.stop()
            assert events == ['on_play', 'on_stop']
        finally:
            sound.unload()

    def test_loop_continues_past_the_end(self):
        import time
        sound = self.get_sound()
        sound.loop = True
        events = self.record_events(sound)
        try:
            sound.play()
            # No Clock ticks here, so only SDL_mixer itself can loop.
            time.sleep(SAMPLE_LENGTH + 0.3)
            assert sound._audiotrack.is_playing()
            assert sound.get_pos() < SAMPLE_LENGTH / 2
            assert events == ['on_play']
        finally:
            sound.unload()

    def test_turning_loop_off_lets_the_sound_end(self):
        import time
        sound = self.get_sound()
        sound.loop = True
        try:
            sound.play()
            time.sleep(0.2)
            sound.loop = False
            time.sleep(SAMPLE_LENGTH)
            assert not sound._audiotrack.is_playing()
        finally:
            sound.unload()
