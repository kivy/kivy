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
import kivy
from kivy.logger import Logger


class CoreCriticalException(Exception):
    pass


def core_select_lib(category, llist, create_instance=False):
    if 'KIVY_DOC' in os.environ:
        return
    category = category.lower()
    libs_ignored = []
    for option, modulename, classname in llist:
        try:
            # module activated in config ?
            if option not in kivy.kivy_options[category]:
                libs_ignored.append(modulename)
                Logger.debug('{0}: Provider <{1}> ignored by config'.format(
                    category.capitalize(), option))
                continue

            # import module
            mod = __import__(name='kivy.core.{0}.{1}'.format(
                category, modulename),
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
            libs_ignored.append(modulename)
            Logger.debug('{0}: Ignored <{1}> (import error)'.format(
                category.capitalize(), option))
            Logger.trace('', exc_info=e)

        except CoreCriticalException as e:
            Logger.error('{0}: Unable to use {1}'.format(
                    category.capitalize(), option))
            Logger.error(
                    '{0}: The module raised an important error: {1!r}'.format(
                    category.capitalize(), e.message))
            raise

        except Exception as e:
            libs_ignored.append(modulename)
            Logger.trace('{0}: Unable to use {1}'.format(
                category.capitalize(), option, category))
            Logger.trace('', exc_info=e)

    Logger.critical(
        '{0}: Unable to find any valuable {1} provider at all!'.format(
        category.capitalize(), category.capitalize()))


def core_register_libs(category, libs):
    if 'KIVY_DOC' in os.environ:
        return
    category = category.lower()
    libs_loaded = []
    libs_ignored = []
    for option, lib in libs:
        try:
            # module activated in config ?
            if option not in kivy.kivy_options[category]:
                Logger.debug('{0}: option <{1}> ignored by config'.format(
                    category.capitalize(), option))
                libs_ignored.append(lib)
                continue

            # import module
            __import__(name='kivy.core.{0}.{1}'.format(category, lib),
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

