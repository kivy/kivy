'''
Application
===========

The :class:`App` class is the base for creating Kivy applications.
Think of it as your main entry point into the Kivy run loop.  In most cases, you
subclass this class and make your own app. You create an instance of your
specific app class and then, when you are ready to start the application's life
cycle, you call your instance's :func:`App.run` method.


Creating an Application
-----------------------

Method using build() override
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To initialize your app with a widget tree, override the build() method in
your app class and return the widget tree you constructed.

Here's an example of a very simple application that just shows a button:

.. include:: ../../examples/application/app_with_build.py
   :literal:

The file is also available in the examples folder at
:file:`kivy/examples/application/app_with_build.py`.

Here, no widget tree was constructed (or if you will, a tree with only the root
node).


Method using kv file
~~~~~~~~~~~~~~~~~~~~

You can also use the :doc:`api-kivy.lang` for creating applications. The .kv can
contain rules and root widget definitions at the same time. Here is the same
example as the Button one in a kv file.

Contents of 'test.kv':

.. include:: ../../examples/application/test.kv
   :literal:

Contents of 'main.py':

.. include:: ../../examples/application/app_with_kv.py
   :literal:

See :file:`kivy/examples/application/app_with_kv.py`.

The relation between main.py and test.kv is explained in :func:`App.load_kv`.


Application configuration
-------------------------

.. versionadded:: 1.0.7

Use the configuration file
~~~~~~~~~~~~~~~~~~~~~~~~~~

Your application might want to have its own configuration file. The
:class:`App` is able to handle an INI file automatically. You add your
section/key/value in the :meth:`App.build_config` method by using the `config`
parameters (instance of :class:`~kivy.config.ConfigParser`::

    class TestApp(App):
        def build_config(self, config):
            config.setdefaults('section1', {
                'key1': 'value1',
                'key2': '42'
            })

As soon as you add one section in the config, a file is created on the disk, and
named from the mangled name of your class:. "TestApp" will give a config
file-name "test.ini" with the content::

    [section1]
    key1 = value1
    key2 = 42

The "test.ini" will be automatically loaded at runtime, and you can access the
configuration in your :meth:`App.build` method::

    class TestApp(App):
        def build_config(self, config):
            config.setdefaults('section1', {
                'key1': 'value1',
                'key2': '42'
            })

        def build(self):
            config = self.config
            return Label(text='key1 is %s and key2 is %d' % (
                config.get('section1', 'key1'),
                config.getint('section1', 'key2')))

Create a settings panel
~~~~~~~~~~~~~~~~~~~~~~~

Your application can have a settings panel to let your user configure some of
your config tokens. Here is an example done in the KinectViewer example
(available in the examples directory):

    .. image:: images/app-settings.jpg
        :align: center

You can extend the default application settings with your own panel by extending
the :meth:`App.build_settings` method.
Check the class:`~kivy.uix.settings.Settings` about how to create a panel,
because you need a JSON file / data first.

Let's take as an example the previous snippet of TestApp with custom config. We
could create a JSON like this::

    [
        { "type": "title",
          "title": "Test application" },

        { "type": "options",
          "title": "My first key",
          "desc": "Description of my first key",
          "section": "section1",
          "key": "key1",
          "options": ["value1", "value2", "another value"] },

        { "type": "numeric",
          "title": "My second key",
          "desc": "Description of my second key",
          "section": "section1",
          "key": "key2" }
    ]

Then, we can create a panel using this JSON to create automatically all the
options, and link them to our :data:`App.config` ConfigParser instance::

    class TestApp(App):
        # ...
        def build_settings(self, settings):
            jsondata = """... put the json data here ..."""
            settings.add_json_panel('Test application',
                self.config, data=jsondata)

That's all ! Now you can press F1 (default keystroke) to toggle the settings
panel, or press the "settings" key on your android device. You can manually call
:meth:`App.open_settings` and :meth:`App.close_settings` if you want. Every
change in the panel is automatically saved in the config file.

However, you might want to know when a config value has been changed by the
user, in order to adapt or reload your UI. You can overload the
:meth:`on_config_change` method::

    class TestApp(self):
        # ...
        def on_config_change(self, config, section, key, value):
            if config is self.config:
                token = (section, key)
                if token == ('section1', 'key1'):
                    print 'Our key1 have been changed to', value
                elif token == ('section1', 'key2'):
                    print 'Our key2 have been changed to', value

One last note, the Kivy configuration panel is added by default in the settings
instance. If you don't want it, you can declare your Application like this::

    class TestApp(App):
        use_kivy_settings = False
        # ...


Pause mode
----------

.. versionadded:: 1.1.0

.. warning::

    This mode is experimental, and designed for phones/tablets. There are some
    cases where your application could crash on resume.

On tablets and phones, the user can switch at any moment to another application.
By default, your application will reach :func:`App.on_stop` behavior.

You can support the Pause mode: when switching to another application, the
application goes into Pause mode and waits infinitely until the user
switches back to your application. There is an issue with OpenGL on Android
devices: you're not ensured that the OpenGL ES Context is restored when your app
resumes. The mechanism for restoring all the OpenGL data is not yet implemented
into Kivy(we are looking for device with this behavior).

The current implemented Pause mechanism is:

    #. Kivy checks every frame, if Pause mode is activated by the Operating
       System, due to user switching to another application, phone shutdown or
       any other reason.
    #. :func:`App.on_pause` is called:
    #. If False is returned (default case), then :func:`App.on_stop` is called.
    #. Otherwise the application will sleep until the OS will resume our App
    #. We got a `resume`, :func:`App.on_resume` is called.
    #. If our app memory has been reclaimed by the OS, then nothing will be
       called.

.. warning::

    Both `on_pause` and `on_stop` must save important data, because after
    `on_pause` call, on_resume may not be called at all.

'''

__all__ = ('App', )

from inspect import getfile
from os.path import dirname, join, exists
from kivy.config import ConfigParser
from kivy.base import runTouchApp, stopTouchApp
from kivy.logger import Logger
from kivy.event import EventDispatcher
from kivy.lang import Builder
from kivy.resources import resource_find
from kivy.utils import platform


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

    # Return the current running App instance
    _running_app = None

    def __init__(self, **kwargs):
        self._app_directory = None
        self._app_name = None
        self._app_settings = None
        self._app_window = None
        super(App, self).__init__()
        self.register_event_type('on_start')
        self.register_event_type('on_stop')
        self.register_event_type('on_pause')
        self.register_event_type('on_resume')
        self.built = False

        #: Options passed to the __init__ of the App
        self.options = kwargs

        #: Instance to the :class:`~kivy.config.ConfigParser` of the application
        #: configuration. Can be used to query some config token in the build()
        self.config = None

        #: Root widget set by the :func:`build` method or by the
        #: :func:`load_kv` method if the kv file contains a root widget.
        self.root = None

    def build(self):
        '''Initializes the application; will be called only once.
        If this method returns a widget (tree), it will be used as the root
        widget and added to the window.

        :return: None or a root :class:`~kivy.uix.widget.Widget` instance
        '''
        pass

    def build_config(self, config):
        '''.. versionadded:: 1.0.7

        This method is called before the application is initialized to construct
        your :class:`~kivy.config.ConfigParser` object. This is where you can
        put any default section / key / value for your config. If anything is
        set, the configuration will be automatically saved in the file returned
        by :meth:`get_application_config`.

        :param config: Use this to add defaults section / key / value
        :type config: :class:`~kivy.config.ConfigParser`

        '''

    def build_settings(self, settings):
        '''.. versionadded:: 1.0.7

        This method is called when the user (or you) want to show the
        application settings. This will be called only once, the first time when
        the user will show the settings.

        :param settings: Settings instance for adding panels
        :type settings: :class:`~kivy.uix.settings.Settings`
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

        :return: ConfigParser instance
        '''
        self.config = config = ConfigParser()
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
            self.load_config()
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
            self._app_window = window
            window.set_title(self.get_application_name())
            icon = self.get_application_icon()
            if icon:
                window.set_icon(icon)
            self._install_settings_keys(window)

        App._running_app = self
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

    def on_pause(self):
        '''Event handler called when pause mode is asked. You must return True
        if you can go to the Pause mode. Otherwise, return False, and your
        application will be stopped.

        You cannot control when the application is going to this mode. It's
        mostly used for embed devices (android/ios), and for resizing.

        Default is False.

        .. versionadded:: 1.1.0
        '''
        return False

    def on_resume(self):
        '''Event handler called when your application is resuming from the Pause
        mode.

        .. versionadded:: 1.1.0

        .. warning::

            When resuming, OpenGL Context might have been damaged / freed. This
            is where you should reconstruct some of your OpenGL state, like FBO
            content.
        '''
        pass

    @staticmethod
    def get_running_app():
        '''Return the current runned application instance.

        .. versionadded:: 1.1.0
        '''
        return App._running_app

    def on_config_change(self, config, section, key, value):
        '''Event handler fired when one configuration token have been changed by
        the settings page.
        '''
        pass

    def open_settings(self, *largs):
        '''Open the application settings panel. It will be created the very
        first time. Then the settings panel will be added to the Window attached
        to your application (automatically done by :meth:`run`)

        :return: True if the settings have been opened
        '''
        win = self._app_window
        if not win:
            raise Exception('No windows are set on the application, you cannot'
                            ' open settings yet.')
        settings = self._create_settings()
        if settings not in win.children:
            win.add_widget(settings)
            return True
        return False

    def close_settings(self, *largs):
        '''Close the previously opened settings panel.

        :return: True if the settings have been closed
        '''
        win = self._app_window
        settings = self._app_settings
        if win is None or settings is None:
            return
        if settings in win.children:
            win.remove_widget(settings)
            return True
        return False

    def _create_settings(self):
        from kivy.uix.settings import Settings
        if self._app_settings is None:
            self._app_settings = s = Settings()
            self.build_settings(s)
            if self.use_kivy_settings:
                s.add_kivy_panel()
            s.bind(on_close=self.close_settings,
                   on_config_change=self._on_config_change)
        return self._app_settings

    def _on_config_change(self, *largs):
        self.on_config_change(*largs[1:])

    def _install_settings_keys(self, window):
        window.bind(on_keyboard=self._on_keyboard_settings)

    def _on_keyboard_settings(self, window, *largs):
        key = largs[0]
        setting_key = 282 # F1

        # android hack, if settings key is pygame K_MENU
        if platform() == 'android':
            import pygame
            setting_key = pygame.K_MENU

        if key == setting_key:
            # toggle settings panel
            if not self.open_settings():
                self.close_settings()
            return True
        if key == 27:
            return self.close_settings()

