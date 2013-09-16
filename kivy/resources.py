'''
Resources management
====================

Resource management can be a pain if you have multiple path and project. We are
offering you 2 functions for searching specific resources across a list of
paths.
'''

__all__ = ('resource_find', 'resource_add_path', 'resource_remove_path')

from os.path import join, dirname, exists
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
    '''Search a resource in list of paths.
    Use resource_add_path to add a custom path to search.
    '''
    if not filename:
        return None
    if filename[:8] == 'atlas://':
        return filename
    if exists(filename):
        return filename
    for path in reversed(resource_paths):
        output = join(path, filename)
        if exists(output):
            return output
    return None


def resource_add_path(path):
    '''Add a custom path to search in
    '''
    if path in resource_paths:
        return
    Logger.debug('Resource: add <%s> in path list' % path)
    resource_paths.append(path)


def resource_remove_path(path):
    '''Remove a search path

    .. versionadded:: 1.0.8
    '''
    if path not in resource_paths:
        return
    Logger.debug('Resource: remove <%s> from path list' % path)
    resource_paths.remove(path)

