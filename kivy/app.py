'''
Application object
==================

Example of very simple application with button ::

    from kivy.app import App
    from kivy.uix.button import Button

    class MyApp(App):
        def build(self):
            return Button(label='hello world')

    MyApp().run()
'''

from kivy.base import runTouchApp
from kivy.event import EventDispatcher


class App(EventDispatcher):
    '''App class is a the base for creating Kivy application.

    :Events:
        `on_start`:
            Fired when the application is beeing started (before the
            :func:`~kivy.base.runTouchApp` call.
        `on_stop`:
            Fired when the application stop.
    '''

    def __init__(self, **kwargs):
        super(App, self).__init__()
        self.register_event_type('on_start')
        self.register_event_type('on_stop')
        self.options = kwargs
        self.use_default_uxl = kwargs.get('use_default_uxl', True)
        self.built = False
        self.root = None

    def build(self):
        '''Initialization of the application, will be called only once.
        If the build() return a widget, it will be used as the root widget.
        '''
        pass

    def run(self):
        '''Launch the app in standalone mode
        '''
        if not self.built:
            root = self.build()
            if root:
                self.root = root
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

