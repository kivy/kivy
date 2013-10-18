'''Application
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

You can add your own panels of settings by extending
the :meth:`App.build_settings` method.
Check the :class:`~kivy.uix.settings.Settings` about how to create a panel,
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

You can also use :meth:`App.build_settings` to modify properties of
the settings panel. For instance, the default panel has a sidebar for
switching between json panels, whose width defaults to 200dp. If you'd
prefer this to be narrower, you could add::

    settings.interface.menu.width = dp(100)

to your :meth:`build_settings` method.

You might want to know when a config value has been changed by the
user, in order to adapt or reload your UI. You can overload the
:meth:`on_config_change` method::

    class TestApp(App):
        # ...
        def on_config_change(self, config, section, key, value):
            if config is self.config:
                token = (section, key)
                if token == ('section1', 'key1'):
                    print('Our key1 have been changed to', value)
                elif token == ('section1', 'key2'):
                    print('Our key2 have been changed to', value)

The Kivy configuration panel is added by default to the settings
instance. If you don't want this panel, you can declare your Application like
this::

    class TestApp(App):
        use_kivy_settings = False
        # ...

This only removes the Kivy panel, but does not stop the settings instance
from appearing. If you want to prevent the settings instance from appearing
altogether, you can do this::

    class TestApp(App):
        def open_settings(self, *largs):
            pass

Profiling with on_start and on_stop
-----------------------------------

It is often useful to profile python code in order to discover locations to
optimise. The standard library profilers
(http://docs.python.org/2/library/profile.html) provide multiple options for
profiling code. For profiling the entire program, the natural
approaches of using profile as a module or profile's run method do not work
with Kivy. It is however possible to use :meth:`App.on_start` and
:meth:`App.on_stop` methods::

    import cProfile

    class MyApp(App):
        def on_start(self):
            self.profile = cProfile.Profile()
            self.profile.enable()

        def on_stop(self):
            self.profile.disable()
            self.profile.dump_stats('myapp.profile')

This will create a file called `myapp.profile` when you exit your app.

Customising layout
------------------

You can choose different settings widget layouts by setting
:attr:`App.settings_cls`. By default, this is
:class:`~kivy.uix.settings.Settings` which provides the pictured
sidebar layout, but you could set it to any of the other layouts
provided in :mod:`kivy.uix.settings` or create your own. See the
module documentation for :mod:`kivy.uix.settings` for more
information.

You can customise how the settings panel is actually displayed by
overriding :meth:`App.display_settings`, which is called to
actually display the settings panel on the screen. By default it
simply draws the panel on top of the window, but you could modify it
to (for instance) show the settings in a
:class:`~kivy.uix.popup.Popup` or add them to your app's
:class:`~kivy.uix.screenmanager.ScreenManager` if you are using
one. If you do so, you should also modify :meth:`App.close_settings`
to exit the panel appropriately. For instance, to have the settings
panel appear in a popup you can do::

    def display_settings(self, settings):
        try:
            p = self.settings_popup
        except AttributeError:
            self.settings_popup = Popup(content=settings,
                                        title='Settings',
                                        size_hint=(0.8, 0.8))
            p = self.settings_popup
        if p.content is not settings:
            p.content = settings
        p.open()
    def close_settings(self, *args):
        try:
            p = self.settings_popup
            p.dismiss()
        except AttributeError:
            pass # Settings popup doesn't exist

Finally, if you want to replace the current settings panel widget, you
can remove the internal references to it using
:meth:`App.destroy_settings`. If you have modified
:meth:`App.display_settings`, you should be careful to detect if the
settings panel has been replaced.

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

Here is a simple example of how on_pause() should be used::

   class TestApp(App):

      def on_pause(self):
         # Here you can save data if needed
         return True

      def on_resume(self):
         # Here you can check if any data needs replacing (usually nothing)
         pass

.. warning::

    Both `on_pause` and `on_stop` must save important data, because after
    `on_pause` call, on_resume may not be called at all.

'''

__all__ = ('App', )

import os
from inspect import getfile
from os.path import dirname, join, exists, sep, expanduser, isfile
from kivy.config import ConfigParser
from kivy.base import runTouchApp, stopTouchApp
from kivy.logger import Logger
from kivy.event import EventDispatcher
from kivy.lang import Builder
from kivy.resources import resource_find
from kivy.utils import platform as core_platform
from kivy.uix.widget import Widget
from kivy.uix.settings import SettingsWithSpinner
from kivy.properties import ObjectProperty


platform = core_platform


class App(EventDispatcher):
    ''' Application class, see module documentation for more information.

    :Events:
        `on_start`:
            Fired when the application is being started (before the
            :func:`~kivy.base.runTouchApp` call.
        `on_stop`:
            Fired when the application stops.
        `on_pause`:
            Fired when the application is paused by the OS.
        `on_resume`:
            Fired when the application is resumed from pause by the OS, beware,
            you have no garantee that this event will be fired after the
            on_pause event has been called.

    :Parameters:
        `kv_directory`: <path>, default to None
            If a kv_directory is set, it will be used to get the initial kv
            file. By default, the file is searched in the same directory as the
            current App definition file.
        `kv_file`: <filename>, default to None
            If a kv_file is set, it will be loaded when the application start.
            The loading of the "default" kv will be avoided.

    .. versionchanged:: 1.7.0
        Parameter `kv_file` added.
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

    settings_cls = ObjectProperty(SettingsWithSpinner)
    '''.. versionadded:: 1.8.0

    The class to use to construct the settings panel, used to
    construct the instance passed to :meth:`build_config`. You should
    use either :class:`~kivy.uix.settings.Settings`, or one of the provided
    subclasses with different layouts
    (:class:`~kivy.uix.settings.SettingsWithSidebar`,
    :class:`~kivy.uix.settings.SettingsWithSpinner`,
    :class:`~kivy.uix.settings.SettingsWithTabbedPanel`,
    :class:`~kivy.uix.settings.SettingsWithNoMenu`), or your own
    Settings subclass. See the documentation
    of :mod:`kivy.uix.Settings` for more information.

    :attr:`~App.settings_cls` is an :class:`~kivy.properties.ObjectProperty`.
    it defaults to :class:`~kivy.uix.settings.SettingsWithSpinner`, which
    displays settings panels with a spinner to switch between them.

    '''

    # Return the current running App instance
    _running_app = None

    __events__ = ('on_start', 'on_stop', 'on_pause', 'on_resume')

    def __init__(self, **kwargs):
        App._running_app = self
        self._app_directory = None
        self._app_name = None
        self._app_settings = None
        self._app_window = None
        super(App, self).__init__(**kwargs)
        self.built = False

        #: Options passed to the __init__ of the App
        self.options = kwargs

        #: Instance to the :class:`~kivy.config.ConfigParser` of the application
        #: configuration. Can be used to query some config token in the build()
        self.config = None

        #: Root widget set by the :meth:`build` method or by the
        #: :meth:`load_kv` method if the kv file contains a root widget.
        self.root = None

    def build(self):
        '''Initializes the application; will be called only once.
        If this method returns a widget (tree), it will be used as the root
        widget and added to the window.

        :return: None or a root :class:`~kivy.uix.widget.Widget` instance is no
                 self.root exist.
        '''
        if not self.root:
            return Widget()

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

        You can use this method to add settings panels and to
        customise the settings widget, e.g. by changing the sidebar
        width. See the module documentation for full details.

        :param settings: Settings instance for adding panels
        :type settings: :class:`~kivy.uix.settings.Settings`

        '''

    def load_kv(self, filename=None):
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
        # Detect filename automatically if it was not specified.
        if filename:
            filename = resource_find(filename)
        else:
            try:
                default_kv_directory = dirname(getfile(self.__class__))
                if default_kv_directory == '':
                    default_kv_directory = '.'
            except TypeError:
                # if it's a builtin module.. use the current dir.
                default_kv_directory = '.'
            kv_directory = self.options.get('kv_directory',
                                            default_kv_directory)
            clsname = self.__class__.__name__.lower()
            if clsname.endswith('app') and \
                not isfile(join(kv_directory, '%s.kv' % clsname)):
                clsname = clsname[:-3]
            filename = join(kv_directory, '%s.kv' % clsname)

        # Load KV file
        Logger.debug('App: Loading kv <{0}>'.format(filename))
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
        if not resource_find(self.icon):
            return ''
        else:
            return resource_find(self.icon)

    def get_application_config(self, defaultpath='%(appdir)s/%(appname)s.ini'):
        '''.. versionadded:: 1.0.7

        .. versionchanged:: 1.4.0
            Customize the default path for iOS and Android platform. Add
            defaultpath parameter for desktop computer (not applicatable for iOS
            and Android.)

        Return the filename of your application configuration. Depending the
        platform, the application file will be stored at different places:

            - on iOS: <appdir>/Documents/.<appname>.ini
            - on Android: /sdcard/.<appname>.ini
            - otherwise: <appdir>/<appname>.ini

        When you are distributing your application on Desktop, please note than
        if the application is meant to be installed system-wise, then the user
        might not have any write-access to the application directory. You could
        overload this method to change the default behavior, and save the
        configuration file in the user directory by default::

            class TestApp(App):
                def get_application_config(self):
                    return super(TestApp, self).get_application_config(
                        '~/.%(appname)s.ini')

        Some notes:

        - The tilda '~' will be expanded to the user directory.
        - %(appdir)s will be replaced with the application :data:`directory`
        - %(appname)s will be replaced with the application :data:`name`
        '''

        if platform == 'android':
            defaultpath = '/sdcard/.%(appname)s.ini'
        elif platform == 'ios':
            defaultpath = '~/Documents/%(appname)s.ini'
        elif platform == 'win':
            defaultpath = defaultpath.replace('/', sep)
        return expanduser(defaultpath) % {
            'appname': self.name, 'appdir': self.directory}

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
        Logger.debug('App: Loading configuration <{0}>'.format(filename))
        if exists(filename):
            try:
                config.read(filename)
            except:
                Logger.error('App: Corrupted config file, ignored.')
                self.config = config = ConfigParser()
                self.build_config(config)
                pass
        else:
            Logger.debug('App: First configuration, create <{0}>'.format(
                filename))
            config.filename = filename
            config.write()
        return config

    @property
    def directory(self):
        '''.. versionadded:: 1.0.7

        Return the directory where the application live
        '''
        if self._app_directory is None:
            try:
                self._app_directory = dirname(getfile(self.__class__))
                if self._app_directory == '':
                    self._app_directory = '.'
            except TypeError:
                # if it's a builtin module.. use the current dir.
                self._app_directory = '.'
        return self._app_directory

    @property
    def user_data_dir(self):
        '''
        .. versionadded:: 1.7.0

        Returns the path to a directory in the users files system, which the
        application can use to store additional data.

        Different platforms have different conventions for where to save user
        data like preferences, saved games, and settings. This function
        implements those conventions.

        On iOS `~/Documents<app_name>` is returned (which is inside the
        apps sandbox).

        On Android `/sdcard/<app_name>` is returned.

        On Windows `%APPDATA%/<app_name>` is returned.

        On Mac OS X `~/Library/Application Support <app_name>` is returned.

        On Linux, `$XDG_CONFIG_HOME/<app_name>` is returned.
        '''
        data_dir = ""
        if platform == 'ios':
            data_dir = join('~/Documents', self.name)
        elif platform == 'android':
            data_dir = join('/sdcard', self.name)
        elif platform == 'win':
            data_dir = os.path.join(os.environ['APPDATA'], self.name)
        elif platform == 'macosx':
            data_dir = '~/Library/Application Support/{}'.format(self.name)
        else:  # _platform == 'linux' or anything else...:
            data_dir = os.environ.get('XDG_CONFIG_HOME', '~/.config')
            data_dir = join(data_dir, self.name)
        data_dir = expanduser(data_dir)
        if not exists(data_dir):
            os.mkdir(data_dir)
        return data_dir

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
            self.load_kv(filename=self.options.get('kv_file'))
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
        else:
            Logger.critical("Application: No window is created."
                " Terminating application run.")
            return

        self.dispatch('on_start')
        runTouchApp()
        self.stop()

    def stop(self, *largs):
        '''Stop the application.

        If you use this method, the whole application will stop by issuing
        a call to :func:`~kivy.base.stopTouchApp`.
        '''
        self.dispatch('on_stop')
        stopTouchApp()

        # Clear the window children
        for child in self._app_window.children:
            self._app_window.remove_widget(child)

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
        first time. The settings panel will be displayed with the
        :meth:`display_settings` method, which by default adds the
        settings panel to the Window attached to your application. You
        should override that method if you want to display the
        settings panel differently.

        :return: True if the settings have been opened

        '''
        if self._app_settings is None:
            self._app_settings = self.create_settings()
        displayed = self.display_settings(self._app_settings)
        if displayed:
            return True
        return False

    def display_settings(self, settings):
        '''.. versionadded:: 1.8.0

        Display the settings panel. By default, the panel is drawn directly
        on top of the window. You can define other behaviour by overriding
        this method, such as adding it to a ScreenManager or Popup.

        You should return True if the display is successful, otherwise False.

        :param settings: A :class:`~kivy.uix.settings.Settings`
                         instance. You should define how to display it.
        :type config: :class:`~kivy.uix.settings.Settings`

        '''
        win = self._app_window
        if not win:
            raise Exception('No windows are set on the application, you cannot'
                            ' open settings yet.')
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

    def create_settings(self):
        '''Create the settings panel. This method is called only one time per
        application life-time, and the result is cached internally.

        By default, it will build a setting panel according to
        :data:`settings_cls`, call :meth:`build_settings`, add the Kivy panel if
        :data:`use_kivy_settings` is True, and bind to
        on_close/on_config_change.

        If you want to plug your own way of doing settings, without Kivy panel
        or close/config change events, this is the method you want to overload.

        .. versionadded:: 1.8.0
        '''
        s = self.settings_cls()
        self.build_settings(s)
        if self.use_kivy_settings:
            s.add_kivy_panel()
        s.bind(on_close=self.close_settings,
               on_config_change=self._on_config_change)
        return s

    def destroy_settings(self):
        '''.. versionadded:: 1.8.0

        Dereferences the current settings panel, if one
        exists. This means that when :meth:`App.open_settings` is next
        run, a new panel will be created and displayed. It doesn't
        affect any of the contents of the panel, but lets you (for
        instance) refresh the settings panel layout if you have
        changed the settings widget in response to a screen size
        change.

        If you have modified :meth:`~App.open_settings` or
        :meth:`~App.display_settings`, you should be careful to
        correctly detect if the previous settings widget has been
        destroyed.

        '''
        if self._app_settings is not None:
            self._app_settings = None

    def _on_config_change(self, *largs):
        self.on_config_change(*largs[1:])

    def _install_settings_keys(self, window):
        window.bind(on_keyboard=self._on_keyboard_settings)

    def _on_keyboard_settings(self, window, *largs):
        key = largs[0]
        setting_key = 282  # F1

        # android hack, if settings key is pygame K_MENU
        if platform == 'android':
            import pygame
            setting_key = pygame.K_MENU

        if key == setting_key:
            # toggle settings panel
            if not self.open_settings():
                self.close_settings()
            return True
        if key == 27:
            return self.close_settings()
