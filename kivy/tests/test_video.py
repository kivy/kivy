
import unittest


class AnimationTestCase(unittest.TestCase):

    def test_video_unload(self):
        # fix issue https://github.com/kivy/kivy/issues/2275
        # AttributeError: 'NoneType' object has no attribute 'texture'
        from kivy.uix.video import Video
        from kivy.clock import Clock
        from kivy.base import runTouchApp, stopTouchApp
        from os.path import join, dirname, abspath
        here = dirname(__file__)
        source = abspath(join(
            here, "..", "..", "examples", "widgets", "softboy.mpg"))
        video = Video(source=source, play=True)
        Clock.schedule_once(lambda x: stopTouchApp(), 1)

        def unload_video(video, position):
            if position > 0.01:
                video.unload()
                Clock.schedule_once(lambda x: stopTouchApp(), 0.1)

        video.bind(position=unload_video)
        runTouchApp(video)
