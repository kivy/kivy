'''
Kivy framework
==============

Kivy is an open source library for developing multi-touch applications. It is
completely cross-platform (Linux/OSX/Win) and released under the terms of the
GNU LGPL.

It comes with native support for many multi-touch input devices, a growing
library of multi-touch aware widgets and hardware accelerated OpenGL drawing.
Kivy is designed to let you focus on building custom and highly interactive
applications as quickly and easily as possible.

With Kivy, you can take full advantage of the dynamic nature of Python. There
are thousands of high-quality, free libraries that can be integrated in your
application. At the same time, performance-critical parts are implemented
in the C language.

See http://kivy.org for more information.
'''

__all__ = (
    'require',
    'kivy_configure', 'kivy_register_post_configuration',
    'kivy_options', 'kivy_base_dir',
    'kivy_modules_dir', 'kivy_data_dir', 'kivy_shader_dir',
    'kivy_icons_dir', 'kivy_home_dir',
    'kivy_config_fn', 'kivy_usermodules_dir',
)

__version__ = '1.1.0'

import sys
import shutil
from getopt import getopt, GetoptError
from os import environ, mkdir
from os.path import dirname, join, basename, exists, expanduser
from kivy.logger import Logger, LOG_LEVELS
from kivy.utils import platform

# internals for post-configuration
__kivy_post_configuration = []


if platform() == 'macosx' and sys.maxint < 9223372036854775807:
    r ='''Unsupported Python version detected!:
    Kivy requires a 64 bit version of Python to run on OS X. We strongly advise
    you to use the version of Python that is provided by Apple (don't use ports,
    fink or homebrew unless you know what you're doing).
    See http://kivy.org/docs/installation/installation-macosx.html for details.
    '''
    Logger.critical(r)


def require(version):
    '''Require can be used to check the minimum version required to run a Kivy
    application. For example, you can start your application code like this::

        import kivy
        kivy.require('1.0.1')

    If a user attempts to run your application with a version of Kivy that is
    older than the specified version, an Exception is raised.

    The Kivy version string is built like this::

        X.Y.Z[-tag[-tagrevision]]

        X is the major version
        Y is the minor version
        Z is the bugfixes revision

    The tag is optional, but may be one of 'dev', 'alpha', or 'beta'.
    The tagrevision is the revision of the tag.

    .. warning::

        You must not ask for a version with a tag, except -dev. Asking for a
        'dev' version will just warn the user if the current Kivy version is not
        a -dev, but it will never raise an exception.
        You must not ask for a version with a tagrevision.

    '''

    def parse_version(version):
        # check for tag
        tag = None
        tagrev = None
        if '-' in version:
            l = version.split('-')
            if len(l) == 2:
                version, tag = l
            elif len(l) == 3:
                version, tag, tagrev = l
            else:
                raise Exception('Revision format must be X.Y.Z[-tag]')

        # check x y z
        l = version.split('.')
        if len(l) != 3:
            raise Exception('Revision format must be X.Y.Z[-tag]')
        return [int(x) for x in l], tag, tagrev

    # user version
    revision, tag, tagrev = parse_version(version)
    # current version
    sysrevision, systag, systagrev = parse_version(__version__)

    # ensure that the required version don't contain tag, except dev
    if tag not in (None, 'dev'):
        raise Exception('Revision format must not have any tag except "dev"')
    if tag == 'dev' and systag != 'dev':
        Logger.warning('Application requested a -dev version of Kivy. '
                       '(You have %s, but the application requires %s)' % (
                            __version__, version))
    # not tag rev (-alpha-1, -beta-x) allowed.
    if tagrev is not None:
        raise Exception('Revision format must not contain any tagrevision')

    # finally, checking revision
    if sysrevision < revision:
        raise Exception('The version of Kivy installed on this system '
                        'is too old. '
                        '(You have %s, but the application requires %s)' % (
                            __version__, version))


def kivy_configure():
    '''Call post-configuration of Kivy.
    This function must be called if you create the window yourself.
    '''
    for callback in __kivy_post_configuration:
        callback()


def kivy_register_post_configuration(callback):
    '''Register a function to be called when kivy_configure() is called.

    .. warning::
        Internal use only.
    '''
    __kivy_post_configuration.append(callback)


def kivy_usage():
    '''Kivy Usage: %s [OPTION...] ::

        -h, --help
            Prints this help message.
        -d, --debug
            Shows debug log
        -a, --auto-fullscreen
            Force 'auto' fullscreen mode (no resolution change).
            Uses your display's resolution. This is most likely what you want.
        -c, --config section:key[:value]
            Set a custom [section] key=value in the configuration object
        -f, --fullscreen
            Force running in fullscreen mode.
        -k, --fake-fullscreen
            Force 'fake' fullscreen mode (no window border/decoration).
            Uses the resolution specified by width and height in your config.
        -w, --windowed
            Force running in a window.
        -p, --provider id:provider[,options]
            Add an input provider (eg: ccvtable1:tuio,192.168.0.1:3333).
        -m mod, --module=mod
            Activate a module (use "list" to get a list of available modules).
        -r, --rotation
            Rotate the window's contents (0, 90, 180, 270).
        -s, --save
            Save current Kivy configuration.
        --size=640x480
            Size of window geometry.
    '''
    print kivy_usage.__doc__ % (basename(sys.argv[0]))


# Start !
if 'vim' in globals():
    Logger.setLevel(level=LOG_LEVELS.get('critical'))
else:
    Logger.setLevel(level=LOG_LEVELS.get('info'))
    Logger.info('Kivy v%s' % (__version__))

#: Global settings options for kivy
kivy_options = {
    'window': ('pygame', ),
    'text': ('pil', 'pygame'),
    'video': ('ffmpeg', 'gstreamer', 'pyglet'),
    'audio': ('pygame', 'gstreamer', ),
    'image': ('dds', 'gif', 'pil', 'pygame'),
    'camera': ('opencv', 'gstreamer', 'videocapture'),
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
            Logger.warning('Core: Wrong value for %s environment key' % key)
            Logger.exception('')

# Extract all needed path in kivy
#: Kivy directory
kivy_base_dir = dirname(sys.modules[__name__].__file__)
#: Kivy modules directory
kivy_modules_dir = environ.get('KIVY_MODULES_DIR',
                               join(kivy_base_dir, 'modules'))
#: Kivy extension directory
kivy_exts_dir = environ.get('KIVY_EXTS_DIR',
                            join(kivy_base_dir, 'extensions'))
#: Kivy data directory
kivy_data_dir = environ.get('KIVY_DATA_DIR',
                            join(kivy_base_dir, 'data'))
#: Kivy glsl shader directory
kivy_shader_dir = join(kivy_data_dir, 'glsl')
#: Kivy icons config path (don't remove the last '')
kivy_icons_dir = join(kivy_data_dir, 'icons', '')
#: Kivy user-home storage directory
kivy_home_dir = None
#: Kivy configuration filename
kivy_config_fn = None
#: Kivy user modules directory
kivy_usermodules_dir = None

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
    if platform() == 'android':
        user_home_dir = environ['ANDROID_APP_PATH']
    kivy_home_dir = join(user_home_dir, '.kivy')
    kivy_config_fn = join(kivy_home_dir, 'config.ini')

    if not exists(kivy_home_dir):
        mkdir(kivy_home_dir)

    kivy_usermodules_dir = join(kivy_home_dir, 'mods')
    if not exists(kivy_usermodules_dir):
        mkdir(kivy_usermodules_dir)

    kivy_userexts_dir = join(kivy_home_dir, 'extensions')
    if not exists(kivy_userexts_dir):
        mkdir(kivy_userexts_dir)

    icon_dir = join(kivy_home_dir, 'icon')
    if not exists(icon_dir):
        try:
            shutil.copytree(join(kivy_data_dir, 'logo'), icon_dir)
        except shutil.Error, e:
            Logger.exception('Error when copying logo directory')

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
            opts, args = getopt(sys_argv[1:], 'hp:fkawFem:sr:dc:',
                ['help', 'fullscreen', 'windowed', 'fps', 'event',
                 'module=', 'save', 'fake-fullscreen', 'auto-fullscreen',
                 'display=', 'size=', 'rotate=', 'config=', 'debug'])

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
            try:
                pid, args = arg.split(':', 1)
                Config.set('input', pid, args)
            except ValueError:
                # when we are doing an executable on macosx with pyinstaller,
                # they are passing information with -p. so it will conflict with
                # our current -p option. since the format is not the same, just
                # avoid it.
                pass
        elif opt in ('-a', '--auto-fullscreen'):
            Config.set('graphics', 'fullscreen', 'auto')
        elif opt in ('-c', '--config'):
            l = arg.split(':', 2)
            if len(l) == 2:
                Config.set(l[0], l[1], '')
            elif len(l) == 3:
                Config.set(l[0], l[1], l[2])
            else:
                raise Exception('Invalid --config value')
            if l[0] == 'kivy' and l[1] == 'log_level':
                level = LOG_LEVELS.get(Config.get('kivy', 'log_level'))
                Logger.setLevel(level=level)
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
                from kivy.modules import Modules
                Modules.usage_list()
                sys.exit(0)
            args = arg.split(':', 1)
            if len(args) == 1:
                args += ['']
            Config.set('modules', args[0], args[1])
        elif opt in ('-s', '--save'):
            need_save = True
        elif opt in ('-r', '--rotation'):
            Config.set('graphics', 'rotation', arg)
        elif opt in ('-d', '--debug'):
            level = LOG_LEVELS.get('debug')
            Logger.setLevel(level=level)

    if need_save:
        try:
            with open(kivy_config_fn, 'w') as fd:
                Config.write(fd)
        except Exception, e:
            Logger.exception('Core: error while saving default'
                             'configuration file:', str(e))
        Logger.info('Core: Kivy configuration saved.')
        sys.exit(0)

# android hooks: force fullscreen and add android touch input provider
if platform() == 'android':
    from kivy.config import Config
    Config.set('graphics', 'fullscreen', 'auto')
    Config.remove_section('input')
    Config.add_section('input')
    Config.set('input', 'androidtouch', 'android')

