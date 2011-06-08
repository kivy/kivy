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
from kivy.config import ConfigParser
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

    use_kivy_settings = True
    '''.. versionadded:: 1.0.7

    If True, the application settings will include also the Kivy settings. If
    you don't want the user to change any kivy settings from your settings UI,
    change this to False.
    '''

    def __init__(self, **kwargs):
        self._app_directory = None
        self._app_name = None
        self._app_settings = None
        super(App, self).__init__()
        self.register_event_type('on_start')
        self.register_event_type('on_stop')
        self.options = kwargs
        self.use_default_uxl = kwargs.get('use_default_uxl', True)
        self.built = False
        self.config = self.load_config()

        #: Root widget set by the :func:`build` method or by the
        #: :func:`load_kv` method if the kv file contains a root widget.
        self.root = None

    def build(self):
        '''Initializes the application; will be called only once.
        If this method returns a widget (tree), it will be used as the root
        widget and added to the window.
        '''
        pass

    def build_config(self, config):
        '''.. versionadded:: 1.0.7

        This method is called before the application is initialized to construct
        your :class:`~kivy.config.ConfigParser` object. This is where you can
        put any default section / key / value for your config. If anything is
        set, the configuration will be automatically saved in the file returned
        by :meth:`get_application_config`.

        :param config: :class:`~kivy.config.ConfigParser` instance.
        '''

    def build_settings(self, settings):
        '''.. versionadded:: 1.0.7

        This method is called when the user (or you) want to show the
        application settings. This will be called only once, the first time when
        the user will show the settings.

        :param settings: :class:`~kivy.uix.settings.Settings` instance
        '''

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
        '''Return the name of the application.
        '''
        if self.title is not None:
            return self.title
        clsname = self.__class__.__name__
        if clsname.endswith('App'):
            clsname = clsname[:-3]
        return clsname

    def get_application_icon(self):
        '''Return the icon of the application.
        '''
        if self.icon is not None:
            return resource_find(self.icon)
        return None

    def get_application_config(self):
        '''.. versionadded:: 1.0.7

        Return the filename of your application configuration
        '''
        return join(self.directory, '%s.ini' % self.name)

    def load_config(self):
        '''(internal) This function is used for returning a ConfigParser with
        the application configuration. It's doing 3 things:
            
            #. Create an instance of a ConfigParser
            #. Load the default configuration by calling
               :meth:`build_config`, then
            #. If exist, load the application configuration file, or create it
               if it's not existing.
        '''
        config = ConfigParser()
        self.build_config(config)
        # if no sections are created, that's mean the user don't have
        # configuration.
        if len(config.sections()) == 0:
            return
        # ok, the user have some sections, read the default file if exist
        # or write it !
        filename = self.get_application_config()
        if filename is None:
            return config
        if exists(filename):
            config.read(filename)
        else:
            config.filename = filename
            config.write()
        return config

    @property
    def directory(self):
        '''.. versionadded:: 1.0.7

        Return the directory where the application live
        '''
        if self._app_directory is None:
            self._app_directory = dirname(getfile(self.__class__))
        return self._app_directory

    @property
    def name(self):
        '''.. versionadded:: 1.0.7

        Return the name of the application, based on the class name
        '''
        if self._app_name is None:
            clsname = self.__class__.__name__
            if clsname.endswith('App'):
                clsname = clsname[:-3]
            self._app_name = clsname.lower()
        return self._app_name

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
            self._install_settings_keys(window)

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

    def on_config_change(self, config, section, key, value):
        '''Event handler fired when one configuration token have been changed by
        the settings page.
        '''
        pass

    def _on_config_change(self, *largs):
        self.on_config_change(*largs[1:])

    def _install_settings_keys(self, window):
        window.bind(on_keyboard=self._on_keyboard_settings)

    def _on_keyboard_settings(self, window, *largs):
        key = largs[0]
        if key == 282: # F1
            self._toggle_settings(window)
            return True
        if key == 27:
            return self._close_settings()

    def _close_settings(self, *largs):
        if self._app_settings is None:
            return
        parent = self._app_settings.parent
        if parent is None:
            return
        parent.remove_widget(self._app_settings)
        return True

    def _toggle_settings(self, window):
        from kivy.uix.settings import Settings
        if self._app_settings is None:
            self._app_settings = s = Settings()
            self.build_settings(s)
            if self.use_kivy_settings:
                s.add_kivy_panel()
            s.bind(on_close=self._close_settings,
                   on_config_change=self._on_config_change)
        if self._app_settings in window.children:
            window.remove_widget(self._app_settings)
        else:
            window.add_widget(self._app_settings)

