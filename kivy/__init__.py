'''
Kivy framework
==============

Kivy is an open source library for developing multi-touch applications. It is
completely cross-platform (Linux/OSX/Win) and released under the terms of the
GNU LGPL.

It comes with native support for many multi-touch input devices, a growing
library of multi-touch aware widgets, hardware accelerated OpenGL drawing,
and an architecture that is designed to let you focus on building custom and
highly interactive applications as quickly and easily as possible.

Thanks to Kivy's pure Python interface, you can take advantage of its highly
dynamic nature and use any of the thousands of high quality Python libraries
out there.
At the same time, performance-critical sections are internally implemented
on the C-level to maximize performance.

See http://kivy.org for more information.
'''

__all__ = (
    'kivy_configure', 'kivy_register_post_configuration',
    'kivy_options', 'kivy_base_dir', 'kivy_libs_dir',
    'kivy_modules_dir', 'kivy_data_dir', 'kivy_shader_dir',
    'kivy_providers_dir', 'kivy_icons_dir', 'kivy_home_dir',
    'kivy_config_fn', 'kivy_usermodules_dir',
)

__version__ = '1.0.1-dev'

import sys
from shutil import copytree
from getopt import getopt, GetoptError
from os import environ, mkdir
from os.path import dirname, join, basename, exists, expanduser
from kivy.logger import Logger, LOG_LEVELS

# internals for post-configuration
__kivy_post_configuration = []


def kivy_configure():
    '''Call post-configuration of Kivy.
    This function must be called in case of you create yourself the window.
    '''
    for callback in __kivy_post_configuration:
        callback()


def kivy_register_post_configuration(callback):
    '''Register a function to be call when kivy_configure() will be called.

    .. warning::
        Internal use only.
    '''
    __kivy_post_configuration.append(callback)


def kivy_usage():
    '''Kivy Usage: %s [OPTION...] ::

        -h, --help
            Prints this help message.
        -d, --debug
            Show debug log
        -f, --fullscreen
            Force running in fullscreen mode.
        -a, --auto-fullscreen
            Force run in 'auto' fullscreen (no resolution change) mode.
            Uses your display's resolution. This is most likely what you want.
        -k, --fake-fullscreen
            Force running in 'fake' fullscreen (no border) mode.
            Uses the resolution specified by width and height in your config.
        -w, --windowed
            Force running in window.
        -p, --provider id:provider[,options]
            Add an input provider (eg: ccvtable1:tuio,192.168.0.1:3333).
        -m mod, --module=mod
            Activate a module (use "list" to get available modules).
        -r, --rotation
            Rotate the window's contents (0, 90, 180, 270).
        -s, --save
            Save current Kivy configuration.
        --size=640x480
            Size of window geometry.
    '''
    print kivy_usage.__doc__ % (basename(sys.argv[0]))


# Start !
Logger.info('Kivy v%s' % (__version__))

#: Global settings options for kivy
kivy_options = {
    'use_accelerate': True,
    'shadow_window': True,
    'window': ('pygame', 'glut'),
    'text': ('pil', 'cairo', 'pygame'),
    'video': ('gstreamer', 'pyglet'),
    'audio': ('pygame', 'gstreamer', ),
    'image': ('pil', 'pygame'),
    'camera': ('opencv', 'gstreamer', 'videocapture'),
    'svg': ('squirtle', ),
    'spelling': ('enchant', 'osxappkit', ),
    'clipboard': ('pygame', 'dummy'), }

# Read environment
for option in kivy_options:
    key = 'KIVY_%s' % option.upper()
    if key in environ:
        try:
            if type(kivy_options[option]) in (list, tuple):
                kivy_options[option] = (str(environ[key]), )
            else:
                kivy_options[option] = environ[key].lower() in \
                    ('true', '1', 'yes', 'yup')
        except Exception:
            Logger.warning('Core: Wrong value for %s'
                           'environment key' % key)
            Logger.exception('')

# Extract all needed path in kivy
#: Kivy directory
kivy_base_dir = dirname(sys.modules[__name__].__file__)
#: Kivy external libraries directory
kivy_libs_dir = join(kivy_base_dir, 'lib')
#: Kivy modules directory
kivy_modules_dir = join(kivy_base_dir, 'modules')
#: Kivy data directory
kivy_data_dir = join(kivy_base_dir, 'data')
#: Kivy glsl shader directory
kivy_shader_dir = join(kivy_data_dir, 'glsl')
#: Kivy input provider directory
kivy_providers_dir = join(kivy_base_dir, 'input', 'providers')
#: Kivy icons config path (don't remove last '')
kivy_icons_dir = join(kivy_data_dir, 'icons', '')
#: Kivy user-home storage directory
kivy_home_dir = None
#: Kivy configuration filename
kivy_config_fn = None
#: Kivy user modules directory
kivy_usermodules_dir = None

# Add lib in pythonpath
sys.path = [kivy_libs_dir] + sys.path

# Don't go further if we generate documentation
if basename(sys.argv[0]) in ('sphinx-build', 'autobuild.py'):
    environ['KIVY_DOC'] = '1'
if basename(sys.argv[0]) in ('sphinx-build', ):
    environ['KIVY_DOC_INCLUDE'] = '1'
if basename(sys.argv[0]) in ('nosetests', ) or 'nosetests' in sys.argv:
    environ['KIVY_UNITTEST'] = '1'
if not 'KIVY_DOC_INCLUDE' in environ:

    # Configuration management
    user_home_dir = expanduser('~')
    kivy_home_dir = join(user_home_dir, '.kivy')
    kivy_config_fn = join(kivy_home_dir, 'config.ini')
    if not exists(kivy_home_dir):
        mkdir(kivy_home_dir)
    kivy_usermodules_dir = join(kivy_home_dir, 'mods')
    if not exists(kivy_usermodules_dir):
        mkdir(kivy_usermodules_dir)
    icon_dir = join(kivy_home_dir, 'icon')
    if not exists(icon_dir):
        copytree(join(kivy_data_dir, 'logo'), icon_dir)

    # configuration
    from kivy.config import Config

    # Set level of logger
    level = LOG_LEVELS.get(Config.get('kivy', 'log_level'))
    Logger.setLevel(level=level)

    # Can be overrided in command line
    if 'KIVY_UNITTEST' not in environ:

        # save sys argv, otherwize, gstreamer use it and display help..
        sys_argv = sys.argv
        sys.argv = sys.argv[:1]

        try:
            opts, args = getopt(sys_argv[1:], 'hp:fkawFem:snr:d',
                ['help', 'fullscreen', 'windowed', 'fps', 'event',
                 'module=', 'save', 'fake-fullscreen', 'auto-fullscreen',
                 'display=', 'size=', 'rotate=', 'debug'])

        except GetoptError, err:
            Logger.error('Core: %s' % str(err))
            kivy_usage()
            sys.exit(2)

        # set argv to the non-read args
        sys.argv = sys_argv[0:1] + args
    else:
        opts = []
        args = []


    need_save = False
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            kivy_usage()
            sys.exit(0)
        elif opt in ('-p', '--provider'):
            pid, args = arg.split(':', 1)
            Config.set('input', pid, args)
        elif opt in ('-a', '--auto-fullscreen'):
            Config.set('graphics', 'fullscreen', 'auto')
        elif opt in ('-k', '--fake-fullscreen'):
            Config.set('graphics', 'fullscreen', 'fake')
        elif opt in ('-f', '--fullscreen'):
            Config.set('graphics', 'fullscreen', '1')
        elif opt in ('-w', '--windowed'):
            Config.set('graphics', 'fullscreen', '0')
        elif opt in ('--size', ):
            w, h = str(arg).split('x')
            Config.set('graphics', 'width', w)
            Config.set('graphics', 'height', h)
        elif opt in ('--display', ):
            Config.set('graphics', 'display', str(arg))
        elif opt in ('-m', '--module'):
            if str(arg) == 'list':
                kivy_modules.usage_list()
                sys.exit(0)
            args = arg.split(':', 1)
            if len(args) == 1:
                args += ['']
            Config.set('modules', args[0], args[1])
        elif opt in ('-s', '--save'):
            need_save = True
        elif opt in ('-r', '--rotation'):
            Config.set('graphics', 'rotation', arg)
        elif opt in ('-n', ):
            kivy_options['shadow_window'] = False
        elif opt in ('-d', '--debug'):
            level = LOG_LEVELS.get('debug')
            Logger.setLevel(level=level)

    if need_save:
        try:
            with open(kivy_config_fn, 'w') as fd:
                Config.write(fd)
        except Exception, e:
            Logger.exception('Core: error while saving default'
                             'configuration file')
        Logger.info('Core: Kivy configuration saved.')
        sys.exit(0)

