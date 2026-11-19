'''
Media Foundation video provider tests
=====================================

The provider is compiled only on Windows (when
``c_options['use_mediafoundation']`` is True in ``setup.py``), so these
tests skip everywhere else, and skip on Windows builds without it.
'''

import sys
import unittest
from unittest import mock

import pytest


pytestmark = pytest.mark.skipif(
    sys.platform != 'win32',
    reason='Media Foundation video provider is Windows only',
)


def _try_import_module():
    try:
        from kivy.core.video import video_mediafoundation
        return video_mediafoundation
    except ImportError:
        return None


class VideoMediaFoundationOptionsTestCase(unittest.TestCase):

    def setUp(self):
        self.module = _try_import_module()
        if self.module is None:
            self.skipTest('VideoMediaFoundation not built in this environment')

    def _make(self, options):
        with mock.patch.object(self.module, 'Logger') as logger:
            video = self.module.VideoMediaFoundation(
                filename=None, options=options)
        self.addCleanup(video.unload)
        return video, logger

    def test_eos_in_options_is_not_unknown(self):
        '''The Video widget copies ``eos`` into ``options`` when an app
        sets it, so it must not be reported as an unknown option.
        '''
        video, logger = self._make({'eos': 'loop'})
        logger.warning.assert_not_called()
        self.assertEqual(video.options, {'eos': 'loop'})

    def test_unknown_option_is_warned_not_raised(self):
        video, logger = self._make({'this_key_does_not_exist': 1})
        logger.warning.assert_called_once()
        self.assertIn('this_key_does_not_exist',
                      logger.warning.call_args[0][0])
        self.assertEqual(video.options, {'this_key_does_not_exist': 1})
