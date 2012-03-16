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
    for option, modulename, classname in llist:
        try:
            # module activated in config ?
            if option not in kivy.kivy_options[category]:
                Logger.debug('%s: option <%s> ignored by config' %
                    (category.capitalize(), option))
                continue

            # import module
            mod = __import__(name='%s.%s' % (category, modulename),
                                globals=globals(),
                                locals=locals(),
                                fromlist=[modulename], level=-1)
            cls = mod.__getattribute__(classname)

            # ok !
            Logger.info('%s: using <%s> as %s provider' %
                (category.capitalize(), option, category))
            if create_instance:
                cls = cls()
            return cls

        except ImportError as e:
            Logger.warning('%s: Unable to use <%s> as %s'
                    'provider' % (category.capitalize(), option, category))
            Logger.warning('%s: Associated module are missing' %
                    (category.capitalize()))
            Logger.debug('', exc_info=e)

        except CoreCriticalException as e:
            Logger.error('%s: Unable to use <%s> as %s'
                    'provider' % (category.capitalize(), option, category))
            Logger.error('%s: The module raised an important error: %r' %
                    (category.capitalize(), e.message))
            raise

        except Exception as e:
            Logger.warning('%s: Unable to use <%s> as %s'
                    'provider' % (category.capitalize(), option, category))
            Logger.debug('', exc_info=e)

    Logger.critical('%s: Unable to find any valuable %s provider '
            'at all!' % (category.capitalize(), category.capitalize()))


def core_register_libs(category, libs):
    if 'KIVY_DOC' in os.environ:
        return
    category = category.lower()
    for option, lib in libs:
        try:
            # module activated in config ?
            if option not in kivy.kivy_options[category]:
                Logger.debug('%s: option <%s> ignored by config' %
                    (category.capitalize(), option))
                continue

            # import module
            __import__(name='%s.%s' % (category, lib),
                        globals=globals(),
                        locals=locals(),
                        fromlist=[lib],
                        level=-1)

        except Exception as e:
            Logger.warning('%s: Unable to use <%s> as loader!' %
                (category.capitalize(), option))
            Logger.debug('', exc_info=e)

