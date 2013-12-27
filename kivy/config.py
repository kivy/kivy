'''
Configuration object
====================

The :class:`Config` object is an instance of a modified Python ConfigParser.
See the `ConfigParser documentation
<http://docs.python.org/library/configparser.html>`_ for more information.

Kivy has a configuration file which determines the default settings. In
order to change these settings, you can alter this file manually or use
the Config object. Please see the :ref:`Configure Kivy` section for more
information.

Usage of the Config object
--------------------------

To read a configuration token from a particular section::

    >>> from kivy.config import Config
    >>> Config.getint('kivy', 'show_fps')
    0

Change the configuration and save it::

    >>> Config.set('kivy', 'retain_time', '50')
    >>> Config.write()

.. versionchanged:: 1.7.1

    The ConfigParser should work correctly with utf-8 now. The values are
    converted from ascii to unicode only when needed. The method get() returns
    utf-8 strings.

Available configuration tokens
------------------------------

.. |log_levels| replace:: 'debug', 'info', 'warning', 'error' or 'critical'

:kivy:

    `desktop`: int, 0 or 1
        This option controls desktop OS specific features, such as enabling
        drag-able scroll-bar in scroll views, disabling of bubbles in
        TextInput etc. 0 is disabled, 1 is enabled.
    `exit_on_escape`: int, 0 or 1
        Enables exiting kivy when escape is pressed.
        0 is disabled, 1 is enabled.
    `log_level`: string, one of |log_levels|
        Set the minimum log level to use.
    `log_dir`: string
        Path of log directory.
    `log_name`: string
        Format string to use for the filename of log file.
    `log_enable`: int, 0 or 1
        Activate file logging. 0 is disabled, 1 is enabled.
    `keyboard_mode`: string
        Specifies the keyboard mode to use. If can be one of the following:

        * '' - Let Kivy choose the best option for your current platform.
        * 'system' - real keyboard.
        * 'dock' - one virtual keyboard docked to a screen side.
        * 'multi' - one virtual keyboard for every widget request.
        * 'systemanddock' - virtual docked keyboard plus input from real
          keyboard.
        * 'systemandmulti' - analogous.
    `keyboard_layout`: string
        Identifier of the layout to use.
    `window_icon`: string
        Path of the window icon. Use this if you want to replace the default
        pygame icon.

:postproc:

    `double_tap_time`: int
        Time allowed for the detection of double tap, in milliseconds.
    `double_tap_distance`: float
        Maximum distance allowed for a double tap, normalized inside the range
        0 - 1000.
    `triple_tap_time`: int
        Time allowed for the detection of triple tap, in milliseconds.
    `triple_tap_distance`: float
        Maximum distance allowed for a triple tap, normalized inside the range
        0 - 1000.
    `retain_time`: int
        Time allowed for a retain touch, in milliseconds.
    `retain_distance`: int
        If the touch moves more than is indicated by retain_distance, it will
        not be retained. Argument should be an int between 0 and 1000.
    `jitter_distance`: int
        Maximum distance for jitter detection, normalized inside the range 0
        - 1000.
    `jitter_ignore_devices`: string, separated with commas
        List of devices to ignore from jitter detection.
    `ignore`: list of tuples
        List of regions where new touches are ignored.
        This configuration token can be used to resolve hotspot problems
        with DIY hardware. The format of the list must be::

            ignore = [(xmin, ymin, xmax, ymax), ...]

        All the values must be inside the range 0 - 1.

:graphics:

    `maxfps`: int, defaults to 60
        Maximum FPS allowed.
    `fullscreen`: int or string, one of 0, 1, 'fake' or 'auto'
        Activate fullscreen. If set to `1`, a resolution of `width`
        times `height` pixels will be used.
        If set to `auto`, your current display's resolution will be
        used instead. This is most likely what you want.
        If you want to place the window in another display,
        use `fake` and adjust `width`, `height`, `top` and `left`.
    `width`: int
        Width of the :class:`~kivy.core.window.Window`, not used if
        `fullscreen` is set to `auto`.
    `height`: int
        Height of the :class:`~kivy.core.window.Window`, not used if
        `fullscreen` is set to `auto`.
    `fbo`: string, one of 'hardware', 'software' or 'force-hardware'
        Selects the FBO backend to use.
    `show_cursor`: int, one of 0 or 1
        Show the cursor on the screen.
    `position`: string, one of 'auto' or 'custom'
        Position of the window on your display. If `auto` is used, you have no
        control of the initial position: `top` and `left` are ignored.
    `top`: int
        Top position of the :class:`~kivy.core.window.Window`.
    `left`: int
        Left position of the :class:`~kivy.core.window.Window`.
    `rotation`: int, one of 0, 90, 180 or 270
        Rotation of the :class:`~kivy.core.window.Window`.
    `resizable`: int, one of 0 or 1
        If 0, the window will have a fixed size. If 1, the window will be
        resizable.

:input:

    You can create new input devices using this syntax::

        # example of input provider instance
        yourid = providerid,parameters

        # example for tuio provider
        default = tuio,127.0.0.1:3333
        mytable = tuio,192.168.0.1:3334

    .. seealso::

        Check the providers in kivy.input.providers for the syntax to use
        inside the configuration file.

:widgets:

    `scroll_distance`: int
        Default value of the
        :data:`~kivy.uix.scrollview.ScrollView.scroll_distance`
        property used by the :class:`~kivy.uix.scrollview.ScrollView` widget.
        Check the widget documentation for more information.

    `scroll_friction`: float
        Default value of the
        :data:`~kivy.uix.scrollview.ScrollView.scroll_friction`
        property used by the :class:`~kivy.uix.scrollview.ScrollView` widget.
        Check the widget documentation for more information.

    `scroll_timeout`: int
        Default value of the
        :data:`~kivy.uix.scrollview.ScrollView.scroll_timeout`
        property used by the  :class:`~kivy.uix.scrollview.ScrollView` widget.
        Check the widget documentation for more information.

    `scroll_stoptime`: int
        Default value of the
        :data:`~kivy.uix.scrollview.ScrollView.scroll_stoptime`
        property used by the :class:`~kivy.uix.scrollview.ScrollView` widget.
        Check the widget documentation for more information.

        .. deprecated:: 1.7.0
            Please use
            :class:`~kivy.uix.scrollview.ScrollView.effect_cls` instead.

    `scroll_moves`: int
        Default value of the
        :data:`~kivy.uix.scrollview.ScrollView.scroll_moves`
        property used by the :class:`~kivy.uix.scrollview.ScrollView` widget.
        Check the widget documentation for more information.

        .. deprecated:: 1.7.0
            Please use
            :class:`~kivy.uix.scrollview.ScrollView.effect_cls` instead.

:modules:

    You can activate modules with this syntax::

        modulename =

    Anything after the = will be passed to the module as arguments.
    Check the specific module's documentation for a list of accepted
    arguments.

.. versionchanged:: 1.8.0
    `systemanddock` and `systemandmulti` has been added as possible values for
    `keyboard_mode` in the kivy section. `exit_on_escape` has been added
    to the kivy section.

.. versionchanged:: 1.2.0
    `resizable` has been added to graphics section.

.. versionchanged:: 1.1.0
    tuio is not listening by default anymore. Window icons are not copied to
    user directory anymore. You can still set a new window icon by using the
    ``window_icon`` config setting.

.. versionchanged:: 1.0.8
    `scroll_timeout`, `scroll_distance` and `scroll_friction` have been added.
    `list_friction`, `list_trigger_distance` and `list_friction_bound`
    have been removed. `keyboard_type` and `keyboard_layout` have been
    removed from the widget. `keyboard_mode` and `keyboard_layout` have
    been added to the kivy section.
'''

__all__ = ('Config', 'ConfigParser')

try:
    from ConfigParser import ConfigParser as PythonConfigParser
except ImportError:
    from configparser import RawConfigParser as PythonConfigParser
from os import environ
from os.path import exists
from kivy import kivy_config_fn
from kivy.logger import Logger, logger_config_update
from collections import OrderedDict
from kivy.utils import platform
from kivy.compat import PY2, string_types

_is_rpi = exists('/opt/vc/include/bcm_host.h')

# Version number of current configuration format
KIVY_CONFIG_VERSION = 10

#: Kivy configuration object
Config = None


class ConfigParser(PythonConfigParser):
    '''Enhanced ConfigParser class that supports the addition of default
    sections and default values.

    .. versionadded:: 1.0.7
    '''

    def __init__(self):
        PythonConfigParser.__init__(self)
        self._sections = OrderedDict()
        self.filename = None
        self._callbacks = []

    def add_callback(self, callback, section=None, key=None):
        '''Add a callback to be called when a specific section/key changed. If
        you don't specify a section or a key, it will call the callback
        for all section/keys changes.

        Callbacks will receive 3 arguments: the section, key and value.

        .. versionadded:: 1.4.1
        '''
        if section is None and key is not None:
            raise Exception('You cannot specify a key without a section')
        self._callbacks.append((callback, section, key))

    def _do_callbacks(self, section, key, value):
        for callback, csection, ckey in self._callbacks:
            if csection is not None and csection != section:
                continue
            elif ckey is not None and ckey != key:
                continue
            callback(section, key, value)

    def read(self, filename):
        '''Read only one filename. In contrast to the original ConfigParser of
        Python, this one is able to read only one file at a time. The last
        read file will be used for the :meth:`write` method.
        '''
        if not isinstance(filename, string_types):
            raise Exception('Only one filename is accepted ({})'.format(
                string_types.__name__))
        self.filename = filename
        # If we try to open directly the configuration file in utf-8,
        # we correctly get the unicode value by default.
        # But, when we try to save it again, all the values we didn't changed
        # are still unicode, and then the PythonConfigParser internal do
        # a str() conversion -> fail.
        # Instead we currently to the conversion to utf-8 when value are
        # "get()", but we internally store them in ascii.
        #with codecs.open(filename, 'r', encoding='utf-8') as f:
        #    self.readfp(f)
        PythonConfigParser.read(self, filename)

    def set(self, section, option, value):
        '''Functions similarly to PythonConfigParser's set method, except that
        the value is implicitly converted to a string.
        '''
        e_value = value
        if PY2:
            if not isinstance(value, string_types):
                # might be boolean, int, etc.
                e_value = str(value)
            else:
                if isinstance(value, unicode):
                    e_value = value.encode('utf-8')
        ret = PythonConfigParser.set(self, section, option, e_value)
        self._do_callbacks(section, option, value)
        return ret

    def get(self, section, option, **kwargs):
        value = PythonConfigParser.get(self, section, option, **kwargs)
        if PY2:
            if type(value) is str:
                return value.decode('utf-8')
        return value

    def setdefaults(self, section, keyvalues):
        '''Set a lot of keys/values in one section at the same time.
        '''
        self.adddefaultsection(section)
        for key, value in keyvalues.items():
            self.setdefault(section, key, value)

    def setdefault(self, section, option, value):
        '''Set the default value of a particular option.
        '''
        if self.has_option(section, option):
            return
        self.set(section, option, value)

    def getdefault(self, section, option, defaultvalue):
        '''Get an option. If not found, it will return the default value.
        '''
        if not self.has_section(section):
            return defaultvalue
        if not self.has_option(section, option):
            return defaultvalue
        return self.get(section, option)

    def getdefaultint(self, section, option, defaultvalue):
        '''Get an option. If not found, it will return the default value.
        The return value will be always converted as an integer.

        .. versionadded:: 1.6.0
        '''
        return int(self.getdefault(section, option, defaultvalue))

    def adddefaultsection(self, section):
        '''Add a section if the section is missing.
        '''
        if self.has_section(section):
            return
        self.add_section(section)

    def write(self):
        '''Write the configuration to the last file opened using the
         :meth:`read` method.

        Return True if the write finished successfully.
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


if not environ.get('KIVY_DOC_INCLUDE'):

    #
    # Read, analyse configuration file
    # Support upgrade of older config file versions
    #

    # Create default configuration
    Config = ConfigParser()
    Config.add_callback(logger_config_update, 'kivy', 'log_level')

    # Read config file if exist
    if (exists(kivy_config_fn) and
            'KIVY_USE_DEFAULTCONFIG' not in environ and
            'KIVY_NO_CONFIG' not in environ):
        try:
            Config.read(kivy_config_fn)
        except Exception as e:
            Logger.exception('Core: error while reading local'
                             'configuration')

    version = Config.getdefaultint('kivy', 'config_version', 0)

    # Add defaults section
    Config.adddefaultsection('kivy')
    Config.adddefaultsection('graphics')
    Config.adddefaultsection('input')
    Config.adddefaultsection('postproc')
    Config.adddefaultsection('widgets')
    Config.adddefaultsection('modules')

    # Upgrade default configuration until we have the current version
    need_save = False
    if version != KIVY_CONFIG_VERSION and 'KIVY_NO_CONFIG' not in environ:
        Logger.warning('Config: Older configuration version detected'
                       ' ({0} instead of {1})'.format(
                           version, KIVY_CONFIG_VERSION))
        Logger.warning('Config: Upgrading configuration in progress.')
        need_save = True

    while version < KIVY_CONFIG_VERSION:
        Logger.debug('Config: Upgrading from %d to %d' %
                     (version, version + 1))

        if version == 0:

            # log level
            Config.setdefault('kivy', 'keyboard_repeat_delay', '300')
            Config.setdefault('kivy', 'keyboard_repeat_rate', '30')
            Config.setdefault('kivy', 'log_dir', 'logs')
            Config.setdefault('kivy', 'log_enable', '1')
            Config.setdefault('kivy', 'log_level', 'info')
            Config.setdefault('kivy', 'log_name', 'kivy_%y-%m-%d_%_.txt')
            Config.setdefault('kivy', 'window_icon', '')

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
            Config.setdefault('input', 'mouse', 'mouse')

            # activate native input provider in configuration
            # from 1.0.9, don't activate mactouch by default, or app are
            # unusable.
            if platform == 'win':
                Config.setdefault('input', 'wm_touch', 'wm_touch')
                Config.setdefault('input', 'wm_pen', 'wm_pen')
            elif platform == 'linux':
                probesysfs = 'probesysfs'
                if _is_rpi:
                    probesysfs += ',provider=hidinput'
                Config.setdefault('input', '%(name)s', probesysfs)

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
            # was a version to automatically copy windows icon in the user
            # directory, but it's now not used anymore. User can still change
            # the window icon by touching the config.
            pass

        elif version == 3:
            # add token for scrollview
            Config.setdefault('widgets', 'scroll_timeout', '55')
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

        elif version == 5:
            Config.setdefault('graphics', 'resizable', '1')

        elif version == 6:
            # if the timeout is still the default value, change it
            Config.setdefault('widgets', 'scroll_stoptime', '300')
            Config.setdefault('widgets', 'scroll_moves', '5')

        elif version == 7:
            # desktop bool indicating whether to use desktop specific features
            is_desktop = int(platform in ('win', 'macosx', 'linux'))
            Config.setdefault('kivy', 'desktop', is_desktop)
            Config.setdefault('postproc', 'triple_tap_distance', '20')
            Config.setdefault('postproc', 'triple_tap_time', '375')

        elif version == 8:
            if Config.getint('widgets', 'scroll_timeout') == 55:
                Config.set('widgets', 'scroll_timeout', '250')

        elif version == 9:
            Config.setdefault('kivy', 'exit_on_escape', '1')

        #elif version == 1:
        #   # add here the command for upgrading from configuration 0 to 1
        #
        else:
            # for future.
            break

        # Pass to the next version
        version += 1

    # Indicate to the Config that we've upgrade to the latest version.
    Config.set('kivy', 'config_version', KIVY_CONFIG_VERSION)

    # Now, activate log file
    Logger.logfile_activated = bool(Config.getint('kivy', 'log_enable'))

    # If no configuration exist, write the default one.
    if ((not exists(kivy_config_fn) or need_save) and
            'KIVY_NO_CONFIG' not in environ):
        try:
            Config.filename = kivy_config_fn
            Config.write()
        except Exception as e:
            Logger.exception('Core: Error while saving default config file')
