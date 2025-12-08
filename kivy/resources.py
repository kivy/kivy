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

import re
from os.path import join, dirname, exists, abspath
from kivy import kivy_data_dir
from kivy.cache import Cache
from kivy.utils import platform
from kivy.logger import Logger
import sys
import os
import kivy

# Regex for @image_provider:providername(path) URI scheme
_provider_uri_re = re.compile(r'^@image_provider:(\w+)\((.+)\)$')

resource_paths = ['.', dirname(sys.argv[0])]
if platform == 'ios':
    resource_paths += [join(dirname(sys.argv[0]), 'YourApp')]
resource_paths += [dirname(kivy.__file__), join(kivy_data_dir, '..')]

Cache.register('kv.resourcefind', timeout=60)


def _resolve_path(filename):
    # Resolve a filename to an absolute path by searching resource_paths.

    # :param filename: The filename to resolve
    # :returns: The absolute path if found, None otherwise
    abspath_filename = abspath(filename)
    if exists(abspath_filename):
        return abspath(filename)
    for path in reversed(resource_paths):
        abspath_filename = abspath(join(path, filename))
        if exists(abspath_filename):
            return abspath_filename
    return None


def resource_find(filename, use_cache=("KIVY_DOC_INCLUDE" not in os.environ)):
    '''Search for a resource in the list of paths.
    Use resource_add_path to add a custom path to the search.
    By default, results are cached for 60 seconds.
    This can be disabled using use_cache=False.

    .. versionchanged:: 2.1.0
        `use_cache` parameter added and made True by default.

    .. versionchanged:: 3.0.0
        Added support for @image_provider:providername(path) URI scheme.
    '''
    if not filename:
        return
    found_filename = None
    if use_cache:
        found_filename = Cache.get('kv.resourcefind', filename)
        if found_filename:
            return found_filename

    # Handle @image_provider:providername(path) URI scheme
    provider_match = _provider_uri_re.match(filename)
    if provider_match:
        provider_name = provider_match.group(1)
        inner_path = provider_match.group(2)
        resolved_path = _resolve_path(inner_path)
        if resolved_path:
            found_filename = f'@image_provider:{provider_name}({resolved_path})'

    elif filename[:8] == 'atlas://':
        found_filename = filename

    else:
        found_filename = _resolve_path(filename)
        if not found_filename and filename.startswith("data:"):
            found_filename = filename

    if use_cache and found_filename:
        Cache.append('kv.resourcefind', filename, found_filename)
    return found_filename


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
