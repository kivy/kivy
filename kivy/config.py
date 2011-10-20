'''
Configuration object
====================

:class:`Config` object is an instance of a modified Python ConfigParser.
See `ConfigParser documentation
<http://docs.python.org/library/configparser.html>`_ for more information.

Usage of Config object
----------------------

Read a configuration token from a particular section::

    >>> from kivy.config import Config
    >>> Config.getint('kivy', 'show_fps')
    0

Change the configuration and save it::

    >>> Config.set('kivy', 'retain_time', 50)
    >>> Config.write()

Available configuration tokens
------------------------------

.. versionchanged:: 1.0.8

    * `scroll_timeout`, `scroll_distance` and `scroll_friction` have been added
    * `list_friction`, `list_trigger_distance` and `list_friction_bound` have
      been removed.
    * `keyboard_type` and `keyboard_layout` have been removed from widget
    * `keyboard_mode` and `keyboard_layout` have been added to kivy section


:kivy:

    `log_level`: (debug, info, warning, error, critical)
        Set the minimum log level to use
    `log_dir`: string
        Path of log directory
    `log_name`: string
        Format string to use for the filename of log file
    `log_enable`: (0, 1)
        Activate file logging
    `keyboard_mode`: ('', 'system', 'dock', 'multi')
        Keyboard mode to use. If empty, Kivy will decide for you what is the
        best for your current platform. Otherwise, you can set one of 'system'
        (real keyboard), 'dock' (one virtual keyboard docked in a screen side),
        'multi' (one virtual keyboard everytime a widget ask for.)
    `keyboard_layout`: string
        Identifier of the layout to use

:postproc:

    `double_tap_time`: int
        Time allowed for the detection of double tap, in milliseconds
    `double_tap_distance`: float
        Maximum distance allowed for a double tap, normalized inside the range
        0 - 1000
    `retain_time`: int
        Time allowed for a retain touch, in milliseconds
    `retain_distance`: int
        If the touch moves more than is indicated by retain_distance, it will
        not be retained. Argument should be an int between 0 and 1000.
    `jitter_distance`: int
        Maximum distance for jittering detection, normalized inside the range 0
        - 1000
    `jitter_ignore_devices`: string, seperated with comma
        List of devices to ignore from jittering detection
    `ignore`: list of tuples
        List of regions where new touches are ignored.
        This configuration token can be used to resolve hotspot problems
        with DIY hardware. The format of the list must be::

            ignore = [(xmin, ymin, xmax, ymax), ...]

        All the values must be inside 0 - 1 range.

:graphics:

    `maxfps`: int, default to 60
        Maximum FPS allowed.
    `fullscreen`: (0, 1, fake, auto)
        Activate fullscreen. If set to `1`, the fullscreen will use a
        resolution of `width` times `height` pixels.
        If set to `auto`, the fullscreen will use your current display's
        resolution instead. This is most likely what you want.
        If you want to place the window in another display,
        use `fake` and adjust `width`, `height`, `top` and `left`.
    `width`: int
        Width of the :class:`~kivy.core.window.Window`, not used if in `auto
        fullscreen`
    `height`: int
        Height of the :class:`~kivy.core.window.Window`, not used if in `auto
        fullscreen`
    `fbo`: (hardware, software, force-hardware)
        Select the FBO backend to use.
    `show_cursor`: (0, 1)
        Show the cursor on the screen
    `position`: (auto, custom)
        Position of the window on your display. If `auto` is used, you have no
        control about the initial position: `top` and `left` are ignored.
    `top`: int
        Top position of the :class:`~kivy.core.window.Window`
    `left`: int
        Left position of the :class:`~kivy.core.window.Window`
    `window_icon`: string
        Path of the window icon. Use this if you want to replace the default
        pygame icon.
    `rotation`: (0, 90, 180, 270)
        Rotation of the :class:`~kivy.core.window.Window`


:input:

    Input section is particular. You can create new input device with this
    syntax::

        # example of input provider instance
        yourid = providerid,parameters

        # example for tuio provider
        default = tuio,127.0.0.1:3333
        mytable = tuio,192.168.0.1:3334

    .. seealso::

        Check all the providers in kivy.input.providers for the syntax to use
        inside the configuration file.

:widgets:

    `scroll_distance`: int
        Default value of :data:`~kivy.uix.scrollview.Scrollview.scroll_distance`
        property in :class:`~kivy.uix.scrollview.Scrollview` widget.
        Check the widget documentation for more information.

    `scroll_friction`: float
        Default value of :data:`~kivy.uix.scrollview.Scrollview.scroll_friction`
        property in :class:`~kivy.uix.scrollview.Scrollview` widget.
        Check the widget documentation for more information.

    `scroll_timeout`: int
        Default value of :data:`~kivy.uix.scrollview.Scrollview.scroll_timeout`
        property in :class:`~kivy.uix.scrollview.Scrollview` widget.
        Check the widget documentation for more information.

:modules:

    You can activate modules with this syntax::

        modulename =

    Anything after the = will be passed to the module as arguments.
    Check the specific module's documentation for a list of accepted arguments.
'''

__all__ = ('Config', 'ConfigParser')

from shutil import copyfile
from ConfigParser import ConfigParser as PythonConfigParser
from sys import platform
from os import environ, listdir
from os.path import exists, join
from kivy import kivy_home_dir, kivy_config_fn, kivy_data_dir
from kivy.logger import Logger
from kivy.utils import OrderedDict

# Version number of current configuration format
KIVY_CONFIG_VERSION = 5

#: Kivy configuration object
Config = None


class ConfigParser(PythonConfigParser):
    '''Enhanced ConfigParser class, that support the possibility of add default
    sections and default values.

    .. versionadded:: 1.0.7
    '''

    def __init__(self):
        PythonConfigParser.__init__(self)
        self._sections = OrderedDict()
        self.filename = None

    def read(self, filename):
        '''Read only one filename. In contrary of the original ConfigParser of
        Python, this one is able to read only one file at time. The latest
        readed file will be used for the :meth:`write` method.
        '''
        if type(filename) not in (str, unicode):
            raise Exception('Only one filename is accepted (str or unicode)')
        self.filename = filename
        PythonConfigParser.read(self, filename)

    def setdefaults(self, section, keyvalues):
        '''Set lot of key/values in one section at the same time
        '''
        self.adddefaultsection(section)
        for key, value in keyvalues.iteritems():
            self.setdefault(section, key, value)

    def setdefault(self, section, option, value):
        '''Set the default value on a particular option
        '''
        if self.has_option(section, option):
            return
        self.set(section, option, value)

    def getdefault(self, section, option, defaultvalue):
        '''Get an option. If not found, it will return the defaultvalue
        '''
        if not self.has_section(section):
            return defaultvalue
        if not self.has_option(section, option):
            return defaultvalue
        return self.getint(section, option)

    def adddefaultsection(self, section):
        '''Add a section if the section is missing.
        '''
        if self.has_section(section):
            return
        self.add_section(section)

    def write(self):
        '''Write the configuration to the latest opened file with :meth:`read`
        method.

        Return True if the write have succeded.
        '''
        if self.filename is None:
            return False
        try:
            with open(self.filename, 'w') as fd:
                PythonConfigParser.write(self, fd)
        except IOError:
            Logger.exception('Unable to write the config <%s>' % self.filename)
            return False
        return True


if not 'KIVY_DOC_INCLUDE' in environ:

    #
    # Read, analyse configuration file
    # Support upgrade of older config file version
    #

    # Create default configuration
    Config = ConfigParser()

    # Read config file if exist
    if exists(kivy_config_fn) and not 'KIVY_USE_DEFAULTCONFIG' in environ:
        try:
            Config.read(kivy_config_fn)
        except Exception, e:
            Logger.exception('Core: error while reading local'
                             'configuration')

    version = Config.getdefault('kivy', 'config_version', 0)

    # Add defaults section
    Config.adddefaultsection('kivy')
    Config.adddefaultsection('graphics')
    Config.adddefaultsection('input')
    Config.adddefaultsection('postproc')
    Config.adddefaultsection('widgets')
    Config.adddefaultsection('modules')

    # Upgrade default configuration until having the current version
    need_save = False
    if version != KIVY_CONFIG_VERSION:
        Logger.warning('Config: Older configuration version detected'
                       ' (%d instead of %d)' % (
                            version, KIVY_CONFIG_VERSION))
        Logger.warning('Config: Upgrading configuration in progress.')
        need_save = True

    while version < KIVY_CONFIG_VERSION:
        Logger.debug('Config: Upgrading from %d to %d' % (version, version + 1))

        if version == 0:

            # log level
            Config.setdefault('kivy', 'keyboard_repeat_delay', '300')
            Config.setdefault('kivy', 'keyboard_repeat_rate', '30')
            Config.setdefault('kivy', 'log_dir', 'logs')
            Config.setdefault('kivy', 'log_enable', '1')
            Config.setdefault('kivy', 'log_level', 'info')
            Config.setdefault('kivy', 'log_name', 'kivy_%y-%m-%d_%_.txt')
            Config.setdefault('kivy', 'window_icon', \
                join(kivy_home_dir, 'icon', 'kivy32.png'))

            # default graphics parameters
            Config.setdefault('graphics', 'display', '-1')
            Config.setdefault('graphics', 'fullscreen', 'no')
            Config.setdefault('graphics', 'height', '600')
            Config.setdefault('graphics', 'left', '0')
            Config.setdefault('graphics', 'maxfps', '0')
            Config.setdefault('graphics', 'multisamples', '2')
            Config.setdefault('graphics', 'position', 'auto')
            Config.setdefault('graphics', 'rotation', '0')
            Config.setdefault('graphics', 'show_cursor', '1')
            Config.setdefault('graphics', 'top', '0')
            Config.setdefault('graphics', 'vsync', '1')
            Config.setdefault('graphics', 'width', '800')

            # input configuration
            Config.setdefault('input', 'default', 'tuio,0.0.0.0:3333')
            Config.setdefault('input', 'mouse', 'mouse')

            # activate native input provider in configuration
            if platform == 'darwin':
                Config.setdefault('input', 'mactouch', 'mactouch')
            elif platform == 'win32':
                Config.setdefault('input', 'wm_touch', 'wm_touch')
                Config.setdefault('input', 'wm_pen', 'wm_pen')
            elif platform == 'linux2':
                Config.setdefault('input', '%(name)s', 'probesysfs')

            # input postprocessing configuration
            Config.setdefault('postproc', 'double_tap_distance', '20')
            Config.setdefault('postproc', 'double_tap_time', '250')
            Config.setdefault('postproc', 'ignore', '[]')
            Config.setdefault('postproc', 'jitter_distance', '0')
            Config.setdefault('postproc', 'jitter_ignore_devices',
                                   'mouse,mactouch,')
            Config.setdefault('postproc', 'retain_distance', '50')
            Config.setdefault('postproc', 'retain_time', '0')

            # default configuration for keyboard repeatition
            Config.setdefault('widgets', 'keyboard_layout', 'qwerty')
            Config.setdefault('widgets', 'keyboard_type', '')
            Config.setdefault('widgets', 'list_friction', '10')
            Config.setdefault('widgets', 'list_friction_bound', '20')
            Config.setdefault('widgets', 'list_trigger_distance', '5')

        elif version == 1:
            Config.remove_option('graphics', 'vsync')
            Config.set('graphics', 'maxfps', '60')

        elif version == 2:
            logo_dir = join(kivy_data_dir, 'logo')
            dest_dir = join(kivy_home_dir, 'icon')
            for logo in listdir(logo_dir):
                copyfile(join(logo_dir, logo), join(dest_dir, logo))
            logo_size = 32
            if platform == 'darwin':
                logo_size = 512
            Config.set('kivy', 'window_icon', \
                join(kivy_home_dir, 'icon', 'kivy-icon-%d.png' % logo_size))

        elif version == 3:
            # add token for scrollview
            Config.setdefault('widgets', 'scroll_timeout', '250')
            Config.setdefault('widgets', 'scroll_distance', '20')
            Config.setdefault('widgets', 'scroll_friction', '1.')

            # remove old list_* token
            Config.remove_option('widgets', 'list_friction')
            Config.remove_option('widgets', 'list_friction_bound')
            Config.remove_option('widgets', 'list_trigger_distance')

        elif version == 4:
            Config.remove_option('widgets', 'keyboard_type')
            Config.remove_option('widgets', 'keyboard_layout')

            # add keyboard token
            Config.setdefault('kivy', 'keyboard_mode', '')
            Config.setdefault('kivy', 'keyboard_layout', 'qwerty')

        #elif version == 1:
        #   # add here the command for upgrading from configuration 0 to 1
        #
        else:
            # for future.
            break

        # Pass to the next version
        version += 1

    # Said to Config that we've upgrade to latest version.
    Config.set('kivy', 'config_version', KIVY_CONFIG_VERSION)

    # Now, activate log file
    if Config.getint('kivy', 'log_enable'):
        Logger.logfile_activated = True

    # If no configuration exist, write the default one.
    if not exists(kivy_config_fn) or need_save:
        try:
            Config.filename = kivy_config_fn
            Config.write()
        except Exception, e:
            Logger.exception('Core: Error while saving default config file')

