'''
Modules
=======

Modules are classes that can be loaded when a Kivy application is starting. The
loading of modules are managed inside the config file. For example, we have few
modules like:

    * touchring: Draw a circle around each touch
    * monitor: Add a red topbar that indicate the FPS and little graph about
      activity input.
    * keybinding: Bind some keys to action, like screenshot.

Modules are automatically searched accross Kivy path and User path:

    * `PATH_TO_KIVY/kivy/modules`
    * `HOME/.kivy/mods`

Activate module in config
-------------------------

To activate a module, you can edit your configuration file (in your
`HOME/.kivy/config.ini`)::

    [modules]
    # uncomment to activate
    touchring =
    # monitor =
    # keybinding =

Only the name of the module followed by a = is sufficient to activate the
module.

Activate module in Python
-------------------------

Before starting your application, preferably at the start of your import, you
can do something like this::

    import kivy
    kivy.require('1.0.8')

    # here, activate touchring module
    from kivy.config import Config
    Config.set('modules', 'touchring', '')


Create my own module
--------------------

Create a file in your `HOME/.kivy/mods`, and create 2 functions::

    def start(win, ctx):
        pass

    def stop(win, ctx):
        pass

Start/stop are functions that will be called for every window opened in Kivy.
When you are starting a module, to use global variables to store the module
state. Use the `ctx` variable as a dictionnary. This context is unique for each
instance / start() call of the module, and will be passed to stop() too.

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
            name, ext = os.path.splitext(module)
            # accept only python extensions
            if ext not in ('.py', '.pyo', '.pyc') or name == '__init__':
                continue
            self.mods[name] = {
                'name': name,
                'activated': False,
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
    print Modules.list()
