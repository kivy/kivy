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

:kivy:
    `show_fps`: (0, 1)
        Display the FPS on the screen
    `log_level`: (debug, info, warning, error, critical)
        Set the minimum log level to use
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
    `log_dir`: string
        Path of log directory
    `log_name`: string
        Format string to use for the filename of log file
    `log_enable`: (0, 1)
        Activate file logging
    `gl_error_check`: (0, 1)
        Activate GL error checking on a per instruction basis.
        Decreases performance. Only use during development.
    `ignore`: list of tuples
        List of region to ignore new touch. This configuration token can be used
        for resolving hotspot problem on DIY hardware. The format of the list
        must be::

            ignore = [(xmin, ymin, xmax, ymax), ...]

        All the values must be inside 0 - 1 range.

:graphics:

    `fps`: int
        Maximum FPS allowed. if fps is <= 0, and vsync activated, the default
        will be set to 60.
    `fullscreen`: (0, 1, fake, auto)
        Activate fullscreen. If you use `1`, the fullscreen will be changed to fit
        to `width` and `height`. If you use `auto`, the fullscreen will use your
        current display size. If you want to place the window in another
        display, use `fake`, and adjust `width`, `height`, `top` and `left`.
    `width`: int
        Width of the :class:`~kivy.core.window.Window`, not used if in `auto
        fullscreen`
    `height`: int
        Height of the :class:`~kivy.core.window.Window`, not used if in `auto
        fullscreen`
    `vsync`: (0, 1)
        Force Vsync (actually not used by Pygame.)
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

    `list_trigger_distance`: int
        Maximum distance to trigger the on_touch_down/on_touch_up on child for
        every :class:`~kivy.uix.list.List` widget. The value is in pixels.

    `list_friction`: int
        Friction factor. 1 mean no friction.

    `list_friction_bound`: int
        If one side of the list have been hit by the user, you have the
        possibility to reduce the friction to use. Prefer a value below the
        `list_friction` token.

    `keyboard_type`: (real, virtual)
        Type of the keyboard to use. If `real` is used, no virtual keyboard will
        be showed on the screen.

:modules:

    Module section is particular. You can activate new module with this syntax::

        modulename =

    All the arguments after = will be passed to the module. Check each module
    documentation about the syntax of arguments.

'''

__all__ = ('Config', 'KivyConfigParser')

from ConfigParser import ConfigParser
import sys
import os
from kivy.logger import Logger
from kivy import kivy_home_dir, kivy_config_fn

# Version number of current configuration format
KIVY_CONFIG_VERSION = 16

#: Kivy configuration object
Config = None


class KivyConfigParser(ConfigParser):
    '''Enhanced ConfigParser class, that support the possibility of add default
    sections and default values.
    '''

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
        '''Write the configuration to the default kivy file
        '''
        with open(kivy_config_fn, 'w') as fd:
            ConfigParser.write(self, fd)

if not 'KIVY_DOC_INCLUDE' in os.environ:

    #
    # Read, analyse configuration file
    # Support upgrade of older config file version
    #

    # Create default configuration
    Config = KivyConfigParser()

    # Read config file if exist
    if os.path.exists(kivy_config_fn):
        try:
            Config.read(kivy_config_fn)
        except Exception, e:
            Logger.exception('Core: error while reading local'
                             'configuration')

    version = Config.getdefault('kivy', 'config_version', 0)

    # Add defaults section
    Config.adddefaultsection('kivy')
    Config.adddefaultsection('keyboard')
    Config.adddefaultsection('graphics')
    Config.adddefaultsection('input')
    Config.adddefaultsection('dump')
    Config.adddefaultsection('modules')
    Config.adddefaultsection('widgets')

    # Upgrade default configuration until having the current version
    need_save = False
    if version != KIVY_CONFIG_VERSION:
        Logger.warning('Config: Older configuration version detected'
                       '(%d instead of %d)' % (
                            version, KIVY_CONFIG_VERSION))
        Logger.warning('Config: Upgrading configuration in progress.')
        need_save = True

    while version < KIVY_CONFIG_VERSION:
        Logger.debug('Config: Upgrading from %d' % version)

        # Versionning introduced in version 0.4.
        if version == 0:

            Config.setdefault('kivy', 'show_fps', '0')
            Config.setdefault('kivy', 'log_level', 'info')
            Config.setdefault('kivy', 'double_tap_time', '250')
            Config.setdefault('kivy', 'double_tap_distance', '20')
            Config.setdefault('kivy', 'enable_simulator', '1')
            Config.setdefault('kivy', 'ignore', '[]')
            Config.setdefault('keyboard', 'layout', 'qwerty')
            Config.setdefault('graphics', 'fbo', 'hardware')
            Config.setdefault('graphics', 'fullscreen', '0')
            Config.setdefault('graphics', 'width', '640')
            Config.setdefault('graphics', 'height', '480')
            Config.setdefault('graphics', 'vsync', '1')
            Config.setdefault('graphics', 'display', '-1')
            Config.setdefault('graphics', 'line_smooth', '1')
            Config.setdefault('dump', 'enabled', '0')
            Config.setdefault('dump', 'prefix', 'img_')
            Config.setdefault('dump', 'format', 'jpeg')
            Config.setdefault('input', 'default', 'tuio,0.0.0.0:3333')
            Config.setdefault('input', 'mouse', 'mouse')

            # activate native input provider in configuration
            if sys.platform == 'darwin':
                Config.setdefault('input', 'mactouch', 'mactouch')
            elif sys.platform == 'win32':
                Config.setdefault('input', 'wm_touch', 'wm_touch')
                Config.setdefault('input', 'wm_pen', 'wm_pen')

        elif version == 1:
            # add retain postproc configuration
            Config.setdefault('kivy', 'retain_time', '0')
            Config.setdefault('kivy', 'retain_distance', '50')

        elif version == 2:
            # add show cursor
            Config.setdefault('graphics', 'show_cursor', '1')

        elif version == 3:
            # add multisamples
            Config.setdefault('graphics', 'multisamples', '2')

        elif version == 4:
            # remove mouse simulator
            Config.remove_option('kivy', 'enable_simulator')

        elif version == 5:
            # add fixccv
            Config.setdefault('kivy', 'fixccv', '0')

        elif version == 6:
            # add log_file format
            Config.setdefault('kivy', 'log_enable', '1')
            Config.setdefault('kivy', 'log_dir', 'logs')
            Config.setdefault('kivy', 'log_name', 'kivy_%y-%m-%d_%_.txt')

        elif version == 7:
            # add option to turn off pyOpenGL Error Checking
            Config.setdefault('kivy', 'gl_error_check', '1')

        elif version == 8:
            Config.setdefault('kivy', 'jitter_distance', '0')
            Config.setdefault('kivy', 'jitter_ignore_devices',
                                   'mouse,mactouch,')

        elif version == 9:
            Config.setdefault('widgets', 'keyboard_type', 'virtual')

        elif version == 10:
            Config.setdefault('widgets', 'list_friction', '10')
            Config.setdefault('widgets', 'list_friction_bound', '20')
            Config.setdefault('widgets', 'list_trigger_distance', '5')

        elif version == 11:
            Config.setdefault('graphics', 'window_icon', os.path.join(kivy_home_dir, 'icon', 'kivy32.png'))

        elif version == 12:
            # default configuration for keyboard repeatition
            Config.setdefault('keyboard', 'repeat_delay', '300')
            Config.setdefault('keyboard', 'repeat_rate', '30')

        elif version == 13:
            # add possibility to set the position of windows
            Config.setdefault('graphics', 'position', 'auto')
            Config.setdefault('graphics', 'top', '0')
            Config.setdefault('graphics', 'left', '0')

        elif version == 14:
            # ability to change maximum FPS
            Config.setdefault('graphics', 'fps', '0')

        elif version == 15:
            # ability to rotate the window
            Config.setdefault('graphics', 'rotation', '0')

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
    if not os.path.exists(kivy_config_fn) or need_save:
        try:
            Config.write()
        except Exception, e:
            Logger.exception('Core: error while saving default configuration file')
