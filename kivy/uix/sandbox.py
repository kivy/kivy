'''
Sandbox
=======

'''

from kivy.context import Context
from kivy.base import ExceptionManagerBase
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout

def sandbox(f):
    def _f2(self, *args, **kwargs):
        ret = None
        with self:
            ret = f(self, *args, **kwargs)
        return ret
    return _f2


class SandboxExceptionManager(ExceptionManagerBase):

    def __init__(self, sandbox):
        ExceptionManagerBase.__init__(self)
        self.sandbox = sandbox

    def handle_exception(self, e):
        if not self.sandbox.on_exception(e):
            return ExceptionManagerBase.RAISE
        return ExceptionManagerBase.PASS


class SandboxContent(RelativeLayout):
    pass


class Sandbox(FloatLayout):

    def __init__(self, **kwargs):
        self._context = Context()
        self._context['ExceptionManager'] = SandboxExceptionManager(self)
        self._context.push()
        self.on_context_created()
        super(Sandbox, self).__init__(**kwargs)
        self._container = SandboxContent()
        self._context.pop()

        # now force Clock scheduling
        Clock.schedule_interval(self._clock_sandbox, 0)
        Clock.schedule_interval(self._clock_sandbox_draw, -1)

    def __enter__(self):
        #print 'ENTERING THE SANDBOX', self
        self._context.push()

    def __exit__(self, _type, value, traceback):
        self._context.pop()
        #print 'EXITING THE SANDBOX', (self, _type, value, traceback)
        if _type is not None:
            return self.on_exception(value, _traceback=traceback)

    def on_context_created(self):
        # override this method in order to load kv, or anything you need afte
        # the new created context.
        print 'on_context_created()'

    def on_exception(self, exception, _traceback=None):
        # override this method in order to deal with exceptions
        # return True = don't reraise the exception
        # return False = raise to the parent
        print 'on_exception() {!r} {!r}'.format(exception, _traceback)
        import traceback
        traceback.print_tb(_traceback)
        return True

    on_touch_down = sandbox(Widget.on_touch_down)
    on_touch_move = sandbox(Widget.on_touch_move)
    on_touch_up = sandbox(Widget.on_touch_move)

    @sandbox
    def add_widget(self, *args, **kwargs):
        self._container.add_widget(*args, **kwargs)

    @sandbox
    def remove_widget(self, *args, **kwargs):
        self._container.remove_widget(*args, **kwargs)

    @sandbox
    def clear_widgets(self, *args, **kwargs):
        self._container.clear_widgets()

    @sandbox
    def on_size(self, *args):
        self._container.size = self.size

    @sandbox
    def on_pos(self, *args):
        self._container.pos = self.pos

    @sandbox
    def _clock_sandbox(self, dt):
        import pdb; pdb.set_trace()
        Clock.tick(dt)
        Builder.apply()

    @sandbox
    def _clock_sandbox_draw(self, dt):
        Clock.tick_draw()
        Builder.apply()


if __name__ == '__main__':
    from kivy.uix.button import Button
    from kivy.base import runTouchApp
    from kivy.lang import Builder
    s = Sandbox()
    with s:
        Builder.load_string('''
<Button>:
    canvas:
        Color:
            rgb: (.3, .2, 0) if self.state == 'normal' else (.7, .7, 0)
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgb: 1, 1, 1
        Rectangle:
            size: self.texture_size
            pos: self.center_x - self.texture_size[0] / 2., self.center_y - self.texture_size[1] / 2.
            texture: self.texture

    # invalid... for testing.
    on_release: args()
''')

        s.add_widget(Button(text='Hello World'))

        # this exception is within the "with" block, but will be ignored by
        # default because the sandbox on_exception will return True
        raise Exception('hello')

    runTouchApp(s)
