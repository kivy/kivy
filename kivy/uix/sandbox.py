'''
Sandbox
=======

'''

from kivy.context import Context
from kivy.base import ExceptionManagerBase
from kivy.uix.widget import Widget

def sandbox(f):
    def _f2(self, *args, **kwargs):
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


class Sandbox(Widget):

    def __init__(self, **kwargs):
        self._context = Context()
        self._context['ExceptionManager'] = SandboxExceptionManager(self)
        self._context.push()
        self.on_context_created()
        super(Sandbox, self).__init__(**kwargs)
        self._context.pop()

    def __enter__(self):
        #print 'ENTERING THE SANDBOX', self
        self._context.push()

    def __exit__(self, _type, value, traceback):
        self._context.pop()
        #print 'EXITING THE SANDBOX', (self, _type, value, traceback)
        if _type is not None:
            return self.on_exception(value, traceback=traceback)

    def on_context_created(self):
        # override this method in order to load kv, or anything you need afte
        # the new created context.
        print 'on_context_created()'

    def on_exception(self, exception, traceback=None):
        # override this method in order to deal with exceptions
        # return True = don't reraise the exception
        # return False = raise to the parent
        print 'on_exception() {!r} {!r}'.format(exception, traceback)
        return True

    on_touch_down = sandbox(Widget.on_touch_down)
    on_touch_move = sandbox(Widget.on_touch_move)
    on_touch_up = sandbox(Widget.on_touch_move)


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
