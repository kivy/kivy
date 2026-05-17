'''
Tests for the AVFoundation video provider.

The provider is a compiled Cython extension (built only when
``c_options['use_avfoundation']`` is True in ``setup.py``), so these
tests gracefully skip when:

  - the host platform is not Darwin (macOS / iOS);
  - the provider failed to import for any reason (provider not compiled
    in the current build, AVFoundation framework unavailable, etc.).

Playback-dependent behaviour is exercised by
``examples/widgets/video/avfoundation_demo.py`` which is a manual
interactive demo. Here we focus on what is reliably testable in a
non-interactive context: import, thumbnail generation, options
round-trip, and basic instantiation lifecycle.
'''

import os
import sys
import unittest
from os.path import abspath, join

import pytest


pytestmark = pytest.mark.skipif(
    sys.platform != 'darwin',
    reason='AVFoundation video provider is macOS / iOS only',
)


def _try_import_provider():
    try:
        from kivy.core.video.video_avfoundation import (  # noqa: F401
            VideoAVFoundation)
        return VideoAVFoundation
    except ImportError:
        return None


def _example_video_path():
    from kivy import kivy_examples_dir
    return abspath(join(kivy_examples_dir, 'widgets', 'cityCC0.mpg'))


class VideoAVFoundationImportTestCase(unittest.TestCase):

    def test_provider_class_importable(self):
        '''The compiled VideoAVFoundation extension can be imported on
        Darwin builds. When it can't (provider not built), skip rather
        than fail so the rest of the suite still runs.
        '''
        provider = _try_import_provider()
        if provider is None:
            self.skipTest(
                'kivy.core.video.video_avfoundation is not available in '
                'this build (likely not compiled with use_avfoundation)')
        # Sanity check: it really is a VideoBase subclass.
        from kivy.core.video import VideoBase
        self.assertTrue(issubclass(provider, VideoBase))

    def test_avfoundation_is_default_on_darwin(self):
        '''avfoundation must be at the head of the PROVIDER_CONFIGS list
        for video, so it is picked first on Darwin builds.
        '''
        from kivy.core import PROVIDER_CONFIGS
        video_providers = PROVIDER_CONFIGS.get('video', [])
        self.assertTrue(len(video_providers) > 0)
        first_name, _ = video_providers[0]
        self.assertEqual(first_name, 'avfoundation')


class VideoAVFoundationOptionsTestCase(unittest.TestCase):

    def setUp(self):
        self.provider = _try_import_provider()
        if self.provider is None:
            self.skipTest('VideoAVFoundation not built in this environment')

    def test_options_default_is_empty(self):
        v = self.provider(filename=None)
        try:
            self.assertEqual(v.options, {})
        finally:
            v.unload()

    def test_force_cpu_copy_option_roundtrip(self):
        v = self.provider(
            filename=None,
            options={'force_cpu_copy': True},
        )
        try:
            self.assertTrue(v.options.get('force_cpu_copy'))
        finally:
            v.unload()

    def test_auto_wait_option_roundtrip(self):
        v = self.provider(
            filename=None,
            options={'automatically_waits_to_minimize_stalling': False},
        )
        try:
            self.assertFalse(
                v.options.get('automatically_waits_to_minimize_stalling'))
        finally:
            v.unload()

    def test_unknown_option_is_ignored_not_raised(self):
        '''Unknown keys in ``options`` should be tolerated (logged as a
        warning, not raised) so apps stashing extra metadata in the dict
        keep working across provider upgrades.
        '''
        v = self.provider(
            filename=None,
            options={'this_key_does_not_exist': 'whatever'},
        )
        try:
            self.assertEqual(
                v.options.get('this_key_does_not_exist'), 'whatever')
        finally:
            v.unload()


class VideoAVFoundationThumbnailTestCase(unittest.TestCase):

    def setUp(self):
        self.provider = _try_import_provider()
        if self.provider is None:
            self.skipTest('VideoAVFoundation not built in this environment')
        self.video_path = _example_video_path()
        if not os.path.exists(self.video_path):
            self.skipTest(
                'example video {} not found'.format(self.video_path))

    def test_generate_thumbnail_returns_texture_or_none(self):
        '''generate_thumbnail() either returns a Texture (when
        AVFoundation can decode the asset at the given timestamp) or
        None (when it can't, e.g. the source codec isn't supported by
        the current macOS AVFoundation build). Either outcome is
        acceptable -- we just assert it doesn't raise and the return
        type is one of those two.
        '''
        from kivy.graphics.texture import Texture
        result = self.provider.generate_thumbnail(
            self.video_path, 0.5, size=(128, 128))
        self.assertTrue(result is None or isinstance(result, Texture))
        if isinstance(result, Texture):
            # Returned thumbnails should have non-zero dimensions.
            self.assertGreater(result.width, 0)
            self.assertGreater(result.height, 0)

    def test_generate_thumbnail_bad_path_returns_none(self):
        result = self.provider.generate_thumbnail(
            '/this/path/does/not/exist.mp4', 0.0)
        self.assertIsNone(result)


if __name__ == '__main__':
    pytest.main(args=[__file__])
