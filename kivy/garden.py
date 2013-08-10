'''
Garden
======

.. versionadded:: 1.7.0

Garden is a project to centralize addons for Kivy, maintained by users. You can
find more information at `Kivy Garden <http://kivy-garden.github.io/>`_ All the
garden packages are centralized on the `kivy-garden Github
<https://github.com/kivy-garden>`_.

We provide a tool (`kivy/tools/garden`) for managing garden packages::

    # Installing a garden package
    garden install graph

    # Upgrade a garden package
    garden install --upgrade graph

    # Uninstall a garden package
    garden uninstall graph

    # List all the garden packages installed
    garden list

    # Search new packages
    garden search

    # Search all the packages that contain "graph"
    garden search graph

    # Show the help
    garden --help

All the garden packages are installed by default in `~/.kivy/garden`.

Packaging
---------

If you want to include garden package in your application, you can add `--app`
in the `install` command. This will create a `libs/garden` directory in your
current directory, and will be used by `kivy.garden`.

For example::

    cd myapp
    garden install --app graph


'''

__path__ = 'kivy.garden'

import sys
import imp
from os.path import dirname, join, realpath, exists
from kivy import kivy_home_dir

#: system path where garden modules can be installed
garden_system_dir = join(kivy_home_dir, 'garden')

#: application path where garden modules can be installed
garden_app_dir = join(realpath(dirname(sys.argv[0])), 'libs', 'garden')


class GardenImporter(object):

    def find_module(self, fullname, path):
        if path == 'kivy.garden':
            return self

    def load_module(self, fullname):
        assert(fullname.startswith('kivy.'))
        modname = fullname.split('.', 1)[-1]
        for directory in (garden_app_dir, garden_system_dir):
            moddir = join(directory, modname)
            if exists(moddir):
                return self._load_module(fullname, moddir)

    def _load_module(self, fullname, moddir):
        mod = imp.load_module(fullname, None, moddir,
                ('', '', imp.PKG_DIRECTORY))
        return mod


# insert the garden importer as ultimate importer
sys.meta_path.append(GardenImporter())

