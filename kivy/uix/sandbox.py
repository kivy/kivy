'''
Sandbox
=======

'''

from kivy.context import Context
from kivy.uix.widget import Widget

def sandbox(f):

    def _f2(*args, **kwargs):
        ret = f(*args, **kwargs)
        return ret

    return _f2


class Sandbox(Widget):

    def __init__(self, **kwargs):
        self._context = Context()
        self._context.push()
        self.on_context_created()
        super(Sandbox, self).__init__(**kwargs)
        self._context.pop()

    def __enter__(self):
        print 'ENTERING THE SANDBOX', self
        self._context.push()

    def __exit__(self, type, value, traceback):
        self._context.pop()
        print 'EXITING THE SANDBOX', (self, type, value, traceback)

    def on_context_created(self):
        # override this method in order to load kv, or anything you need afte
        # the new created context.
        pass


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
            rgb: 1, 1, 0
        Rectangle:
            pos: self.pos
            size: self.size
''')
        s.add_widget(Button())
    runTouchApp(s)
