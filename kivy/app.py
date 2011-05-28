'''
Application
===========

The :class:`App` class is the base for creating Kivy applications.
Think of it as your main entry point into the Kivy run loop.  In most cases, you
subclass this class and make your own app. You create an instance of your
specific app class and then, when you are ready to start the application's life
cycle, you call your instance's :func:`App.run` method.


Creating an Application by Overriding build()
---------------------------------------------

To initialize your app with a widget tree, override the build() method in
your app class and return the widget tree you constructed.

Here's an example of very simple application that just shows a button:

.. include:: ../examples/application/app_with_build.py
   :literal:

The file is also available in the examples folder at
:file:`kivy/examples/application/app_with_build.py`.

Here, no widget tree was constructed (or if you will, a tree with only the root
node).


Creating an Application via kv File
------------------------------------

You can also use the :doc:`api-kivy.lang` for creating application. The .kv can
contain rules and root widget definitions at the same time. Here is the same
example as the Button one in a kv file.

Contents of 'test.kv':

.. include:: ../examples/application/test.kv
   :literal:

Contents of 'main.py':

.. include:: ../examples/application/app_with_kv.py
   :literal:

See :file:`kivy/examples/application/app_with_kv.py`.

The relation between main.py and test.kv is explained in :func:`App.load_kv`.
'''

from inspect import getfile
from os.path import dirname, join, exists
from kivy.base import runTouchApp, stopTouchApp
from kivy.logger import Logger
from kivy.event import EventDispatcher
from kivy.lang import Builder
from kivy.resources import resource_find


class App(EventDispatcher):
    ''' Application class, see module documentation for more information.

    :Events:
        `on_start`:
            Fired when the application is being started (before the
            :func:`~kivy.base.runTouchApp` call.
        `on_stop`:
            Fired when the application stops.

    :Parameters:
        `kv_directory`: <path>, default to None
            If a kv_directory is set, it will be used to get the initial kv
            file. By default, the file is searched in the same directory as the
            current App definition file.
    '''

    title = None
    '''.. versionadded:: 1.0.5

    Title of your application. You can set by doing::

        class MyApp(App):
            title = 'Custom title'

    '''

    icon = None
    '''.. versionadded:: 1.0.5

    Icon of your application. You can set by doing::

        class MyApp(App):
            icon = 'customicon.png'

    The icon can be located in the same directory as your main file.
    '''

    def __init__(self, **kwargs):
        super(App, self).__init__()
        self.register_event_type('on_start')
        self.register_event_type('on_stop')
        self.options = kwargs
        self.use_default_uxl = kwargs.get('use_default_uxl', True)
        self.built = False

        #: Root widget set by the :func:`build` method or by the
        #: :func:`load_kv` method if the kv file contains a root widget.
        self.root = None

    def build(self):
        '''Initializes the application; will be called only once.
        If this method returns a widget (tree), it will be used as the root
        widget and added to the window.
        '''
        pass

    def load_kv(self):
        '''This method is invoked the first time the app is being run if no
        widget tree has been constructed before for this app.
        This method then looks for a matching kv file in the same directory as
        the file that contains the application class.

        For example, if you have a file named main.py that contains::

            class ShowcaseApp(App):
                pass

        This method will search for a file named `showcase.kv` in
        the directory that contains main.py. The name of the kv file has to be
        the lowercase name of the class, without the 'App' postfix at the end
        if it exists.

        You can define rules and a root widget in your kv file::

            <ClassName>: # this is a rule
                ...

            ClassName: # this is a root widget
                ...

        There must be only one root widget. See the :doc:`api-kivy.lang`
        documentation for more information on how to create kv files. If your
        kv file contains a root widget, it will be used as self.root, the root
        widget for the application.
        '''
        kv_directory = self.options.get('kv_directory',
            dirname(getfile(self.__class__)))
        clsname = self.__class__.__name__
        if clsname.endswith('App'):
            clsname = clsname[:-3]
        filename = join(kv_directory, '%s.kv' % clsname.lower())
        if not exists(filename):
            Logger.debug('App: kv <%s> not found' % filename)
            return False
        root = Builder.load_file(filename)
        if root:
            self.root = root
        return True

    def get_application_name(self):
        if self.title is not None:
            return self.title
        clsname = self.__class__.__name__
        if clsname.endswith('App'):
            clsname = clsname[:-3]
        return clsname

    def get_application_icon(self):
        if self.icon is not None:
            return resource_find(self.icon)
        return None

    def run(self):
        '''Launches the app in standalone mode.
        '''
        if not self.built:
            self.load_kv()
            root = self.build()
            if root:
                self.root = root
        if self.root:
            from kivy.core.window import Window
            Window.add_widget(self.root)

        # Check if the window is already created
        from kivy.base import EventLoop
        window = EventLoop.window
        if window:
            window.set_title(self.get_application_name())
            icon = self.get_application_icon()
            if icon:
                window.set_icon(icon)

        # Run !
        self.dispatch('on_start')
        runTouchApp()
        self.dispatch('on_stop')

    def stop(self, *largs):
        '''Stop the application.

        If you use this method, the whole application will stop by issuing
        a call to :func:`~kivy.base.stopTouchApp`.
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

