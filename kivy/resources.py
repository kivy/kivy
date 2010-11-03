'''
Resources: Search a file inside a list of paths
'''

__all__ = ('resource_find', 'resource_add_path')

from os.path import join, dirname, exists
from kivy.logger import Logger
import sys

resource_paths = [
    '.',
    dirname(sys.argv[0]),
]

def resource_find(filename):
    '''Search a resource in list of paths.
    Use resource_add_path to add a custom path to search.
    '''
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

