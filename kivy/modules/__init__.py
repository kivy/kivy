'''
Modules
=======

UI module you can plug on any running Kivy apps.
'''

__all__ = ('Modules', )

from kivy.config import Config
from kivy.logger import Logger
import kivy
import os
import sys


class ModuleContext:
    '''Context of a module

    You can access to the config with self.config.
    '''

    def __init__(self):
        self.config = {}


class ModuleBase:
    '''Handle modules of Kivy. Automaticly load and instance
    module for the general window'''

    def __init__(self, **kwargs):
        self.mods = {}
        self.wins = []

    def add_path(self, path):
        '''Add a path to search modules in'''
        if not os.path.exists(path):
            return
        if path not in sys.path:
            sys.path.append(path)
        dirs = os.listdir(path)
        for module in dirs:
            if module[-3:] != '.py' or module == '__init__.py':
                continue
            module = module[:-3]
            self.mods[module] = {'name': module, 'activated': False,
                                 'context': ModuleContext()}

    def list(self):
        '''Return the list of available modules'''
        return self.mods

    def import_module(self, name):
        try:
            module = __import__(name=name, fromlist='.')
        except ImportError:
            Logger.exception('Modules: unable to import <%s>' % name)
            raise
        # basic check on module
        if not hasattr(module, 'start'):
            Logger.warning('Modules: Module <%s> missing start() function' %
                           name)
            return
        if not hasattr(module, 'stop'):
            err = 'Modules: Module <%s> missing stop() function' % name
            Logger.warning(err)
            return
        self.mods[name]['module'] = module

    def activate_module(self, name, win):
        '''Activate a module on a window'''
        if not name in self.mods:
            Logger.warning('Modules: Module <%s> not found' % name)
            return

        if not 'module' in self.mods[name]:
            try:
                self.import_module(name)
            except ImportError:
                return

        module = self.mods[name]['module']
        if not self.mods[name]['activated']:

            # convert configuration like:
            # -m mjpegserver:port=8080,fps=8
            # and pass it in context.config token
            config = dict()

            args = Config.get('modules', name)
            if args != '':
                values = Config.get('modules', name).split(',')
                for value in values:
                    x = value.split('=', 1)
                    if len(x) == 1:
                        config[x[0]] = True
                    else:
                        config[x[0]] = x[1]

            msg = 'Modules: Start <%s> with config %s' % (name, str(config))
            Logger.debug(msg)
            self.mods[name]['context'].config = config
            module.start(win, self.mods[name]['context'])

    def deactivate_module(self, name, win):
        '''Deactivate a module from a window'''
        if not name in self.mods:
            Logger.warning('Modules: Module <%s> not found' % name)
            return
        if not hasattr(self.mods[name], 'module'):
            return
        module = self.mods[name]['module']
        if self.mods[name]['activated']:
            module.stop(win, self.mods[name]['context'])

    def register_window(self, win):
        '''Add window in window list'''
        self.wins.append(win)
        self.update()

    def unregister_window(self, win):
        '''Remove window from window list'''
        self.wins.remove(win)
        self.update()

    def update(self):
        '''Update status of module for each windows'''
        modules_to_activate = map(lambda x: x[0], Config.items('modules'))
        for win in self.wins:
            for name in self.mods:
                if not name in modules_to_activate:
                    self.deactivate_module(name, win)
            for name in modules_to_activate:
                self.activate_module(name, win)

    def usage_list(self):
        print
        print 'Available modules'
        print '================='
        for module in self.list():
            if not 'module' in self.mods[module]:
                self.import_module(module)
            text = self.mods[module]['module'].__doc__.strip("\n ")
            print '%-12s: %s' % (module, text)
        print

Modules = ModuleBase()
Modules.add_path(kivy.kivy_modules_dir)
if not 'KIVY_DOC' in os.environ:
    Modules.add_path(kivy.kivy_usermodules_dir)

if __name__ == '__main__':
    print Module.list()
