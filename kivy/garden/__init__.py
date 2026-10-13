'''
Garden
======

.. versionadded:: 1.7.0

.. versionchanged:: 1.11.1

Garden is a project to centralize addons for Kivy maintained by users. You can
find more information at `Kivy Garden <http://kivy-garden.github.io/>`_. All
the garden packages are centralized on the `kivy-garden Github
<https://github.com/kivy-garden>`_ repository.

.. warning::

    The garden flower widgets are contributed by regular users such as
    yourself. The kivy developers do not take any responsibility for the code
    hosted in the garden organization repositories - we do not actively monitor
    the flower repos. Please use at your own risk.

Update to garden structure
--------------------------

Starting with the kivy 1.11.0 release, kivy has
`shifted <https://github.com/kivy/kivy/wiki/Moving-kivy.garden.xxx-to-kivy_\
garden.xxx-and-kivy.deps.xxx-to-kivy_deps.xxx>`_ from using the garden legacy
tool that installs flowers with `garden install flower` where the flower
does not have a proper python package structure to flowers that can be
installed with pip and uploaded to pypi. Kivy supports the legacy garden
flowers side by side with the newer packages so the garden tool and legacy
flowers will be able to be used indefinitely. But we will only provide support
for the newer packages format in the future.

For garden package maintainers - for a guide how to migrate your garden package
from the legacy structure `garden.flower` to the newer `flower` structure used
with the pip, see `this guide
<https://kivy-garden.github.io/#guideformigratingflowersfromlegacystructure>`_.

We hope most garden packages will be converted to the newer format to help
with installation.

General Usage Guidelines
------------------------

To use a kivy garden flower, first check if the flower is in the legacy format.
If the flower name is in the format of `garden.flower`, such as
`garden.graph <https://github.com/kivy-garden/garden.graph>`_ it is a legacy
flower. If it is just `flower` such as
`graph <https://github.com/kivy-garden/graph>`_ it is in the present format.
If it is in the legacy format see `Legacy garden tool instructions`_ for how to
install and use it. Otherwise, continue with the guide below.

Garden flowers can now be installed with the `pip` tool like a normal python
package. Given a flower that you want to install, lets use
`graph <https://github.com/kivy-garden/graph>`_ as an example. You can install
master directly from github with::

    python -m pip install \
https://github.com/kivy-garden/graph/archive/master.zip

Look under the repository's releases tab if you'd like to install a specific
release or a pre-compiled wheel, if the flower has any. Then use the url with
`pip`.

Or you can automatically install it using garden's pypi server with::

    python -m pip install kivy_garden.graph \
--extra-index-url https://kivy-garden.github.io/simple/

To permanently add our garden server to your pip configuration so that you
don't have to specify it with `--extra-index-url`, add::

    [global]
    timeout = 60
    index-url = https://kivy-garden.github.io/simple/

to your `pip.conf <https://pip.pypa.io/en/stable/user_guide/#config-file>`_.

If the flower maintainer has uploaded the flower to
`pypi <https://pypi.org/>`_, you can just install it with
`pip install kivy_garden.flower`.


Legacy garden tool instructions
-------------------------------

Garden is now distributed as a separate Python module, kivy-garden. You can
install it with pip::

    pip install kivy-garden

The garden module does not initially include any packages. You can download
them with the garden tool installed by the pip package::

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

.. Note:: In previous versions of Kivy, garden was a tool at
          kivy/tools/garden. This no longer exists, but the
          kivy-garden module provides exactly the same functionality.

Packaging
~~~~~~~~~

If you want to include garden packages in your application, you can add `--app`
to the `install` command. This will create a `libs/garden` directory in your
current directory which will be used by `kivy.garden`.

For example::

    cd myapp
    garden install --app graph


'''

__path__ = 'kivy.garden'

import importlib.util
from importlib.abc import MetaPathFinder
import sys
from os.path import dirname, join, realpath, exists, abspath
from kivy import kivy_home_dir
from kivy.utils import platform
import kivy

#: system path where garden modules can be installed
garden_system_dir = join(kivy_home_dir, 'garden')
garden_kivy_dir = abspath(join(dirname(kivy.__file__), 'garden'))

#: application path where garden modules can be installed
if getattr(sys, 'frozen', False) and getattr(sys, '_MEIPASS', False):
    garden_app_dir = join(realpath(sys._MEIPASS), 'libs', 'garden')
else:
    garden_app_dir = join(realpath(dirname(sys.argv[0])), 'libs', 'garden')
#: Fixes issue #4030 in kivy where garden path is incorrect on iOS
if platform == "ios":
    from os.path import join, dirname
    import __main__
    main_py_file = __main__.__file__
    garden_app_dir = join(dirname(main_py_file), 'libs', 'garden')


class GardenImporter(MetaPathFinder):

    def find_spec(self, fullname, path, target=None):
        if path != "kivy.garden":
            return None

        moddir = join(
            garden_kivy_dir, fullname.split(".", 2)[-1], "__init__.py"
        )
        if exists(moddir):
            return importlib.util.spec_from_file_location(fullname, moddir)

        modname = fullname.split(".", 1)[-1]
        for directory in (garden_app_dir, garden_system_dir):
            moddir = join(directory, modname, "__init__.py")
            if exists(moddir):
                return importlib.util.spec_from_file_location(fullname, moddir)

        return None


# insert the garden importer as ultimate importer
sys.meta_path.append(GardenImporter())
