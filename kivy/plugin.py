'''
Plugins: basic plugins management, used for desktop examples
'''

__all__ = ('MTContext', 'MTPlugins')

import sys
import os

class MTContext(object):
    '''Context storage of a plugin'''
    def __init__(self):
        pass

class MTPlugins(object):
    '''Scan the examples directory, and extract the plugins in.'''
    def __init__(self, plugin_paths=['../examples/']):
        self.plugin_paths = plugin_paths
        self.plugins = {}
        self.plugins_loaded = False

    def update_sys_path(self):
        for path in self.plugin_paths:
            if path not in sys.path:
                sys.path.append(path)

    def search_plugins(self):
        self.update_sys_path()
        for path in self.plugin_paths:
            try:
                l = os.listdir(path)
            except:
                continue
            for plugin in l:
                if not os.path.isdir(os.path.join(path, plugin)):
                    continue
                try:
                    a = __import__(name='%s.%s' % (plugin, plugin),
                                   fromlist=plugin)
                    if not a.IS_KIVY_PLUGIN:
                        continue
                    a.__internal_path = os.path.join(path, plugin)
                    a.__internal_name = plugin
                    self.plugins[plugin] = a
                except Exception:
                    pass

    def list(self):
        '''Return a list of plugin'''
        if not self.plugins_loaded:
            self.search_plugins()
        return self.plugins

    def get_plugin(self, name):
        '''Return a module from a name'''
        return self.plugins[name]

    def get_key(self, plugin, key, default_value=''):
        try:
            return plugin.__getattribute__(key)
        except:
            return default_value

    def get_infos(self, plugin):
        '''Return a dict info from module'''
        return {
            'title': self.get_key(plugin, 'PLUGIN_TITLE'),
            'author': self.get_key(plugin, 'PLUGIN_AUTHOR'),
            'email': self.get_key(plugin, 'PLUGIN_EMAIL'),
            'description': self.get_key(plugin, 'PLUGIN_DESCRIPTION'),
            'icon': self.get_key(plugin, 'PLUGIN_ICON', '%s.png' % \
                                 plugin.__internal_name),
            'path': plugin.__internal_path
        }

    def activate(self, plugin, container):
        '''Activate a plugin'''
        ctx = MTContext()
        plugin.kivy_plugin_activate(container, ctx)

    def deactivate(self, plugin, container):
        '''Deactivate a plugin'''
        # XXX TODO: remember each context for each plugin instance !
        #ctx = MTContext()
        try:
            plugin.kivy_plugin_deactivate(container)
        except:
            pass


if __name__ == '__main__':
    a = MTPlugins()
    for plugin in a.list():
        print a.get_infos(a.get_plugin(plugin))
