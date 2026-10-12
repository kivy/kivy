import gc
import unittest
import weakref

from kivy.event import EventDispatcher
from kivy.input.recorder import Recorder


class RecorderWindow(EventDispatcher):
    __events__ = ('on_motion', 'on_key_up', 'on_key_down', 'on_keyboard')

    def on_motion(self, *args):
        pass

    def on_key_up(self, *args):
        pass

    def on_key_down(self, *args):
        pass

    def on_keyboard(self, *args):
        pass


class TrackingRecorder(Recorder):

    def __init__(self, **kwargs):
        self.calls = []
        super().__init__(**kwargs)

    def on_keyboard(self, etype, window, key, *args, **kwargs):
        self.calls.append((etype, key))


class RecorderReleaseTest(unittest.TestCase):

    def test_release_removes_all_observers(self):
        window = RecorderWindow()
        recorder = Recorder(window=window)
        for event in window.__events__:
            self.assertEqual(len(window.get_property_observers(event)), 1)
        recorder.release()
        for event in window.__events__:
            with self.subTest(event=event):
                self.assertEqual(window.get_property_observers(event), [])

    def test_released_recorder_no_longer_receives_keys(self):
        window = RecorderWindow()
        recorder = TrackingRecorder(window=window)
        window.dispatch('on_key_down', 65)
        window.dispatch('on_key_up', 65)
        window.dispatch('on_keyboard', 65)
        expected = [('keydown', 65), ('keyup', 65), ('keyboard', 65)]
        self.assertEqual(recorder.calls, expected)
        recorder.release()
        recorder.release()
        window.dispatch('on_key_down', 66)
        window.dispatch('on_key_up', 66)
        window.dispatch('on_keyboard', 66)
        self.assertEqual(recorder.calls, expected)

    def test_release_preserves_other_recorder(self):
        window = RecorderWindow()
        first = TrackingRecorder(window=window)
        second = TrackingRecorder(window=window)
        self.addCleanup(second.release)
        first.release()
        window.dispatch('on_keyboard', 65)
        self.assertEqual(first.calls, [])
        self.assertEqual(second.calls, [('keyboard', 65)])

    def test_released_recorder_can_be_collected(self):
        window = RecorderWindow()
        recorder = Recorder(window=window)
        reference = weakref.ref(recorder)
        recorder.release()
        del recorder
        gc.collect()
        self.assertIsNone(reference())


if __name__ == '__main__':
    unittest.main()
