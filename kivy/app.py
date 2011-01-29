'''
The Application Object
======================

Here's an example of very simple application that just shows a button::

    from kivy.app import App
    from kivy.uix.button import Button

    class MyApp(App):
        def build(self):
            return Button(text='hello world')

    MyApp().run()
'''

from kivy.base import runTouchApp
from kivy.event import EventDispatcher


class App(EventDispatcher):
    '''The App class is the base for creating Kivy applications.
       Think of it as your main entry point into the Kivy runloop.
       In most cases, you subclass this class and make your own app.
       You create an instance of your specific app class and then, when you are
       ready to start the application's life cycle, you call your instance's
       run() method.

       To initialize your app with a widget tree, override the build() method in
       your app class and return the widget tree you constructed.


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
        '''Initializes the application, will be called only once.
        If this method returns a widget (tree), it will be used as the root
        widget and added to the window.
        '''
        pass

    def run(self):
        '''Launches the app in standalone mode.
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
        '''Event handler for the on_start event, which is fired after
        initialization (after build() has been called), and before the
        application is being run.
        '''
        pass

    def on_stop(self):
        '''Event handler for the on_stop event, which is fired when the
        application has finished running (e.g. the window is about to be
        closed).
        '''
        pass

