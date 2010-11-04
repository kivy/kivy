'''
App: base class for creating a Kivy application

Example of very simple application with button ::

    from kivy.app import App
    from kivy.uix.button import Button

    class MyApp(App):
        def init(self):
            self.root = Button(label='hello world'))

    MyApp().run()
'''

from kivy.base import EventLoop, runTouchApp
from kivy.event import EventDispatcher

class App(EventDispatcher):
    def __init__(self, **kwargs):
        super(App, self).__init__()
        self.register_event_type('on_start')
        self.register_event_type('on_stop')
        self.options = kwargs
        self.use_default_uxl = kwargs.get('use_default_uxl', True)
        self.is_build = False
        self.root = None

    def build(self):
        '''Initialization of the application, will be called only once.
        If the build() return a widget, it will be used as the root widget.
        '''
        pass

    def run(self):
        '''Launch the app in standalone mode
        '''
        if not self.is_build:
            self.root = self.build()
        self.dispatch('on_start')
        if self.root:
            runTouchApp(self.root)
        else:
            runTouchApp()
        self.dispatch('on_stop')

    def on_start(self):
        '''Event called after initialization, and before running the
        application
        '''
        pass

    def on_stop(self):
        '''Event called after running, before closing the application
        '''
        pass

