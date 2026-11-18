
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

    def test_on_error_event_registered(self):
        from kivy.core.video import VideoBase
        self.assertIn('on_error', VideoBase.__events__)

    def test_do_error_stops_then_dispatches_once(self):
        from kivy.core.video import VideoBase
        vb = VideoBase(filename=None)
        events = []
        try:
            vb.bind(on_buffering=lambda inst, val: events.append(
                ('buffering', val)))
            vb.bind(on_error=lambda inst, err: events.append(
                ('error', err, inst.state, inst.buffering)))
            vb.play()
            vb._buffering = True
            vb._do_error('boom')
        finally:
            vb.unload()
        # Buffering is cleared first, then on_error fires once with
        # playback already stopped.
        self.assertEqual(
            events, [('buffering', False), ('error', 'boom', '', False)])

    def test_do_error_without_handler_does_not_raise(self):
        from kivy.core.video import VideoBase
        vb = VideoBase(filename=None)
        try:
            vb.play()
            vb._do_error('boom')
            self.assertEqual(vb.state, '')
        finally:
            vb.unload()


class VideoWidgetErrorTestCase(unittest.TestCase):
    '''on_error on the Video and VideoPlayer widgets, without depending
    on any particular video provider.
    '''

    def test_missing_file_stops_and_dispatches_on_error(self):
        from kivy.uix.video import Video
        video = Video(source='does-not-exist-kivy-test.mp4', state='play')
        errors = []
        video.bind(on_error=lambda inst, err: errors.append(
            (err, inst.state)))
        video._do_video_load()
        self.assertEqual(video.state, 'stop')
        self.assertFalse(video.loaded)
        self.assertEqual(len(errors), 1)
        self.assertIn('does-not-exist-kivy-test.mp4', errors[0][0])
        self.assertEqual(errors[0][1], 'stop')

    def test_core_error_stops_widget(self):
        from kivy.uix.video import Video
        video = Video(state='play')
        errors = []
        video.bind(on_error=lambda inst, err: errors.append(
            (err, inst.state)))
        video._on_error(None, 'decoder missing')
        self.assertEqual(errors, [('decoder missing', 'stop')])

    def test_video_player_forwards_on_error(self):
        from kivy.uix.videoplayer import VideoPlayer
        player = VideoPlayer(source='does-not-exist-kivy-test.mp4',
                             state='play')
        errors = []
        player.bind(on_error=lambda inst, err: errors.append(
            (err, inst.state)))
        player._do_video_load()
        player._video._do_video_load()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0][1], 'stop')
        self.assertEqual(player.state, 'stop')
