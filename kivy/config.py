'''
Config: base for Kivy configuration file
'''

__all__ = ('Config', )

from ConfigParser import ConfigParser
import sys
import os
from kivy.logger import Logger
from kivy import kivy_home_dir, kivy_config_fn

# Version number of current configuration format
KIVY_CONFIG_VERSION = 16

#: Kivy configuration object
Config = None

if not 'KIVY_DOC_INCLUDE' in os.environ:

    #
    # Read, analyse configuration file
    # Support upgrade of older config file version
    #

    class KivyConfigParser(ConfigParser):
        def setdefault(self, section, option, value):
            if self.has_option(section, option):
                return
            self.set(section, option, value)

        def getdefault(self, section, option, defaultvalue):
            if not self.has_section(section):
                return defaultvalue
            if not self.has_option(section, option):
                return defaultvalue
            return self.getint(section, option)

        def adddefaultsection(self, section):
            if self.has_section(section):
                return
            self.add_section(section)

        def write(self):
            with open(kivy_config_fn, 'w') as fd:
                ConfigParser.write(self, fd)

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
            Config.setdefault('graphics', 'window_icon', os.path.join(kivy_home_dir, 'icon', 'kivy32.png') )

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
