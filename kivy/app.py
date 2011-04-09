'''
Application
===========

The :class:`App` class is the base for creating Kivy applications.
Think of it as your main entry point into the Kivy runloop.  In most cases, you
subclass this class and make your own app. You create an instance of your
specific app class and then, when you are ready to start the application's life
cycle, you call your instance's :func:`App.run` method.

Create an application by overidding build()
-------------------------------------------

To initialize your app with a widget tree, override the build() method in
your app class and return the widget tree you constructed.

Here's an example of very simple application that just shows a button::

    from kivy.app import App
    from kivy.uix.button import Button

    class TestApp(App):
        def build(self):
            return Button(text='hello world')

    if __name__ == '__main__':
        TestApp().run()

Check :file:`kivy/examples/application/app_with_build.py`.


Create an application with kv file
----------------------------------

You can also use the :doc:`api-kivy.lang` for creating application. The .kv can
contain rules and root widget definitions at the same time. Here is the same
example as the Button one in a kv file.

Content of 'test.kv'::

    #:kivy 1.0

    Button:
        text: 'Hello world'


Content of 'main.py'::

    from kivy.app import App

    class TestApp(App):
        pass

    if __name__ == '__main__':
        TestApp().run()

Check :file:`kivy/examples/application/app_with_kv.py`.

The relation between main.py and test.kv is explained in :func:`App.load_kv`.

'''

from inspect import getfile
from os.path import dirname, join, exists
from kivy.base import runTouchApp, stopTouchApp
from kivy.event import EventDispatcher
from kivy.lang import Builder


class App(EventDispatcher):
    ''' Application class, see module documentation for more informations.

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

        #: Root widget setted by the :func:`build` method or by the
        #: :func:`load_kv` method if the kv file return a root widget.
        self.root = None

    def build(self):
        '''Initializes the application, will be called only once.
        If this method returns a widget (tree), it will be used as the root
        widget and added to the window.
        '''
        pass

    def load_kv(self,directory=None):
        '''If the application have never been built, try to find the kv of the
        application in the same directory as the application class.

        For example, if you have a file named main.py that contains::

            class ShowcaseApp(App):
                pass

        The :func:`load_kv` will search for a file named `showcase.kv` in
        the directory of the main.py. The name of the kv file is the lower name
        of the class, without the App at the end if exist.

        You can define rules and root widget in your kv file::

            <ClassName>: # this is a rule
                ...

            ClassName: # this is a root widget
                ...

        You cannot declare a root widget twice. Check :doc:`api-kivy.lang`
        documentation for more information about how to create kv files. If your
        kv file return a root widget, it will be set in self.root
        '''
        if directory is None:
            directory = dirname(getfile(self.__class__))
        clsname = self.__class__.__name__
        if clsname.endswith('App'):
            clsname = clsname[:-3]
        filename = join(directory, '%s.kv' % clsname.lower())
        if not exists(filename):
            return
        root = Builder.load_file(filename)
        if root:
            self.root = root

    def run(self,directory = None):
        '''Launches the app in standalone mode.
        '''
        if not self.built:
            self.load_kv(directory)
            root = self.build()
            if root:
                self.root = root
        self.dispatch('on_start')
        if self.root:
            runTouchApp(self.root)
        else:
            runTouchApp()
        self.dispatch('on_stop')

    def stop(self, *largs):
        '''Stop the application.

        If you use this method, the whole application will stop by using
        :func:`~kivy.base.stopTouchApp` call.
        '''
        stopTouchApp()

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

