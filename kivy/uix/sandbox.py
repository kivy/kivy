'''
Sandbox
=======

'''

from kivy.context import Context
from kivy.base import ExceptionManagerBase, EventLoop
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.lang import Builder

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
        #Passed True to init because if False is passed then Builder and Clock
        #are not sandboxed.
        self._context = Context(init=True)
        self._context['ExceptionManager'] = SandboxExceptionManager(self)
        self._context.sandbox = self
        self._context.push()
        self.on_context_created()
        self._container = None
        super(Sandbox, self).__init__(**kwargs)
        self._container = SandboxContent(size=self.size, pos=self.pos)
        super(Sandbox, self).add_widget(self._container)
        self._context.pop()
        
        #force SandboxClock's scheduling
        Clock.schedule_interval(self._clock_sandbox, 0)
        Clock.schedule_once(self._clock_sandbox_draw, -1)
        self.main_clock = object.__getattribute__(Clock, '_obj')

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
    on_touch_up = sandbox(Widget.on_touch_up)
        
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
        if self._container:
            self._container.size = self.size

    @sandbox
    def on_pos(self, *args):
        if self._container:
            self._container.pos = self.pos

    @sandbox
    def _clock_sandbox(self, dt):
        #import pdb; pdb.set_trace()
        Clock.tick()
        Builder.sync()

    @sandbox
    def _clock_sandbox_draw(self, dt):
        Clock.tick_draw()
        Builder.sync()
        self.main_clock.schedule_once(self._call_draw, 0)

    def _call_draw(self, dt):
        self.main_clock.schedule_once(self._clock_sandbox_draw, -1)

from kivy.uix.button import Button
from kivy.uix.label import Label

class TestButton(Button):

    def on_touch_up(self, touch):
        #raise Exception('fdfdfdfdfdfdfd')
        return super(TestButton, self).on_touch_up(touch)

    def on_touch_down(self, touch):
        #raise Exception('')
        return super(TestButton, self).on_touch_down(touch)

if __name__ == '__main__':
    from kivy.base import runTouchApp
    from kivy.lang import Builder
    s = Sandbox()
    with s:
        Builder.load_string('''
<TestButton>:
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
    #on_touch_up: root.d()
    #on_touch_down: root.f()
    on_release: root.args()
    #on_press: root.args()
''')
        b = TestButton(text='Hello World')
        s.add_widget(b)

        # this exception is within the "with" block, but will be ignored by
        # default because the sandbox on_exception will return True
        raise Exception('hello')
    #print object.__getattribute__(Clock, '_obj')
    runTouchApp(s)
