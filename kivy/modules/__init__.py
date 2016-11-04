'''
Modules
=======

Modules are classes that can be loaded when a Kivy application is starting. The
loading of modules is managed by the config file. Currently, we include:

    * :class:`~kivy.modules.touchring`: Draw a circle around each touch.
    * :class:`~kivy.modules.monitor`: Add a red topbar that indicates the FPS
      and a small graph indicating input activity.
    * :class:`~kivy.modules.keybinding`: Bind some keys to actions, such as a
      screenshot.
    * :class:`~kivy.modules.recorder`: Record and playback a sequence of
      events.
    * :class:`~kivy.modules.screen`: Emulate the characteristics (dpi/density/
      resolution) of different screens.
    * :class:`~kivy.modules.inspector`: Examines your widget hierarchy and
      widget properties.
    * :class:`~kivy.modules.webdebugger`: Realtime examination of your app
      internals via a web browser.

Modules are automatically loaded from the Kivy path and User path:

    * `PATH_TO_KIVY/kivy/modules`
    * `HOME/.kivy/mods`

Activating a module
-------------------

There are various ways in which you can activate a kivy module.

Activate a module in the config
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To activate a module this way, you can edit your configuration file (in your
`HOME/.kivy/config.ini`)::

    [modules]
    # uncomment to activate
    touchring =
    # monitor =
    # keybinding =

Only the name of the module followed by "=" is sufficient to activate the
module.

Activate a module in Python
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before starting your application, preferably at the start of your import, you
can do something like this::

    import kivy
    kivy.require('1.0.8')

    # Activate the touchring module
    from kivy.config import Config
    Config.set('modules', 'touchring', '')

Activate a module via the commandline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When starting your application from the commandline, you can add a
*-m <modulename>* to the arguments. For example::

    python main.py -m webdebugger

.. note::
    Some modules, such as the screen, may require additional parameters. They
    will, however, print these parameters to the console when launched without
    them.


Create your own module
----------------------

Create a file in your `HOME/.kivy/mods`, and create 2 functions::

    def start(win, ctx):
        pass

    def stop(win, ctx):
        pass

Start/stop are functions that will be called for every window opened in
Kivy. When you are starting a module, you can use these to store and
manage the module state. Use the `ctx` variable as a dictionary. This
context is unique for each instance/start() call of the module, and will
be passed to stop() too.

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

    def __repr__(self):
        return repr(self.config)


class ModuleBase:
    '''Handle Kivy modules. It will automatically load and instantiate the
    module for the general window.'''

    def __init__(self, **kwargs):
        self.mods = {}
        self.wins = []

    def add_path(self, path):
        '''Add a path to search for modules in'''
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
            modname = 'kivy.modules.{0}'.format(name)
            module = __import__(name=modname)
            module = sys.modules[modname]
        except ImportError:
            try:
                module = __import__(name=name)
                module = sys.modules[name]
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
        if name not in self.mods:
            Logger.warning('Modules: Module <%s> not found' % name)
            return

        mod = self.mods[name]

        # ensure the module has been configured
        if 'module' not in mod:
            self._configure_module(name)

        pymod = mod['module']
        if not mod['activated']:
            context = mod['context']
            msg = 'Modules: Start <{0}> with config {1}'.format(
                  name, context)
            Logger.debug(msg)
            pymod.start(win, context)
            mod['activated'] = True

    def deactivate_module(self, name, win):
        '''Deactivate a module from a window'''
        if not name in self.mods:
            Logger.warning('Modules: Module <%s> not found' % name)
            return
        if not 'module' in self.mods[name]:
            return

        module = self.mods[name]['module']
        if self.mods[name]['activated']:
            module.stop(win, self.mods[name]['context'])
            self.mods[name]['activated'] = False

    def register_window(self, win):
        '''Add the window to the window list'''
        if win not in self.wins:
            self.wins.append(win)
        self.update()

    def unregister_window(self, win):
        '''Remove the window from the window list'''
        if win in self.wins:
            self.wins.remove(win)
        self.update()

    def update(self):
        '''Update the status of the module for each window'''
        modules_to_activate = [x[0] for x in Config.items('modules')]
        for win in self.wins:
            for name in self.mods:
                if not name in modules_to_activate:
                    self.deactivate_module(name, win)
            for name in modules_to_activate:
                try:
                    self.activate_module(name, win)
                except:
                    import traceback
                    traceback.print_exc()
                    raise

    def configure(self):
        '''(internal) Configure all the modules before using them.
        '''
        modules_to_configure = [x[0] for x in Config.items('modules')]
        for name in modules_to_configure:
            if name not in self.mods:
                Logger.warning('Modules: Module <%s> not found' % name)
                continue
            self._configure_module(name)

    def _configure_module(self, name):
        if 'module' not in self.mods[name]:
            try:
                self.import_module(name)
            except ImportError:
                return

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

        self.mods[name]['context'].config = config

        # call configure if module have one
        if hasattr(self.mods[name]['module'], 'configure'):
            self.mods[name]['module'].configure(config)

    def usage_list(self):
        print()
        print('Available modules')
        print('=================')
        for module in self.list():
            if not 'module' in self.mods[module]:
                self.import_module(module)
            text = self.mods[module]['module'].__doc__.strip("\n ")
            print('%-12s: %s' % (module, text))
        print()

Modules = ModuleBase()
Modules.add_path(kivy.kivy_modules_dir)
if not 'KIVY_DOC' in os.environ:
    Modules.add_path(kivy.kivy_usermodules_dir)

if __name__ == '__main__':
    print(Modules.list())
