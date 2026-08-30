'''
Audio tests
===========
'''

import unittest
import os
import pytest
from kivy.utils import platform
if os.environ.get('KIVY_TEST_AUDIO') == '0':
    pytestmark = pytest.mark.skip("Audio is not available")

IS_GSTPLAYER_AVAILABLE = True
try:
    import kivy.lib.gstplayer._gstplayer
except ImportError:
    IS_GSTPLAYER_AVAILABLE = False
else:
    del kivy.lib.gstplayer._gstplayer

IS_FFPYPLAYER_AVAILABLE = True
try:
    import ffpyplayer
except ImportError:
    IS_FFPYPLAYER_AVAILABLE = False
else:
    del ffpyplayer


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


class OnEOSTest:

    @pytest.fixture(autouse=True)
    def set_clock(self, kivy_clock):
        self.kivy_clock = kivy_clock

    def test_on_eos_event(self):
        eos = False

        def callback(_):
            nonlocal eos
            eos = True

        import time
        sound = self.get_sound()
        sound.bind(on_eos=callback)
        sound.play()
        time.sleep(SAMPLE_LENGTH + 0.5)  # the callback is called with a delay
        self.kivy_clock.tick()
        self.assertTrue(eos)


@pytest.mark.skipif(
    not IS_GSTPLAYER_AVAILABLE,
    reason='gstreamer is not available'
)
class AudioGstplayerTestCase(AudioTestCase, OnEOSTest):

    def get_sound(self):
        assert os.path.exists(SAMPLE_FILE)
        from kivy.core.audio_output import audio_gstplayer
        return audio_gstplayer.SoundGstplayer(source=SAMPLE_FILE)


@pytest.mark.skipif(
    not IS_FFPYPLAYER_AVAILABLE or platform in ('macosx', 'linux'),
    # It seems that there are problems with the audio card on macos and linux
    # (Github CI). From logs:
    # SDL_OpenAudio (1 channels, 44100 Hz): ALSA: Couldn't open audio device
    reason='ffpyplayer is not available'
)
class AudioFFPyplayerTestCase(AudioTestCase, OnEOSTest):

    def get_sound(self):
        assert os.path.exists(SAMPLE_FILE)
        from kivy.core.audio_output import audio_ffpyplayer
        return audio_ffpyplayer.SoundFFPy(source=SAMPLE_FILE)
