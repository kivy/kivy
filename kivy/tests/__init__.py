from kivy.tests.common import GraphicUnitTest, UnitTestTouch, UTMotionEvent, \
    async_run
try:
    from kivy.tests.async_common import UnitKivyApp
except SyntaxError:
    # async app tests would be skipped due to async_run forcing it to skip so
    # it's ok to be None as it won't be used anyway
    UnitKivyApp = None

__all__ = ('GraphicUnitTest', 'UnitTestTouch', 'UTMotionEvent', 'async_run',
           'UnitKivyApp')
