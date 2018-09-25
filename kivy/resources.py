'''
Resources management
====================

Resource management can be a pain if you have multiple paths and projects.
Kivy offers 2 functions for searching for specific resources across a list
of paths.

Resource lookup
---------------

When Kivy looks for a resource e.g. an image or a kv file, it searches through
a predetermined set of folders. You can modify this folder list using the
:meth:`resource_add_path` and :meth:`resource_remove_path` functions.

Customizing Kivy
----------------

These functions can also be helpful if you want to replace standard Kivy
resources with your own. For example, if you wish to customize or re-style
Kivy, you can force your *style.kv* or *data/defaulttheme-0.png* files to be
used in preference to the defaults simply by adding the path to your preferred
alternatives via the :meth:`resource_add_path` method.

As almost all Kivy resources are looked up using the :meth:`resource_find`, so
you can use this approach to add fonts and keyboard layouts and to replace
images and icons.

'''

__all__ = ('resource_find', 'resource_add_path', 'resource_remove_path')

from os.path import join, dirname, exists, abspath
from kivy import kivy_data_dir
from kivy.utils import platform
from kivy.logger import Logger
import sys
import kivy

resource_paths = ['.', dirname(sys.argv[0])]
if platform == 'ios':
    resource_paths += [join(dirname(sys.argv[0]), 'YourApp')]
resource_paths += [dirname(kivy.__file__), join(kivy_data_dir, '..')]


def resource_find(filename):
    '''Search for a resource in the list of paths.
    Use resource_add_path to add a custom path to the search.
    '''
    if not filename:
        return
    if filename[:8] == 'atlas://':
        return filename
    if exists(abspath(filename)):
        return abspath(filename)
    for path in reversed(resource_paths):
        output = abspath(join(path, filename))
        if exists(output):
            return output
    if filename[:5] == 'data:':
        return filename


def resource_add_path(path):
    '''Add a custom path to search in.
    '''
    if path in resource_paths:
        return
    Logger.debug('Resource: add <%s> in path list' % path)
    resource_paths.append(path)


def resource_remove_path(path):
    '''Remove a search path.

    .. versionadded:: 1.0.8
    '''
    if path not in resource_paths:
        return
    Logger.debug('Resource: remove <%s> from path list' % path)
    resource_paths.remove(path)
