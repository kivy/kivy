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

Applying configurations
-----------------------

Configuration options control the initialization of the :class:`~kivy.app.App`.
In order to avoid situations where the config settings do not work or are not
applied before window creation (like setting an initial window size),
:meth:`Config.set <kivy.config.ConfigParser.set>` should be used before
importing any other Kivy modules. Ideally, this means setting them right at
the start of your main.py script.

Alternatively, you can save these settings permanently using
:meth:`Config.set <ConfigParser.set>` then
:meth:`Config.write <ConfigParser.write>`. In this case, you will need to
restart the app for the changes to take effect. Note that this approach will
effect all Kivy apps system wide.

Please note that no underscores (`_`) are allowed in the section name.

Usage of the Config object
--------------------------

To read a configuration token from a particular section::

    >>> from kivy.config import Config
    >>> Config.getint('kivy', 'show_fps')
    0

Change the configuration and save it::

    >>> Config.set('postproc', 'retain_time', '50')
    >>> Config.write()

For information on configuring your :class:`~kivy.app.App`, please see the
:ref:`Application configuration` section.

.. versionchanged:: 1.7.1
    The ConfigParser should work correctly with utf-8 now. The values are
    converted from ascii to unicode only when needed. The method get() returns
    utf-8 strings.

Changing configuration with environment variables
-------------------------------------------------

Since 1.11.0, it is now possible to change the configuration using
environment variables. They take precedence on the loaded config.ini.
The format is::

    KCFG_<section>_<key> = <value>

For example:

    KCFG_GRAPHICS_FULLSCREEN=auto ...
    KCFG_KIVY_LOG_LEVEL=warning ...

Or in your file before any kivy import:

    import os
    os.environ["KCFG_KIVY_LOG_LEVEL"] = "warning"

If you don't want to map any environment variables, you can disable
the behavior::

    os.environ["KIVY_NO_ENV_CONFIG"] = "1"


.. _configuration-tokens:

Available configuration tokens
------------------------------

.. |log_levels| replace::
    'trace', 'debug', 'info', 'warning', 'error' or 'critical'

:kivy:

    `default_font`: list
        Default fonts used for widgets displaying any text. It defaults to
        ['Roboto', 'data/fonts/Roboto-Regular.ttf',
        'data/fonts/Roboto-Italic.ttf', 'data/fonts/Roboto-Bold.ttf',
        'data/fonts/Roboto-BoldItalic.ttf'].
    `desktop`: int, 0 or 1
        This option controls desktop OS specific features, such as enabling
        drag-able scroll-bar in scroll views, disabling of bubbles in
        TextInput etc. 0 is disabled, 1 is enabled.
    `exit_on_escape`: int, 0 or 1
        Enables exiting kivy when escape is pressed.
        0 is disabled, 1 is enabled.
    `pause_on_minimize`: int, 0 or 1
        If set to `1`, the main loop is paused and the `on_pause` event
        is dispatched when the window is minimized. This option is intended
        for desktop use only. Defaults to `0`.
    `keyboard_layout`: string
        Identifier of the layout to use.
    `keyboard_mode`: string
        Specifies the keyboard mode to use. If can be one of the following:

        * '' - Let Kivy choose the best option for your current platform.
        * 'system' - real keyboard.
        * 'dock' - one virtual keyboard docked to a screen side.
        * 'multi' - one virtual keyboard for every widget request.
        * 'systemanddock' - virtual docked keyboard plus input from real
          keyboard.
        * 'systemandmulti' - analogous.
    `kivy_clock`: one of `default`, `interrupt`, `free_all`, `free_only`
        The clock type to use with kivy. See :mod:`kivy.clock`.
    `log_dir`: string
        Path of log directory.
    `log_enable`: int, 0 or 1
        Activate file logging. 0 is disabled, 1 is enabled.

        .. note::
            Logging output can also be controlled by the environment variables
            ``KIVY_LOG_MODE``, ``KIVY_NO_FILELOG`` and ``KIVY_NO_CONSOLELOG``.
            More information is provided in the :mod:`kivy.logger` module.

    `log_level`: string, one of |log_levels|
        Set the minimum log level to use.
    `log_name`: string
        Format string to use for the filename of log file.

    `log_maxfiles`: int
        Keep log_maxfiles recent logfiles while purging the log directory. Set
        'log_maxfiles' to -1 to disable logfile purging (eg keep all logfiles).

        .. note::
            You end up with 'log_maxfiles + 1' logfiles because the logger
            adds a new one after purging.

    `window_icon`: string
        Path of the window icon. Use this if you want to replace the default
        icon.
    `window_shape`: str (default: '')
        Specifies the default path to an image file that defines the window shape.
        To change the window shape after initialization, use the
        :attr:`~kivy.core.window.WindowBase.shape_image` attribute.

        .. warning::
            This option takes effect only if the `shaped` setting in the `[graphics]`
            configuration section is set to `1`.

        .. warning::
            The image file must meet the requirements outlined in
            :attr:`~kivy.core.window.WindowBase.shape_image`.

:postproc:

    `double_tap_distance`: float
        Maximum distance allowed for a double tap, normalized inside the range
        0 - 1000.
    `double_tap_time`: int
        Time allowed for the detection of double tap, in milliseconds.
    `ignore`: list of tuples
        List of regions where new touches are ignored.
        This configuration token can be used to resolve hotspot problems
        with DIY hardware. The format of the list must be::

            ignore = [(xmin, ymin, xmax, ymax), ...]

        All the values must be inside the range 0 - 1.
    `jitter_distance`: int
        Maximum distance for jitter detection, normalized inside the range 0
        - 1000.
    `jitter_ignore_devices`: string, separated with commas
        List of devices to ignore from jitter detection.
    `retain_distance`: int
        If the touch moves more than is indicated by retain_distance, it will
        not be retained. Argument should be an int between 0 and 1000.
    `retain_time`: int
        Time allowed for a retain touch, in milliseconds.
    `triple_tap_distance`: float
        Maximum distance allowed for a triple tap, normalized inside the range
        0 - 1000.
    `triple_tap_time`: int
        Time allowed for the detection of triple tap, in milliseconds.

:graphics:
    `borderless`: int, one of 0 or 1
        If set to `1`, removes the window border/decoration. Window resizing
        must also be disabled to hide the resizing border.
    `custom_titlebar`: int, one of 0 or 1
        If set to `1`, removes the window border and allows user to set a Widget
        as a titlebar
        see :meth:`~kivy.core.window.WindowBase.set_custom_titlebar`
        for detailed usage
    `custom_titlebar_border`: int, defaults to 5
        sets the how many pixles off the border should be used as the
        rezising frame
    `window_state`: string , one of 'visible', 'hidden', 'maximized'
                    or 'minimized'

        Sets the window state, defaults to 'visible'. This option is available
        only for the SDL3 window provider and it should be used on desktop
        OSes.
    `fbo`: string, one of 'hardware', 'software' or 'force-hardware'
        Selects the FBO backend to use.
    `fullscreen`: int or string, one of 0, 1, 'fake' or 'auto'
        Activate fullscreen. If set to `1`, a resolution of `width`
        times `height` pixels will be used.
        If set to `auto`, your current display's resolution will be
        used instead. This is most likely what you want.
        If you want to place the window in another display,
        use `fake`, or set the `borderless` option from the graphics section,
        then adjust `width`, `height`, `top` and `left`.
    `height`: int
        Height of the :class:`~kivy.core.window.Window`, not used if
        `fullscreen` is set to `auto`.
    `left`: int
        Left position of the :class:`~kivy.core.window.Window`.
    `maxfps`: int, defaults to 60
        Maximum FPS allowed.

        .. warning::
            Setting maxfps to 0 will lead to max CPU usage.

    'multisamples': int, defaults to 2
        Sets the `MultiSample Anti-Aliasing (MSAA)
        <http://en.wikipedia.org/wiki/Multisample_anti-aliasing>`_ level.
        Increasing this value results in smoother graphics but at the cost of
        processing time.

        .. note::
           This feature is limited by device hardware support and will have no
           effect on devices which do not support the level of MSAA requested.

    `position`: string, one of 'auto' or 'custom'
        Position of the window on your display. If `auto` is used, you have no
        control of the initial position: `top` and `left` are ignored.
    `show_cursor`: int, one of 0 or 1
        Set whether or not the cursor is shown on the window.
    `top`: int
        Top position of the :class:`~kivy.core.window.Window`.
    `resizable`: int, one of 0 or 1
        If 0, the window will have a fixed size. If 1, the window will be
        resizable.
    `rotation`: int, one of 0, 90, 180 or 270
        Rotation of the :class:`~kivy.core.window.Window`.
    `width`: int
        Width of the :class:`~kivy.core.window.Window`, not used if
        `fullscreen` is set to `auto`.
    `minimum_width`: int
        Minimum width to restrict the window to. (sdl3 only)
    `minimum_height`: int
        Minimum height to restrict the window to. (sdl3 only)
    `min_state_time`: float, defaults to .035
        Minimum time for widgets to display a given visual state.
        This attrib is currently used by widgets like
        :class:`~kivy.uix.dropdown.DropDown` &
        :class:`~kivy.uix.behaviors.buttonbehavior.ButtonBehavior` to
        make sure they display their current visual state for the given
        time.
    `always_on_top`: int, one of ``0`` or ``1``, defaults to ``0``
        When enabled, the window will be brought to the front and will keep
        the window above the rest. Only works for the sdl3 window provider.
        ``0`` is disabled, ``1`` is enabled.
    `show_taskbar_icon`: int, one of ``0`` or ``1``, defaults to ``1``
        Determines whether the app's icon will be added to the taskbar. Only
        applicable for the SDL3 window provider.
        ``0`` means the icon will not be shown in the taskbar and ``1`` means
        it will.
    `allow_screensaver`: int, one of 0 or 1, defaults to 1
        Allow the device to show a screen saver, or to go to sleep
        on mobile devices. Only works for the sdl3 window provider.
    `vsync`: `none`, empty value, or integers
        Whether vsync is enabled, currently only used with sdl3 window.
        Possible values are `none` or empty value -- leaves it unchanged,
        ``0`` -- disables vsync, ``1`` or larger -- sets vsync interval,
        ``-1`` sets adaptive vsync. It falls back to 1 if setting to ``2+``
        or ``-1`` failed. See ``SDL_GL_SetSwapInterval``.
    `verify_gl_main_thread`: int, 1 or 0, defaults to 1
        Whether to check if code that changes any gl instructions is
        running outside the main thread and then raise an error.
    `shaped`: int, 0 or 1 (default: 0)
        If set to `1`, the system will attempt to initialize the window as shapable.
        However, whether the window is actually shapable depends on the
        platform and implementation. To check if shaping is supported, inspect
        the window object's `shapable` property.

        .. warning::
            For shaping to work reliably across platforms, set
            `Window.clearcolor` to `(0, 0, 0, 0)`.
    `alpha_size: int (default: 0 on the Raspberry Pi and 8 on all other platforms)
        Specifies the minimum number of bits for the alpha channel of the color buffer.
        Set this to 0, so SDL3 works without X11.
        Only applicable for the SDL3 window provider.

:input:

    You can create new input devices using this syntax::

        # example of input provider instance
        yourid = providerid,parameters

        # example for tuio provider
        default = tuio,127.0.0.1:3333
        mytable = tuio,192.168.0.1:3334

    .. seealso::

        Check the providers in :mod:`kivy.input.providers` for the syntax to
        use inside the configuration file.

:widgets:

    `scroll_distance`: int
        Default value of the
        :attr:`~kivy.uix.scrollview.ScrollView.scroll_distance`
        property used by the :class:`~kivy.uix.scrollview.ScrollView` widget.
        Check the widget documentation for more information.

    `scroll_friction`: float
        Default value of the
        :attr:`~kivy.uix.scrollview.ScrollView.scroll_friction`
        property used by the :class:`~kivy.uix.scrollview.ScrollView` widget.
        Check the widget documentation for more information.

        .. deprecated:: 1.7.0
            Please use
            :class:`~kivy.uix.scrollview.ScrollView.effect_cls` instead.

    `scroll_timeout`: int
        Default value of the
        :attr:`~kivy.uix.scrollview.ScrollView.scroll_timeout`
        property used by the  :class:`~kivy.uix.scrollview.ScrollView` widget.
        Check the widget documentation for more information.

    `scroll_stoptime`: int
        Default value of the
        :attr:`~kivy.uix.scrollview.ScrollView.scroll_stoptime`
        property used by the :class:`~kivy.uix.scrollview.ScrollView` widget.
        Check the widget documentation for more information.

        .. deprecated:: 1.7.0
            Please use
            :class:`~kivy.uix.scrollview.ScrollView.effect_cls` instead.

    `scroll_moves`: int
        Default value of the
        :attr:`~kivy.uix.scrollview.ScrollView.scroll_moves`
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

.. versionadded:: 3.0.0
    `alpha_size` have been added to the `graphics` section.

.. versionadded:: 2.2.0
    `always_on_top` have been added to the `graphics` section.
    `show_taskbar_icon` have been added to the `graphics` section.

.. versionchanged:: 2.2.0
    `implementation` has been added to the network section.

.. versionchanged:: 2.1.0
    `vsync` has been added to the graphics section.
    `verify_gl_main_thread` has been added to the graphics section.

.. versionchanged:: 1.10.0
    `min_state_time`  and `allow_screensaver` have been added
    to the `graphics` section.
    `kivy_clock` has been added to the kivy section.
    `default_font` has beed added to the kivy section.
    `useragent` has been added to the network section.

.. versionchanged:: 1.9.0
    `borderless` and `window_state` have been added to the graphics section.
    The `fake` setting of the `fullscreen` option has been deprecated,
    use the `borderless` option instead.
    `pause_on_minimize` has been added to the kivy section.

.. versionchanged:: 1.8.0
    `systemanddock` and `systemandmulti` has been added as possible values for
    `keyboard_mode` in the kivy section. `exit_on_escape` has been added
    to the kivy section.

.. versionchanged:: 1.2.0
    `resizable` has been added to graphics section.

.. versionchanged:: 1.1.0
    tuio no longer listens by default. Window icons are not copied to
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

from configparser import RawConfigParser as PythonConfigParser
from collections import OrderedDict
from os import environ
from os.path import exists
from weakref import ref

from kivy.logger import Logger, logger_config_update
from kivy.utils import pi_version, platform

_is_rpi = exists('/opt/vc/include/bcm_host.h')

# Version number of current configuration format
KIVY_CONFIG_VERSION = 29

Config = None
'''The default Kivy configuration object. This is a :class:`ConfigParser`
instance with the :attr:`~kivy.config.ConfigParser.name` set to 'kivy'.

.. code-block:: python

    Config = ConfigParser(name='kivy')

'''


class ConfigParser(PythonConfigParser, object):
    '''Enhanced ConfigParser class that supports the addition of default
    sections and default values.

    By default, the kivy ConfigParser instance, :attr:`~kivy.config.Config`,
    is named `'kivy'` and the ConfigParser instance used by the
    :meth:`App.build_settings <~kivy.app.App.build_settings>` method is named
    `'app'`.

    :Parameters:
        `name`: string
            The name of the instance. See :attr:`name`. Defaults to `''`.

    .. versionchanged:: 1.9.0
        Each ConfigParser can now be :attr:`named <name>`. You can get the
        ConfigParser associated with a name using :meth:`get_configparser`.
        In addition, you can now control the config values with
        :class:`~kivy.properties.ConfigParserProperty`.

    .. versionadded:: 1.0.7
    '''

    def __init__(self, name='', **kwargs):
        PythonConfigParser.__init__(self, **kwargs)
        self._sections = OrderedDict()
        self.filename = None
        self._callbacks = []
        self.name = name

    def add_callback(self, callback, section=None, key=None):
        '''Add a callback to be called when a specific section or key has
        changed. If you don't specify a section or key, it will call the
        callback for all section/key changes.

        Callbacks will receive 3 arguments: the section, key and value.

        .. versionadded:: 1.4.1
        '''
        if section is None and key is not None:
            raise Exception('You cannot specify a key without a section')
        self._callbacks.append((callback, section, key))

    def remove_callback(self, callback, section=None, key=None):
        '''Removes a callback added with :meth:`add_callback`.
        :meth:`remove_callback` must be called with the same parameters as
        :meth:`add_callback`.

        Raises a `ValueError` if not found.

        .. versionadded:: 1.9.0
        '''
        self._callbacks.remove((callback, section, key))

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

        .. versionchanged:: 1.9.0
            :meth:`read` now calls the callbacks if read changed any values.

        '''
        if not isinstance(filename, str):
            raise Exception('Only one filename is accepted (str)')
        self.filename = filename
        # If we try to open directly the configuration file in utf-8,
        # we correctly get the unicode value by default.
        # But, when we try to save it again, all the values we didn't changed
        # are still unicode, and then the PythonConfigParser internal do
        # a str() conversion -> fail.
        # Instead we currently to the conversion to utf-8 when value are
        # "get()", but we internally store them in ascii.
        # with codecs.open(filename, 'r', encoding='utf-8') as f:
        #    self.readfp(f)
        old_vals = {sect: {k: v for k, v in self.items(sect)} for sect in
                    self.sections()}
        PythonConfigParser.read(self, filename, encoding="utf-8-sig")

        # when reading new file, sections/keys are only increased, not removed
        f = self._do_callbacks
        for section in self.sections():
            if section not in old_vals:  # new section
                for k, v in self.items(section):
                    f(section, k, v)
                continue

            old_keys = old_vals[section]
            for k, v in self.items(section):  # just update new/changed keys
                if k not in old_keys or v != old_keys[k]:
                    f(section, k, v)

    def set(self, section, option, value):
        '''Functions similarly to PythonConfigParser's set method, except that
        the value is implicitly converted to a string.
        '''
        e_value = value
        if not isinstance(value, str):
            # might be boolean, int, etc.
            e_value = str(value)
        ret = PythonConfigParser.set(self, section, option, e_value)
        self._do_callbacks(section, option, value)
        return ret

    def setall(self, section, keyvalues):
        '''Sets multiple key-value pairs in a section. keyvalues should be a
        dictionary containing the key-value pairs to be set.
        '''
        for key, value in keyvalues.items():
            self.set(section, key, value)

    def get(self, section, option, **kwargs):
        value = PythonConfigParser.get(self, section, option, **kwargs)
        return value

    def setdefaults(self, section, keyvalues):
        '''Set multiple key-value defaults in a section. keyvalues should be
        a dictionary containing the new key-value defaults.
        '''
        self.adddefaultsection(section)
        for key, value in keyvalues.items():
            self.setdefault(section, key, value)

    def setdefault(self, section, option, value):
        '''Set the default value for an option in the specified section.
        '''
        if self.has_option(section, option):
            return
        self.set(section, option, value)

    def getdefault(self, section, option, defaultvalue):
        '''Get the value of an option in the specified section. If not found,
        it will return the default value.
        '''
        if not self.has_section(section):
            return defaultvalue
        if not self.has_option(section, option):
            return defaultvalue
        return self.get(section, option)

    def getdefaultint(self, section, option, defaultvalue):
        '''Get the value of an option in the specified section. If not found,
        it will return the default value. The value will always be
        returned as an integer.

        .. versionadded:: 1.6.0
        '''
        return int(self.getdefault(section, option, defaultvalue))

    def adddefaultsection(self, section):
        '''Add a section if the section is missing.
        '''
        assert "_" not in section
        if self.has_section(section):
            return
        self.add_section(section)

    def write(self):
        '''Write the configuration to the last file opened using the
        :meth:`read` method.

        Return True if the write finished successfully, False otherwise.
        '''
        if self.filename is None:
            return False
        try:
            with open(self.filename, 'w', encoding="utf-8") as fd:
                PythonConfigParser.write(self, fd)
        except IOError:
            Logger.exception('Unable to write the config <%s>' % self.filename)
            return False
        return True

    def update_config(self, filename, overwrite=False):
        '''Upgrade the configuration based on a new default config file.
        Overwrite any existing values if overwrite is True.
        '''
        pcp = PythonConfigParser()
        pcp.read(filename)
        confset = self.setall if overwrite else self.setdefaults
        for section in pcp.sections():
            confset(section, dict(pcp.items(section)))
        self.write()

    @staticmethod
    def _register_named_property(name, widget_ref, *largs):
        ''' Called by the ConfigParserProperty to register a property which
        was created with a config name instead of a config object.

        When a ConfigParser with this name is later created, the properties
        are then notified that this parser now exists so they can use it.
        If the parser already exists, the property is notified here. See
        :meth:`~kivy.properties.ConfigParserProperty.set_config`.

        :Parameters:
            `name`: a non-empty string
                The name of the ConfigParser that is associated with the
                property. See :attr:`name`.
            `widget_ref`: 2-tuple.
                The first element is a reference to the widget containing the
                property, the second element is the name of the property. E.g.:

                    class House(Widget):
                        address = ConfigParserProperty('', 'info', 'street',
                            'directory')

                Then, the first element is a ref to a House instance, and the
                second is `'address'`.
        '''
        configs = ConfigParser._named_configs
        try:
            config, props = configs[name]
        except KeyError:
            configs[name] = (None, [widget_ref])
            return

        props.append(widget_ref)
        if config:
            config = config()
        widget = widget_ref[0]()

        if config and widget:  # associate this config with property
            widget.property(widget_ref[1]).set_config(config)

    @staticmethod
    def get_configparser(name):
        '''Returns the :class:`ConfigParser` instance whose name is `name`, or
        None if not found.

        :Parameters:
            `name`: string
                The name of the :class:`ConfigParser` instance to return.
        '''
        try:
            config = ConfigParser._named_configs[name][0]
            if config is not None:
                config = config()
                if config is not None:
                    return config
            del ConfigParser._named_configs[name]
        except KeyError:
            return None

    # keys are configparser names, values are 2-tuple of (ref(configparser),
    # widget_ref), where widget_ref is same as in _register_named_property
    _named_configs = {}
    _name = ''

    @property
    def name(self):
        ''' The name associated with this ConfigParser instance, if not `''`.
        Defaults to `''`. It can be safely changed dynamically or set to `''`.

        When a ConfigParser is given a name, that config object can be
        retrieved using :meth:`get_configparser`. In addition, that config
        instance can also be used with a
        :class:`~kivy.properties.ConfigParserProperty` instance that set its
        `config` value to this name.

        Setting more than one ConfigParser with the same name will raise a
        `ValueError`.
        '''
        return self._name

    @name.setter
    def name(self, value):
        old_name = self._name
        if value is old_name:
            return
        self._name = value
        configs = ConfigParser._named_configs

        if old_name:  # disconnect this parser from previously connected props
            _, props = configs.get(old_name, (None, []))
            for widget, prop in props:
                widget = widget()
                if widget:
                    widget.property(prop).set_config(None)
            configs[old_name] = (None, props)

        if not value:
            return

        # if given new name, connect it with property that used this name
        try:
            config, props = configs[value]
        except KeyError:
            configs[value] = (ref(self), [])
            return

        if config is not None and config() is not None:
            raise ValueError('A parser named {} already exists'.format(value))
        for widget, prop in props:
            widget = widget()
            if widget:
                widget.property(prop).set_config(self)
        configs[value] = (ref(self), props)


class ConfigProxy:
    '''Lazy proxy for Config that defers initialization until App.__init__().

    This proxy enforces strict mode - any attempt to read config values before
    initialization raises a RuntimeError. This ensures that all config access
    happens after the config file is loaded from the app-specific directory.

    Use Config.on_config_ready(callback) to register callbacks that will be
    executed after initialization.

    .. versionadded:: 3.0.0
    '''

    def __init__(self):
        self._initialized = False
        self._real_config = None
        # List of ('set'/'remove_section'/'add_section', args)
        self._pending_operations = []
        self._pending_callbacks = []  # [(callback, section, key), ...]
        self._ready_callbacks = []  # [callback, ...]

    def _initialize(self, config_path):
        '''Initialize the real Config object.

        This is called by App._init_config() after setting the correct config path.
        It creates the real ConfigParser, applies defaults, loads the config file,
        and fires all registered callbacks.

        :Parameters:
            `config_path`: str
                Full path to the config.ini file
        '''
        if self._initialized:
            return

        # Create real ConfigParser
        self._real_config = ConfigParser(name='kivy')

        # Add default sections
        self._real_config.adddefaultsection('kivy')
        self._real_config.adddefaultsection('graphics')
        self._real_config.adddefaultsection('input')
        self._real_config.adddefaultsection('postproc')
        self._real_config.adddefaultsection('widgets')
        self._real_config.adddefaultsection('modules')
        self._real_config.adddefaultsection('network')

        # Apply all default config values
        _apply_default_config(self._real_config)

        # Apply KCFG environment variables
        _apply_env_config(self._real_config)

        # Apply pending callbacks first (before file load)
        for callback, section, key in self._pending_callbacks:
            self._real_config.add_callback(callback, section, key)

        # Load config file (reads, upgrades, writes if needed)
        _load_config_file(self._real_config, config_path)

        # Apply pending operations in order (so they take precedence over file)
        for operation, args in self._pending_operations:
            if operation == 'set':
                section, option, value = args
                self._real_config.set(section, option, value)
            elif operation == 'remove_section':
                section = args
                if self._real_config.has_section(section):
                    self._real_config.remove_section(section)
            elif operation == 'add_section':
                section = args
                if not self._real_config.has_section(section):
                    self._real_config.add_section(section)

        self._initialized = True

        # Trigger pending callbacks with current values (so they initialize properly)
        # This is important for callbacks like logger_config_update that need to act
        # on the initial config values, not just future changes
        for callback, section, key in self._pending_callbacks:
            if section is not None and key is not None:
                # Specific section/key callback - trigger with current value
                if self._real_config.has_option(section, key):
                    value = self._real_config.get(section, key)
                    callback(section, key, value)
            elif section is not None:
                # Section-wide callback - trigger for all keys in section
                if self._real_config.has_section(section):
                    for option in self._real_config.options(section):
                        value = self._real_config.get(section, option)
                        callback(section, option, value)
            else:
                # Global callback - trigger for all sections/keys
                for section_name in self._real_config.sections():
                    for option in self._real_config.options(section_name):
                        value = self._real_config.get(section_name, option)
                        callback(section_name, option, value)

        # Fire all ready callbacks
        for callback in self._ready_callbacks:
            callback()
        self._ready_callbacks.clear()

    def on_config_ready(self, callback):
        '''Register a callback to be called after Config is initialized.

        If Config is already initialized, the callback is called immediately.
        Otherwise, it's stored and will be called after initialization.

        This is useful for modules that need to read Config values at import time.

        :Parameters:
            `callback`: callable
                Function to call after Config is ready. Takes no arguments.

        Example::

            def _init_from_config():
                global _scroll_distance
                from kivy.config import Config
                _scroll_distance = Config.getint('widgets', 'scroll_distance')

            from kivy.config import Config
            Config.on_config_ready(_init_from_config)

        .. versionadded:: 3.0.0
        '''
        if self._initialized:
            callback()
        else:
            self._ready_callbacks.append(callback)

    # Proxy all ConfigParser methods with strict checking

    def set(self, section, option, value):
        '''Set a configuration value.

        If Config is not yet initialized, the value is stored and will be
        applied after initialization (taking precedence over file values).
        '''
        if not self._initialized:
            self._pending_operations.append(('set', (section, option, value)))
        else:
            self._real_config.set(section, option, value)

    def get(self, section, option, **kwargs):
        '''Get a configuration value.

        Raises RuntimeError if called before initialization.
        '''
        if not self._initialized:
            raise RuntimeError(
                f"Config.get('{section}', '{option}') called before "
                "Config initialization. Config is initialized in App.__init__(). "
                "Use Config.on_config_ready(callback) to defer access until "
                "after initialization."
            )
        return self._real_config.get(section, option, **kwargs)

    def getint(self, section, option):
        '''Get a configuration value as an integer.

        Raises RuntimeError if called before initialization.
        '''
        if not self._initialized:
            raise RuntimeError(
                f"Config.getint('{section}', '{option}') called before "
                "Config initialization. Use Config.on_config_ready(callback) "
                "to defer access."
            )
        return self._real_config.getint(section, option)

    def getfloat(self, section, option):
        '''Get a configuration value as a float.

        Raises RuntimeError if called before initialization.
        '''
        if not self._initialized:
            raise RuntimeError(
                f"Config.getfloat('{section}', '{option}') called before "
                "Config initialization. Use Config.on_config_ready(callback) "
                "to defer access."
            )
        return self._real_config.getfloat(section, option)

    def getboolean(self, section, option):
        '''Get a configuration value as a boolean.

        Raises RuntimeError if called before initialization.
        '''
        if not self._initialized:
            raise RuntimeError(
                f"Config.getboolean('{section}', '{option}') called before "
                "Config initialization. Use Config.on_config_ready(callback) "
                "to defer access."
            )
        return self._real_config.getboolean(section, option)

    def add_callback(self, callback, section=None, key=None):
        '''Add a callback. Stored until initialization if not yet initialized.'''
        if not self._initialized:
            self._pending_callbacks.append((callback, section, key))
        else:
            self._real_config.add_callback(callback, section, key)

    def remove_callback(self, callback, section=None, key=None):
        '''Remove a callback.'''
        if not self._initialized:
            self._pending_callbacks.remove((callback, section, key))
        else:
            self._real_config.remove_callback(callback, section, key)

    def read(self, filename):
        '''Read a config file. Only works after initialization.'''
        if not self._initialized:
            raise RuntimeError(
                'Cannot read config file before initialization. '
                'Config.read() is called automatically during initialization.'
            )
        return self._real_config.read(filename)

    def write(self):
        '''Write the config file. Only works after initialization.'''
        if not self._initialized:
            raise RuntimeError('Cannot write config file before initialization')
        return self._real_config.write()

    def has_section(self, section):
        '''Check if a section exists.'''
        if not self._initialized:
            # Before init, all standard sections exist
            return section in ('kivy', 'graphics', 'input', 'postproc',
                             'widgets', 'modules', 'network')
        return self._real_config.has_section(section)

    def has_option(self, section, option):
        '''Check if an option exists in a section.'''
        if not self._initialized:
            # Check pending operations
            for operation, args in self._pending_operations:
                if operation == 'set':
                    s, o, v = args
                    if s == section and o == option:
                        return True
            return False
        return self._real_config.has_option(section, option)

    def add_section(self, section):
        '''Add a section.'''
        if not self._initialized:
            self._pending_operations.append(('add_section', section))
        else:
            self._real_config.add_section(section)

    def remove_section(self, section):
        '''Remove a section.'''
        if not self._initialized:
            self._pending_operations.append(('remove_section', section))
        else:
            self._real_config.remove_section(section)

    def remove_option(self, section, option):
        '''Remove an option from a section.'''
        if not self._initialized:
            pass  # Can't remove before initialization
        else:
            self._real_config.remove_option(section, option)

    def setdefault(self, section, option, value):
        '''Set default value for an option.'''
        if not self._initialized:
            # Check if already in pending operations
            for operation, args in self._pending_operations:
                if operation == 'set':
                    s, o, v = args
                    if s == section and o == option:
                        return  # Already set
            self._pending_operations.append(('set', (section, option, value)))
        else:
            self._real_config.setdefault(section, option, value)

    def setdefaults(self, section, keyvalues):
        '''Set multiple default values.'''
        for key, value in keyvalues.items():
            self.setdefault(section, key, value)

    def setall(self, section, keyvalues):
        '''Set multiple values.'''
        for key, value in keyvalues.items():
            self.set(section, key, value)

    def sections(self):
        '''Return list of sections.'''
        if not self._initialized:
            return [
                'kivy', 'graphics', 'input', 'postproc',
                'widgets', 'modules', 'network'
            ]
        return self._real_config.sections()

    def items(self, section):
        '''Return items in a section.'''
        if not self._initialized:
            raise RuntimeError(
                f"Config.items('{section}') called before initialization. "
                "Use Config.on_config_ready(callback) to defer access."
            )
        return self._real_config.items(section)

    def getdefault(self, section, option, defaultvalue):
        '''Get value with a default.'''
        if not self._initialized:
            # Check pending operations (reversed to get most recent set)
            for operation, args in reversed(self._pending_operations):
                if operation == 'set':
                    s, o, v = args
                    if s == section and o == option:
                        return v
            return defaultvalue
        return self._real_config.getdefault(section, option, defaultvalue)

    def getdefaultint(self, section, option, defaultvalue):
        '''Get integer value with a default.'''
        if not self._initialized:
            # Check pending operations (reversed to get most recent set)
            for operation, args in reversed(self._pending_operations):
                if operation == 'set':
                    s, o, v = args
                    if s == section and o == option:
                        return int(v)
            return defaultvalue
        return self._real_config.getdefaultint(section, option, defaultvalue)

    def update_config(self, filename, overwrite=False):
        '''Update config from another file.'''
        if not self._initialized:
            raise RuntimeError('Cannot update config before initialization')
        return self._real_config.update_config(filename, overwrite)

    def adddefaultsection(self, section):
        '''Add a default section.'''
        if not self._initialized:
            pass  # Sections added during initialization
        else:
            self._real_config.adddefaultsection(section)

    @property
    def filename(self):
        '''Get config filename.'''
        if not self._initialized:
            return None
        return self._real_config.filename

    @filename.setter
    def filename(self, value):
        '''Set config filename.'''
        if self._initialized:
            self._real_config.filename = value


def _apply_default_config(config):
    '''Apply all default configuration values to a ConfigParser instance.

    This sets all the default values for the latest config version.

    :Parameters:
        `config`: ConfigParser instance
            The config object to apply defaults to

    .. versionadded:: 3.0.0
    '''
    # Apply all defaults for the latest version

    # kivy section
    config.setdefault('kivy', 'keyboard_repeat_delay', '300')
    config.setdefault('kivy', 'keyboard_repeat_rate', '30')
    config.setdefault('kivy', 'log_dir', 'logs')
    config.setdefault('kivy', 'log_enable', '1')
    config.setdefault('kivy', 'log_level', 'info')
    config.setdefault('kivy', 'log_name', 'kivy_%y-%m-%d_%_.txt')
    config.setdefault('kivy', 'window_icon', '')
    config.setdefault('kivy', 'keyboard_mode', '')
    config.setdefault('kivy', 'keyboard_layout', 'qwerty')
    is_desktop = int(platform in ('win', 'macosx', 'linux'))
    config.setdefault('kivy', 'desktop', is_desktop)
    config.setdefault('kivy', 'exit_on_escape', '1')
    config.setdefault('kivy', 'pause_on_minimize', '0')
    config.setdefault('kivy', 'kivy_clock', 'default')
    config.setdefault('kivy', 'default_font', [
        'Roboto',
        'data/fonts/Roboto-Regular.ttf',
        'data/fonts/Roboto-Italic.ttf',
        'data/fonts/Roboto-Bold.ttf',
        'data/fonts/Roboto-BoldItalic.ttf'])
    config.setdefault('kivy', 'log_maxfiles', '100')
    config.setdefault('kivy', 'window_shape', '')
    config.setdefault('kivy', 'config_version', KIVY_CONFIG_VERSION)

    # graphics section
    config.setdefault('graphics', 'display', '-1')
    config.setdefault('graphics', 'fullscreen', '0')
    config.setdefault('graphics', 'height', '600')
    config.setdefault('graphics', 'left', '0')
    config.setdefault('graphics', 'maxfps', '60')
    config.setdefault('graphics', 'multisamples', '2')
    config.setdefault('graphics', 'position', 'auto')
    config.setdefault('graphics', 'rotation', '0')
    config.setdefault('graphics', 'show_cursor', '1')
    config.setdefault('graphics', 'top', '0')
    config.setdefault('graphics', 'width', '800')
    config.setdefault('graphics', 'resizable', '1')
    config.setdefault('graphics', 'borderless', '0')
    config.setdefault('graphics', 'window_state', 'visible')
    config.setdefault('graphics', 'minimum_width', '0')
    config.setdefault('graphics', 'minimum_height', '0')
    config.setdefault('graphics', 'min_state_time', '.035')
    config.setdefault('graphics', 'allow_screensaver', '1')
    config.setdefault('graphics', 'shaped', '0')
    config.setdefault('graphics', 'vsync', '')
    config.setdefault('graphics', 'verify_gl_main_thread', '1')
    config.setdefault('graphics', 'custom_titlebar', '0')
    config.setdefault('graphics', 'custom_titlebar_border', '5')
    config.setdefault('graphics', 'always_on_top', '0')
    config.setdefault('graphics', 'show_taskbar_icon', '1')
    config.setdefault('graphics', 'alpha_size', '8' if pi_version is None else '0')

    # input section
    config.setdefault('input', 'mouse', 'mouse')
    if platform == 'win':
        config.setdefault('input', 'wm_touch', 'wm_touch')
        config.setdefault('input', 'wm_pen', 'wm_pen')
    elif platform == 'linux':
        probesysfs = 'probesysfs'
        if _is_rpi:
            probesysfs += ',provider=hidinput'
        config.setdefault('input', '%(name)s', probesysfs)

    # postproc section
    config.setdefault('postproc', 'double_tap_distance', '20')
    config.setdefault('postproc', 'double_tap_time', '250')
    config.setdefault('postproc', 'ignore', '[]')
    config.setdefault('postproc', 'jitter_distance', '0')
    config.setdefault('postproc', 'jitter_ignore_devices', 'mouse,mactouch,')
    config.setdefault('postproc', 'retain_distance', '50')
    config.setdefault('postproc', 'retain_time', '0')
    config.setdefault('postproc', 'triple_tap_distance', '20')
    config.setdefault('postproc', 'triple_tap_time', '375')

    # widgets section
    config.setdefault('widgets', 'keyboard_layout', 'qwerty')
    config.setdefault('widgets', 'scroll_timeout', '250')
    config.setdefault('widgets', 'scroll_distance', '20')
    config.setdefault('widgets', 'scroll_friction', '1.')
    config.setdefault('widgets', 'scroll_stoptime', '300')
    config.setdefault('widgets', 'scroll_moves', '5')

    # network section
    config.setdefault('network', 'useragent', 'curl')
    config.setdefault('network', 'implementation', 'default')


def _apply_env_config(config):
    '''Apply KCFG_* environment variables to a ConfigParser instance.

    This reads all KCFG_section_key environment variables and applies them
    to the config. Environment variables take precedence over file values.

    :Parameters:
        `config`: ConfigParser instance
            The config object to apply environment variables to

    .. versionadded:: 3.0.0
    '''
    from kivy.logger import Logger

    if environ.get('KIVY_NO_ENV_CONFIG', '0') == '1':
        return

    for key, value in environ.items():
        if not key.startswith("KCFG_"):
            continue
        try:
            _, section, name = key.split("_", 2)
        except ValueError:
            Logger.warning((
                "Config: Environ `{}` invalid format, "
                "must be KCFG_section_name").format(key))
            continue

        # extract and check section
        section = section.lower()
        if not config.has_section(section):
            Logger.warning(
                "Config: Environ `{}`: unknown section `{}`".format(
                    key, section))
            continue

        # extract and check the option name
        name = name.lower()
        sections_to_check = {
            "kivy", "graphics", "widgets", "postproc", "network"}
        if (section in sections_to_check and
                not config.has_option(section, name)):
            Logger.warning((
                "Config: Environ `{}` unknown `{}` "
                "option in `{}` section.").format(
                    key, name, section))

        config.set(section, name, value)


def _load_config_file(config, config_filename):
    '''Load and upgrade the Kivy configuration file.

    This function should be called by ConfigProxy._initialize() after
    setting the correct config file path. It handles reading the config file,
    upgrading to the latest version if needed, and writing it back if necessary.

    :Parameters:
        `config`: ConfigParser instance
            The config object to load the file into
        `config_filename`: str
            Full path to the config.ini file to load

    .. versionadded:: 3.0.0
    '''
    from kivy.logger import Logger

    # Read config file if exist
    if (exists(config_filename) and
            'KIVY_USE_DEFAULTCONFIG' not in environ and
            'KIVY_NO_CONFIG' not in environ):
        try:
            config.read(config_filename)
        except Exception:
            Logger.exception('Core: error while reading local configuration')

    version = config.getdefaultint('kivy', 'config_version', 0)

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

        # Version upgrades happen here
        if version == 0:
            pass  # Defaults already applied in _apply_default_config
        elif version == 1:
            config.set('graphics', 'maxfps', '60')
        elif version == 2:
            pass  # Was icon copy, no longer needed
        elif version == 3:
            config.setdefault('widgets', 'scroll_timeout', '55')
            config.setdefault('widgets', 'scroll_distance', '20')
            config.setdefault('widgets', 'scroll_friction', '1.')
        elif version == 4:
            config.setdefault('kivy', 'keyboard_mode', '')
            config.setdefault('kivy', 'keyboard_layout', 'qwerty')
        elif version == 5:
            config.setdefault('graphics', 'resizable', '1')
        elif version == 6:
            config.setdefault('widgets', 'scroll_stoptime', '300')
            config.setdefault('widgets', 'scroll_moves', '5')
        elif version == 7:
            is_desktop = int(platform in ('win', 'macosx', 'linux'))
            config.setdefault('kivy', 'desktop', is_desktop)
            config.setdefault('postproc', 'triple_tap_distance', '20')
            config.setdefault('postproc', 'triple_tap_time', '375')
        elif version == 8:
            if config.getint('widgets', 'scroll_timeout') == 55:
                config.set('widgets', 'scroll_timeout', '250')
        elif version == 9:
            config.setdefault('kivy', 'exit_on_escape', '1')
        elif version == 10:
            config.set('graphics', 'fullscreen', '0')
            config.setdefault('graphics', 'borderless', '0')
        elif version == 11:
            config.setdefault('kivy', 'pause_on_minimize', '0')
        elif version == 12:
            config.setdefault('graphics', 'window_state', 'visible')
        elif version == 13:
            config.setdefault('graphics', 'minimum_width', '0')
            config.setdefault('graphics', 'minimum_height', '0')
        elif version == 14:
            config.setdefault('graphics', 'min_state_time', '.035')
        elif version == 15:
            config.setdefault('kivy', 'kivy_clock', 'default')
        elif version == 16:
            config.setdefault('kivy', 'default_font', [
                'Roboto',
                'data/fonts/Roboto-Regular.ttf',
                'data/fonts/Roboto-Italic.ttf',
                'data/fonts/Roboto-Bold.ttf',
                'data/fonts/Roboto-BoldItalic.ttf'])
        elif version == 17:
            config.setdefault('graphics', 'allow_screensaver', '1')
        elif version == 18:
            config.setdefault('kivy', 'log_maxfiles', '100')
        elif version == 19:
            config.setdefault('graphics', 'shaped', '0')
            config.setdefault('kivy', 'window_shape', 'data/images/defaultshape.png')
        elif version == 20:
            config.setdefault('network', 'useragent', 'curl')
        elif version == 21:
            config.setdefault('graphics', 'vsync', '')
        elif version == 22:
            config.setdefault('graphics', 'verify_gl_main_thread', '1')
        elif version == 23:
            config.setdefault('graphics', 'custom_titlebar', '0')
            config.setdefault('graphics', 'custom_titlebar_border', '5')
        elif version == 24:
            config.setdefault("network", "implementation", "default")
        elif version == 25:
            config.setdefault('graphics', 'always_on_top', '0')
        elif version == 26:
            config.setdefault("graphics", "show_taskbar_icon", "1")
        elif version == 27:
            if config.get("kivy", "window_shape") == "data/images/defaultshape.png":
                config.set("kivy", "window_shape", "")
        elif version == 28:
            alpha_size = "8" if pi_version is None else "0"
            config.setdefault("graphics", "alpha_size", alpha_size)
        # WARNING: When adding a new version migration here,
        # don't forget to increment KIVY_CONFIG_VERSION !
        else:
            break

        version += 1

    # Indicate to the Config that we've upgraded to the latest version.
    config.set('kivy', 'config_version', KIVY_CONFIG_VERSION)

    # Now, activate log file
    Logger.logfile_activated = bool(config.getint('kivy', 'log_enable'))

    # If no configuration exist, write the default one.
    if ((not exists(config_filename) or need_save) and
            'KIVY_NO_CONFIG' not in environ):
        try:
            config.filename = config_filename
            config.write()
        except Exception:
            Logger.exception('Core: Error while saving default config file')


if not environ.get('KIVY_DOC_INCLUDE'):

    #
    # Create lazy Config proxy at module import time
    # Actual initialization deferred until App.__init__()
    #

    # Create lazy proxy (no side effects!)
    Config = ConfigProxy()

    # Register the logger callback (will be applied during initialization)
    Config.add_callback(logger_config_update, 'kivy', 'log_level')
