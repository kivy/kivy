'''
Kivy: Python Multitouch Toolkit

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

__version__ = '0.6-dev'

import sys
import getopt
import os
import shutil
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

        -h, --help                  prints this mesage
        -f, --fullscreen            force run in fullscreen
        -k, --fake-fullscreen       force run in 'fake' fullscreen (no border mode)
        -a, --auto-fullscreen       force run in 'auto' fullscreen (no resolution change)
        -w, --windowed              force run in window
        -p, --provider id:provider[,options] add a provider (eg: ccvtable1:tuio,192.168.0.1:3333)
        -F, --fps                   show fps in window
        -m mod, --module=mod        activate a module (use "list" to get available module)
        -r, --rotation              rotate the window (0, 90, 180, 270)
        -s, --save                  save current Kivy configuration
        --size=640x480              size of window

    '''
    print kivy_usage.__doc__ % (os.path.basename(sys.argv[0]))


# Start !
Logger.info('Kivy v%s' % (__version__))

#: Global settings options for kivy
kivy_options = {
    'use_accelerate': True,
    'shadow_window': True,
    'window': ('pygame', 'glut'),
    'text': ('pil', 'cairo', 'pygame'),
    'video': ('gstreamer', 'pyglet' ),
    'audio': ('pygame', 'gstreamer', ),
    'image': ('pil', 'pygame'),
    'camera': ('opencv', 'gstreamer', 'videocapture'),
    'svg': ('squirtle',),
    'spelling': ('enchant', 'osxappkit',),
    'clipboard': ('pygame', 'dummy'),
}

# Read environment
for option in kivy_options:
    key = 'KIVY_%s' % option.upper()
    if key in os.environ:
        try:
            if type(kivy_options[option]) in (list, tuple):
                kivy_options[option] = (str(os.environ[key]),)
            else:
                kivy_options[option] = os.environ[key].lower() in \
                    ('true', '1', 'yes', 'yup')
        except Exception:
            Logger.warning('Core: Wrong value for %s'
                           'environment key' % key)
            Logger.exception('')

# Extract all needed path in kivy
#: Kivy directory
kivy_base_dir        = os.path.dirname(sys.modules[__name__].__file__)
#: Kivy external libraries directory
kivy_libs_dir        = os.path.join(kivy_base_dir, 'lib')
#: Kivy modules directory
kivy_modules_dir     = os.path.join(kivy_base_dir, 'modules')
#: Kivy data directory
kivy_data_dir        = os.path.join(kivy_base_dir, 'data')
#: Kivy glsl shader directory
kivy_shader_dir        = os.path.join(kivy_data_dir, 'glsl')
#: Kivy input provider directory
kivy_providers_dir   = os.path.join(kivy_base_dir, 'input', 'providers')
#: Kivy icons config path (don't remove last '')
kivy_icons_dir        = os.path.join(kivy_data_dir, 'icons', '')
#: Kivy user-home storage directory
kivy_home_dir        = None
#: Kivy configuration filename
kivy_config_fn       = None
#: Kivy user modules directory
kivy_usermodules_dir = None

# Add lib in pythonpath
sys.path           = [kivy_libs_dir] + sys.path

# Don't go further if we generate documentation
if os.path.basename(sys.argv[0]) in ('sphinx-build', 'autobuild.py'):
    os.environ['KIVY_DOC'] = '1'
if os.path.basename(sys.argv[0]) in ('sphinx-build', ):
    os.environ['KIVY_DOC_INCLUDE'] = '1'
if os.path.basename(sys.argv[0]) in ('nosetests', ) or 'nosetests' in sys.argv:
    os.environ['KIVY_UNITTEST'] = '1'
if not 'KIVY_DOC_INCLUDE' in os.environ:

    # Configuration management
    user_home_dir = os.path.expanduser('~')
    kivy_home_dir = os.path.join(user_home_dir, '.kivy')
    kivy_config_fn = os.path.join(kivy_home_dir, 'config')
    if not os.path.exists(kivy_home_dir):
        os.mkdir(kivy_home_dir)
    kivy_usermodules_dir = os.path.join(kivy_home_dir, 'mods')
    if not os.path.exists(kivy_usermodules_dir):
        os.mkdir(kivy_usermodules_dir)
    '''
    icon_dir = os.path.join(kivy_home_dir, 'icon')
    if not os.path.exists(icon_dir):
        shutil.copytree(os.path.join(kivy_data_dir, 'logo'), icon_dir)
    '''

    # configuration
    from kivy.config import *

    # Set level of logger
    level = LOG_LEVELS.get(Config.get('kivy', 'log_level'))
    Logger.setLevel(level=level)

    # Can be overrided in command line
    if 'KIVY_UNITTEST' not in os.environ:

        # save sys argv, otherwize, gstreamer use it and display help..
        sys_argv = sys.argv
        sys.argv = sys.argv[:1]

        try:
            opts, args = getopt.getopt(sys_argv[1:], 'hp:fkawFem:snr:',
                ['help', 'fullscreen', 'windowed', 'fps', 'event',
                 'module=', 'save', 'fake-fullscreen', 'auto-fullscreen',
                 'display=', 'size=', 'rotate='])

        except getopt.GetoptError, err:
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
        elif opt in ('-F', '--fps'):
            Config.set('kivy', 'show_fps', '1')
        elif opt in ('-e', '--eventstats'):
            Config.set('kivy', 'show_eventstats', '1')
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

    if need_save:
        try:
            with open(kivy_config_fn, 'w') as fd:
                Config.write(fd)
        except Exception, e:
            Logger.exception('Core: error while saving default'
                             'configuration file')
        Logger.info('Core: Kivy configuration saved.')
        sys.exit(0)

# cleanup namespace
if not 'KIVY_DOC_INCLUDE' in os.environ:
    del level, need_save, opts, args
del sys, getopt, os, key
