'''
Core: providers for image, text, video, audio, camera...
'''

import os
import kivy
from kivy.logger import Logger

if 'KIVY_DOC' in os.environ:
    # stub for sphinx generation
    def core_select_lib(category, llist, create_instance=False):
        pass
    def core_register_libs(category, libs):
        pass
else:
    def core_select_lib(category, llist, create_instance=True):
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

            except Exception as e:
                Logger.warning('%s: Unable to use <%s> as %s'
                     'provider' % ( category.capitalize(), option, category))
                Logger.debug('', exc_info=e)

        Logger.critical('%s: Unable to find any valuable %s provider'
              'at all!' % (category.capitalize(),category.capitalize()))


    def core_register_libs(category, libs):
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

