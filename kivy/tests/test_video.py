
import unittest


class VideoTestCase(unittest.TestCase):

    def test_video_unload(self):
        # fix issue https://github.com/kivy/kivy/issues/2275
        # AttributeError: 'NoneType' object has no attribute 'texture'
        from kivy.uix.video import Video
        from kivy.clock import Clock
        from kivy.base import runTouchApp, stopTouchApp
        from kivy import kivy_examples_dir
        from os.path import join, abspath
        source = abspath(join(kivy_examples_dir, "widgets", "cityCC0.mpg"))
        video = Video(source=source, state='play')
        Clock.schedule_once(lambda x: stopTouchApp(), 1)

        def unload_video(video, position):
            if position > 0.01:
                video.unload()
                Clock.schedule_once(lambda x: stopTouchApp(), 0.1)

        video.bind(position=unload_video)
        runTouchApp(video)


class VideoBaseAPITestCase(unittest.TestCase):
    '''Cross-platform tests for the new VideoBase API surface added in
    3.0.0 (options dict, buffering property/event, generate_thumbnail
    classmethod). These exercise the base class directly without
    requiring any specific provider; an AVFoundation-only test module
    covers the macOS provider's actual behaviour.
    '''

    def test_options_roundtrip(self):
        from kivy.core.video import VideoBase
        opts = {'force_cpu_copy': True, 'custom': 'x'}
        vb = VideoBase(filename=None, options=opts)
        try:
            self.assertEqual(vb.options, opts)
            # Mutating the caller's dict must not retroactively change
            # what the provider sees: VideoBase copies it.
            opts['force_cpu_copy'] = False
            self.assertTrue(vb.options.get('force_cpu_copy'))
        finally:
            vb.unload()

    def test_options_default_is_empty_dict(self):
        from kivy.core.video import VideoBase
        vb = VideoBase(filename=None)
        try:
            self.assertEqual(vb.options, {})
        finally:
            vb.unload()

    def test_buffering_default_is_false(self):
        from kivy.core.video import VideoBase
        vb = VideoBase(filename=None)
        try:
            self.assertFalse(vb.buffering)
        finally:
            vb.unload()

    def test_on_buffering_event_registered(self):
        from kivy.core.video import VideoBase
        self.assertIn('on_buffering', VideoBase.__events__)

    def test_on_buffering_dispatches_with_value(self):
        from kivy.core.video import VideoBase
        vb = VideoBase(filename=None)
        seen = []
        try:
            vb.bind(on_buffering=lambda inst, val: seen.append(val))
            vb.dispatch('on_buffering', True)
            vb.dispatch('on_buffering', False)
        finally:
            vb.unload()
        self.assertEqual(seen, [True, False])

    def test_generate_thumbnail_default_returns_none(self):
        from kivy.core.video import VideoBase
        result = VideoBase.generate_thumbnail('does-not-matter.mp4', 0.0)
        self.assertIsNone(result)
