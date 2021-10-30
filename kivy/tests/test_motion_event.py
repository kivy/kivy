import pytest

from kivy.compat import isclose
from kivy.input import MotionEvent


class DummyMotionEvent(MotionEvent):
    pass


class TestMotionEvent:

    def build_to_absolute_pos_data(self, x_max, y_max, x_step, y_step):
        for x, y in zip(range(0, x_max, x_step), range(0, y_max, y_step)):
            result = (x, y)
            yield x / x_max, y / y_max, x_max, y_max, 0, result
        for x, y, in zip(range(0, x_max, x_step), range(0, y_max, y_step)):
            result = (y, x_max - x)
            yield x / x_max, y / y_max, x_max, y_max, 90, result
        for x, y, in zip(range(0, x_max, x_step), range(0, y_max, y_step)):
            result = (x_max - x, y_max - y)
            yield x / x_max, y / y_max, x_max, y_max, 180, result
        for x, y, in zip(range(0, x_max, x_step), range(0, y_max, y_step)):
            result = (y_max - y, x)
            yield x / x_max, y / y_max, x_max, y_max, 270, result

    def test_to_absolute_pos(self):
        event = DummyMotionEvent('fake', 'fake1', (0, 0))
        for item in self.build_to_absolute_pos_data(320, 240, 20, 21):
            args = item[:-1]
            expected_x, expected_y = item[-1]
            x, y = event.to_absolute_pos(*args)
            message = ('For args {} expected ({}, {}), got ({}, {})'
                       .format(args, x, y, expected_x, expected_y))
            correct = isclose(x, expected_x) and isclose(y, expected_y)
            assert correct, message

    def test_to_absolute_pos_error(self):
        event = DummyMotionEvent('fake', 'fake1', (0, 0))
        with pytest.raises(ValueError):
            event.to_absolute_pos(0, 0, 100, 100, 10)
