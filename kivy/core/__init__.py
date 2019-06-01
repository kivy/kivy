'''
Core Abstraction
================

This module defines the abstraction layers for our core providers and their
implementations. For further information, please refer to
:ref:`architecture` and the :ref:`providers` section of the documentation.

In most cases, you shouldn't directly use a library that's already covered
by the core abstraction. Always try to use our providers first.
In case we are missing a feature or method, please let us know by
opening a new Bug report instead of relying on your library.

.. warning::
    These are **not** widgets! These are just abstractions of the respective
    functionality. For example, you cannot add a core image to your window.
    You have to use the image **widget** class instead. If you're really
    looking for widgets, please refer to :mod:`kivy.uix` instead.
'''


import os
import sysconfig
import sys
import traceback
import tempfile
import subprocess
import kivy
from kivy.logger import Logger
from kivy.compat import PY2


class CoreCriticalException(Exception):
    pass


def core_select_lib(category, llist, create_instance=False,
                    base='kivy.core', basemodule=None):
    if 'KIVY_DOC' in os.environ:
        return
    category = category.lower()
    basemodule = basemodule or category
    libs_ignored = []
    errs = []
    for option, modulename, classname in llist:
        try:
            # module activated in config ?
            try:
                if option not in kivy.kivy_options[category]:
                    libs_ignored.append(modulename)
                    Logger.debug(
                        '{0}: Provider <{1}> ignored by config'.format(
                            category.capitalize(), option))
                    continue
            except KeyError:
                pass

            # import module
            mod = __import__(name='{2}.{0}.{1}'.format(
                basemodule, modulename, base),
                globals=globals(),
                locals=locals(),
                fromlist=[modulename], level=0)
            cls = mod.__getattribute__(classname)

            # ok !
            Logger.info('{0}: Provider: {1}{2}'.format(
                category.capitalize(), option,
                '({0} ignored)'.format(libs_ignored) if libs_ignored else ''))
            if create_instance:
                cls = cls()
            return cls

        except ImportError as e:
            errs.append((option, e, sys.exc_info()[2]))
            libs_ignored.append(modulename)
            Logger.debug('{0}: Ignored <{1}> (import error)'.format(
                category.capitalize(), option))
            Logger.trace('', exc_info=e)

        except CoreCriticalException as e:
            errs.append((option, e, sys.exc_info()[2]))
            Logger.error('{0}: Unable to use {1}'.format(
                category.capitalize(), option))
            Logger.error(
                '{0}: The module raised an important error: {1!r}'.format(
                    category.capitalize(), e.message))
            raise

        except Exception as e:
            errs.append((option, e, sys.exc_info()[2]))
            libs_ignored.append(modulename)
            Logger.trace('{0}: Unable to use {1}'.format(
                category.capitalize(), option, category))
            Logger.trace('', exc_info=e)

    err = '\n'.join(['{} - {}: {}\n{}'.format(opt, e.__class__.__name__, e,
                   ''.join(traceback.format_tb(tb))) for opt, e, tb in errs])
    Logger.critical(
        '{0}: Unable to find any valuable {0} provider. Please enable '
        'debug logging (e.g. add -d if running from the command line, or '
        'change the log level in the config) and re-run your app to '
        'identify potential causes\n{1}'.format(category.capitalize(), err))


def core_register_libs(category, libs, base='kivy.core'):
    if 'KIVY_DOC' in os.environ:
        return
    category = category.lower()
    kivy_options = kivy.kivy_options[category]
    libs_loadable = {}
    libs_ignored = []

    for option, lib in libs:
        # module activated in config ?
        if option not in kivy_options:
            Logger.debug('{0}: option <{1}> ignored by config'.format(
                category.capitalize(), option))
            libs_ignored.append(lib)
            continue
        libs_loadable[option] = lib

    libs_loaded = []
    for item in kivy_options:
        try:
            # import module
            try:
                lib = libs_loadable[item]
            except KeyError:
                continue
            __import__(name='{2}.{0}.{1}'.format(category, lib, base),
                       globals=globals(),
                       locals=locals(),
                       fromlist=[lib],
                       level=0)

            libs_loaded.append(lib)

        except Exception as e:
            Logger.trace('{0}: Unable to use <{1}> as loader!'.format(
                category.capitalize(), option))
            Logger.trace('', exc_info=e)
            libs_ignored.append(lib)

    Logger.info('{0}: Providers: {1} {2}'.format(
        category.capitalize(),
        ', '.join(libs_loaded),
        '({0} ignored)'.format(
            ', '.join(libs_ignored)) if libs_ignored else ''))
    return libs_loaded


def handle_win_lib_import_error(category, provider, mod_name):
    if sys.platform != 'win32':
        return

    assert mod_name.startswith('kivy.')
    kivy_root = os.path.dirname(kivy.__file__)
    dirs = mod_name[5:].split('.')
    mod_path = os.path.join(kivy_root, *dirs)

    # get the full expected path to the compiled pyd file
    if PY2:
        mod_path += '.pyd'
    else:
        # filename is <debug>.cp<major><minor>-<platform>.pyd
        # https://github.com/python/cpython/blob/master/Doc/whatsnew/3.5.rst
        if hasattr(sys, 'gettotalrefcount'):  # debug
            mod_path += '._d'
        mod_path += '.cp{}{}-{}.pyd'.format(
            sys.version_info.major, sys.version_info.minor,
            sysconfig.get_platform().replace('-', '_'))

    # does the compiled pyd exist at all?
    if not os.path.exists(mod_path):
        Logger.debug(
            '{}: Failed trying to import "{}" for provider {}. Compiled file '
            'does not exist. Have you perhaps forgotten to compile Kivy, or '
            'did not install all required dependencies?'.format(
                category, provider, mod_path))
        return

    # tell user to provide dependency walker
    env_var = 'KIVY_{}_DEPENDENCY_WALKER'.format(provider.upper())
    if env_var not in os.environ:
        Logger.debug(
            '{0}: Failed trying to import the "{1}" provider from "{2}". '
            'This error is often encountered when a dependency is missing,'
            ' or if there are multiple copies of the same dependency dll on '
            'the Windows PATH and they are incompatible with each other. '
            'This can occur if you are mixing installations (such as different'
            ' python installations, like anaconda python and a system python) '
            'or if another unrelated program added its directory to the PATH. '
            'Please examine your PATH and python installation for potential '
            'issues. To further troubleshoot a "DLL load failed" error, '
            'please download '
            '"Dependency Walker" (64 or 32 bit version - matching your python '
            'bitness) from dependencywalker.com and set the environment '
            'variable {3} to the full path of the downloaded depends.exe file '
            'and rerun your application to generate an error report'.
            format(category, provider, mod_path, env_var))
        return

    depends_bin = os.environ[env_var]
    if not os.path.exists(depends_bin):
        raise ValueError('"{}" provided in {} does not exist'.format(
            depends_bin, env_var))

    # make file for the resultant log
    fd, temp_file = tempfile.mkstemp(
        suffix='.dwi', prefix='kivy_depends_{}_log_'.format(provider),
        dir=os.path.expanduser('~/'))
    os.close(fd)

    Logger.info(
        '{}: Running dependency walker "{}" on "{}" to generate '
        'troubleshooting log. Please wait for it to complete'.format(
            category, depends_bin, mod_path))
    Logger.debug(
        '{}: Dependency walker command is "{}"'.format(
            category,
            [depends_bin, '/c', '/od:{}'.format(temp_file), mod_path]))

    try:
        subprocess.check_output([
            depends_bin, '/c', '/od:{}'.format(temp_file), mod_path])
    except subprocess.CalledProcessError as exc:
        if exc.returncode >= 0x00010000:
            Logger.error(
                '{}: Dependency walker failed with error code "{}". No '
                'error report was generated'.
                format(category, exc.returncode))
            return

    Logger.info(
        '{}: dependency walker generated "{}" containing troubleshooting '
        'information about provider {} and its failing file "{} ({})". You '
        'can open the file in dependency walker to view any potential issues '
        'and troubleshoot it yourself. '
        'To share the file with the Kivy developers and request support, '
        'please contact us at our support channels '
        'https://kivy.org/doc/master/contact.html (not on github, unless '
        'it\'s truly a bug). Make sure to provide the generated file as well '
        'as the *complete* Kivy log being printed here. Keep in mind the '
        'generated dependency walker log file contains paths to dlls on your '
        'system used by kivy or its dependencies to help troubleshoot them, '
        'and these paths may include your name in them. Please view the '
        'log file in dependency walker before sharing to ensure you are not '
        'sharing sensitive paths'.format(
            category, temp_file, provider, mod_name, mod_path))
