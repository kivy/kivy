'''
FileChooser
===========

The FileChooser module provides various classes for describing, displaying and
browsing file systems.

Simple widgets
--------------

There are two ready-to-use widgets that provide views of the file system. Each
of these present the files and folders in a different style.

The :class:`FileChooserListView` displays file entries as text items in a
vertical list, where folders can be collapsed and expanded.

.. image:: images/filechooser_list.png

The :class:`FileChooserIconView` presents icons and text from left to right,
wrapping them as required.

.. image:: images/filechooser_icon.png

They both provide for scrolling, selection and basic user interaction.
Please refer to the :class:`FileChooserController` for details on supported
events and properties.

Widget composition
------------------

FileChooser classes adopt a
`MVC <https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller>`_
design. They are exposed so that you to extend and customize your file chooser
according to your needs.

The FileChooser classes can be categorized as follows:

* Models are represented by concrete implementations of the
  :class:`FileSystemAbstract` class, such as the :class:`FileSystemLocal`.

* Views are represented by the :class:`FileChooserListLayout` and
  :class:`FileChooserIconLayout` classes. These are used by the
  :class:`FileChooserListView` and :class:`FileChooserIconView` widgets
  respectively.

* Controllers are represented by concrete implementations of the
  :class:`FileChooserController`, namely the :class:`FileChooser`,
  :class:`FileChooserIconView` and :class:`FileChooserListView` classes.

This means you can define your own views or provide :class:`FileSystemAbstract`
implementations for alternative file systems for use with these widgets.
The :class:`FileChooser` can be used as a controller for handling multiple,
synchronized views of the same path. By combining these elements, you can add
your own views and file systems and have them easily interact with the existing
components.

Usage example
-------------

main.py

.. include:: ../../examples/RST_Editor/main.py
    :literal:

editor.kv

.. highlight:: kv

.. include:: ../../examples/RST_Editor/editor.kv
    :literal:

.. versionadded:: 1.0.5

.. versionchanged:: 1.2.0

    In the chooser template, the `controller` is no longer a direct reference
    but a weak-reference. If you are upgrading, you should change the notation
    `root.controller.xxx` to `root.controller().xxx`.

'''

__all__ = ('FileChooserListView', 'FileChooserIconView',
           'FileChooserListLayout', 'FileChooserIconLayout',
           'FileChooser', 'FileChooserController',
           'FileChooserProgressBase', 'FileSystemAbstract',
           'FileSystemLocal')

from weakref import ref
from time import time
from kivy.compat import string_types
from kivy.factory import Factory
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.utils import platform as core_platform
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import (
    StringProperty, ListProperty, BooleanProperty, ObjectProperty,
    NumericProperty, AliasProperty)
from os import listdir
from os.path import (
    basename, join, sep, normpath, expanduser, altsep,
    splitdrive, realpath, getsize, isdir, abspath)
from fnmatch import fnmatch
import collections

platform = core_platform
filesize_units = ('B', 'KB', 'MB', 'GB', 'TB')

_have_win32file = False
if platform == 'win':
    # Import that module here as it's not available on non-windows machines.
    # See http://bit.ly/i9klJE except that the attributes are defined in
    # win32file not win32com (bug on page).
    # Note: For some reason this doesn't work after a os.chdir(), no matter to
    #       what directory you change from where. Windows weirdness.
    try:
        from win32file import FILE_ATTRIBUTE_HIDDEN, GetFileAttributesExW, error
        _have_win32file = True
    except ImportError:
        Logger.error('filechooser: win32file module is missing')
        Logger.error('filechooser: we cant check if a file is hidden or not')


def alphanumeric_folders_first(files, filesystem):
    return (sorted(f for f in files if filesystem.is_dir(f)) +
            sorted(f for f in files if not filesystem.is_dir(f)))


class FileSystemAbstract(object):
    '''Class for implementing a File System view that can be used with the
    :class:`FileChooser <FileChooser>`.

    .. versionadded:: 1.8.0
    '''

    def listdir(self, fn):
        '''Return the list of files in the directory `fn`
        '''
        pass

    def getsize(self, fn):
        '''Return the size in bytes of a file
        '''
        pass

    def is_hidden(self, fn):
        '''Return True if the file is hidden
        '''
        pass

    def is_dir(self, fn):
        '''Return True if the argument passed to this method is a directory
        '''
        pass


class FileSystemLocal(FileSystemAbstract):
    '''Implementation of :class:`FileSystemAbstract` for local files.

    .. versionadded:: 1.8.0
    '''

    def listdir(self, fn):
        return listdir(fn)

    def getsize(self, fn):
        return getsize(fn)

    def is_hidden(self, fn):
        if platform == 'win':
            if not _have_win32file:
                return False
            try:
                return GetFileAttributesExW(fn)[0] & FILE_ATTRIBUTE_HIDDEN
            except error:
                # This error can occurred when a file is already accessed by
                # someone else. So don't return to True, because we have lot
                # of chances to not being able to do anything with it.
                Logger.exception('unable to access to <%s>' % fn)
                return True

        return basename(fn).startswith('.')

    def is_dir(self, fn):
        return isdir(fn)


class FileChooserProgressBase(FloatLayout):
    '''Base for implementing a progress view. This view is used when too many
    entries need to be created and are delayed over multiple frames.

    .. versionadded:: 1.2.0
    '''

    path = StringProperty('')
    '''Current path of the FileChooser, read-only.
    '''

    index = NumericProperty(0)
    '''Current index of :attr:`total` entries to be loaded.
    '''

    total = NumericProperty(1)
    '''Total number of entries to load.
    '''

    def cancel(self, *largs):
        '''Cancel any action from the FileChooserController.
        '''
        if self.parent:
            self.parent.cancel()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            super(FileChooserProgressBase, self).on_touch_down(touch)
            return True

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            super(FileChooserProgressBase, self).on_touch_move(touch)
            return True

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            super(FileChooserProgressBase, self).on_touch_up(touch)
            return True


class FileChooserProgress(FileChooserProgressBase):
    pass


class FileChooserLayout(FloatLayout):
    '''Base class for file chooser layouts.

    .. versionadded:: 1.9.0
    '''

    VIEWNAME = 'undefined'

    __events__ = ('on_entry_added', 'on_entries_cleared',
                  'on_subentry_to_entry', 'on_remove_subentry', 'on_submit')

    controller = ObjectProperty()
    '''
    Reference to the controller handling this layout.

    :class:`~kivy.properties.ObjectProperty`
    '''

    def on_entry_added(self, node, parent=None):
        pass

    def on_entries_cleared(self):
        pass

    def on_subentry_to_entry(self, subentry, entry):
        pass

    def on_remove_subentry(self, subentry, entry):
        pass

    def on_submit(self, selected, touch=None):
        pass


class FileChooserListLayout(FileChooserLayout):
    '''File chooser layout using a list view.

    .. versionadded:: 1.9.0
    '''
    VIEWNAME = 'list'
    _ENTRY_TEMPLATE = 'FileListEntry'

    def __init__(self, **kwargs):
        super(FileChooserListLayout, self).__init__(**kwargs)
        self.fbind('on_entries_cleared', self.scroll_to_top)

    def scroll_to_top(self, *args):
        self.ids.scrollview.scroll_y = 1.0


class FileChooserIconLayout(FileChooserLayout):
    '''File chooser layout using an icon view.

    .. versionadded:: 1.9.0
    '''

    VIEWNAME = 'icon'
    _ENTRY_TEMPLATE = 'FileIconEntry'

    def __init__(self, **kwargs):
        super(FileChooserIconLayout, self).__init__(**kwargs)
        self.fbind('on_entries_cleared', self.scroll_to_top)

    def scroll_to_top(self, *args):
        self.ids.scrollview.scroll_y = 1.0


class FileChooserController(RelativeLayout):
    '''Base for implementing a FileChooser. Don't use this class directly, but
    prefer using an implementation such as the :class:`FileChooser`,
    :class:`FileChooserListView` or :class:`FileChooserIconView`.

    :Events:
        `on_entry_added`: entry, parent
            Fired when a root-level entry is added to the file list. If you
            return True from this event, the entry is not added to FileChooser.
        `on_entries_cleared`
            Fired when the the entries list is cleared, usually when the
            root is refreshed.
        `on_subentry_to_entry`: entry, parent
            Fired when a sub-entry is added to an existing entry or
            when entries are removed from an entry e.g. when
            a node is closed.
        `on_submit`: selection, touch
            Fired when a file has been selected with a double-tap.
    '''
    _ENTRY_TEMPLATE = None

    layout = ObjectProperty(baseclass=FileChooserLayout)
    '''
    Reference to the layout widget instance.

    layout is an :class:`~kivy.properties.ObjectProperty`.

    .. versionadded:: 1.9.0
    '''

    path = StringProperty(u'/')
    '''
    path is a :class:`~kivy.properties.StringProperty` and defaults to the
    current working directory as a unicode string. It specifies the path on the
    filesystem that this controller should refer to.

    .. warning::

        If a unicode path is specified, all the files returned will be in
        unicode, allowing the display of unicode files and paths. If a bytes
        path is specified, only files and paths with ascii names will be
        displayed properly: non-ascii filenames will be displayed and listed
        with questions marks (?) instead of their unicode characters.
    '''

    filters = ListProperty([])
    '''
    filters specifies the filters to be applied to the files in the directory.
    filters is a :class:`~kivy.properties.ListProperty` and defaults to []. This
    is equivalent to '\*' i.e. nothing is filtered.

    The filters are not reset when the path changes. You need to do that
    yourself if desired.

    There are two kinds of filters: patterns and callbacks.

    #. Patterns

        e.g. ['\*.png'].
        You can use the following patterns:

            ========== =================================
            Pattern     Meaning
            ========== =================================
            \*         matches everything
            ?          matches any single character
            [seq]      matches any character in seq
            [!seq]     matches any character not in seq
            ========== =================================

    #. Callbacks

        You can specify a function that will be called for each file. The
        callback will be passed the folder and file name as the first
        and second parameters respectively. It should return True to
        indicate a match and False otherwise.

    .. versionchanged:: 1.4.0
        Added the option to specify the filter as a callback.
    '''

    filter_dirs = BooleanProperty(False)
    '''
    Indicates whether filters should also apply to directories.
    filter_dirs is a :class:`~kivy.properties.BooleanProperty` and defaults to
    False.
    '''

    sort_func = ObjectProperty(alphanumeric_folders_first)
    '''
    Provides a function to be called with a list of filenames as the first
    argument and the filesystem implementation as the second argument. It
    returns a list of filenames sorted for display in the view.

    sort_func is an :class:`~kivy.properties.ObjectProperty` and defaults to a
    function returning alphanumerically named folders first.

    .. versionchanged:: 1.8.0

        The signature needs now 2 arguments: first the list of files,
        second the filesystem class to use.
    '''

    files = ListProperty([])
    '''
    The list of files in the directory specified by path after applying the
    filters.

    files is a read-only :class:`~kivy.properties.ListProperty`.
    '''

    show_hidden = BooleanProperty(False)
    '''
    Determines whether hidden files and folders should be shown.

    show_hidden is a :class:`~kivy.properties.BooleanProperty` and defaults to
    False.
    '''

    selection = ListProperty([])
    '''
    Contains the list of files that are currently selected.

    selection is a read-only :class:`~kivy.properties.ListProperty` and defaults
    to [].
    '''

    multiselect = BooleanProperty(False)
    '''
    Determines whether the user is able to select multiple files or not.

    multiselect is a :class:`~kivy.properties.BooleanProperty` and defaults to
    False.
    '''

    dirselect = BooleanProperty(False)
    '''
    Determines whether directories are valid selections or not.

    dirselect is a :class:`~kivy.properties.BooleanProperty` and defaults to
    False.

    .. versionadded:: 1.1.0
    '''

    rootpath = StringProperty(None, allownone=True)
    '''
    Root path to use instead of the system root path. If set, it will not show
    a ".." directory to go up to the root path. For example, if you set
    rootpath to /users/foo, the user will be unable to go to /users or to any
    other directory not starting with /users/foo.

    rootpath is a :class:`~kivy.properties.StringProperty` and defaults to None.

    .. versionadded:: 1.2.0

    .. note::

        Similarly to :attr:`path`, whether `rootpath` is specified as
        bytes or a unicode string determines the type of the filenames and paths
        read.
    '''

    progress_cls = ObjectProperty(FileChooserProgress)
    '''Class to use for displaying a progress indicator for filechooser
    loading.

    progress_cls is an :class:`~kivy.properties.ObjectProperty` and defaults to
    :class:`FileChooserProgress`.

    .. versionadded:: 1.2.0

    .. versionchanged:: 1.8.0

        If set to a string, the :class:`~kivy.factory.Factory` will be used to
        resolve the class name.

    '''

    file_encodings = ListProperty(['utf-8', 'latin1', 'cp1252'])
    '''Possible encodings for decoding a filename to unicode. In the case that
    the user has a non-ascii filename, undecodable without knowing it's
    initial encoding, we have no other choice than to guess it.

    Please note that if you encounter an issue because of a missing encoding
    here, we'll be glad to add it to this list.

    file_encodings is a :class:`~kivy.properties.ListProperty` and defaults to
    ['utf-8', 'latin1', 'cp1252'].

    .. versionadded:: 1.3.0

    .. deprecated:: 1.8.0
       This property is no longer used as the filechooser no longer decodes
       the file names.

    '''

    file_system = ObjectProperty(FileSystemLocal(),
                                 baseclass=FileSystemAbstract)
    '''The file system object used to access the file system. This should be a
    subclass of :class:`FileSystemAbstract`.

    file_system is an :class:`~kivy.properties.ObjectProperty` and defaults to
    :class:`FileSystemLocal()`

    .. versionadded:: 1.8.0
    '''

    _update_files_ev = None
    _create_files_entries_ev = None

    __events__ = ('on_entry_added', 'on_entries_cleared',
                  'on_subentry_to_entry', 'on_remove_subentry', 'on_submit')

    def __init__(self, **kwargs):
        self._progress = None
        super(FileChooserController, self).__init__(**kwargs)

        self._items = []
        fbind = self.fbind
        fbind('selection', self._update_item_selection)

        self._previous_path = [self.path]
        fbind('path', self._save_previous_path)
        update = self._trigger_update
        fbind('path', update)
        fbind('filters', update)
        fbind('rootpath', update)
        update()

    def on_touch_down(self, touch):
        # don't respond to touchs outside self
        if not self.collide_point(*touch.pos):
            return
        if self.disabled:
            return True
        return super(FileChooserController, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        # don't respond to touchs outside self
        if not self.collide_point(*touch.pos):
            return
        if self.disabled:
            return True
        return super(FileChooserController, self).on_touch_up(touch)

    def _update_item_selection(self, *args):
        for item in self._items:
            item.selected = item.path in self.selection

    def _save_previous_path(self, instance, value):
        self._previous_path.append(value)
        self._previous_path = self._previous_path[-2:]

    def _trigger_update(self, *args):
        ev = self._update_files_ev
        if ev is None:
            ev = self._update_files_ev = Clock.create_trigger(
                self._update_files)
        ev()

    def on_entry_added(self, node, parent=None):
        if self.layout:
            self.layout.dispatch('on_entry_added', node, parent)

    def on_entries_cleared(self):
        if self.layout:
            self.layout.dispatch('on_entries_cleared')

    def on_subentry_to_entry(self, subentry, entry):
        if self.layout:
            self.layout.dispatch('on_subentry_to_entry', subentry, entry)

    def on_remove_subentry(self, subentry, entry):
        if self.layout:
            self.layout.dispatch('on_remove_subentry', subentry, entry)

    def on_submit(self, selected, touch=None):
        if self.layout:
            self.layout.dispatch('on_submit', selected, touch)

    def entry_touched(self, entry, touch):
        '''(internal) This method must be called by the template when an entry
        is touched by the user.
        '''
        if (
            'button' in touch.profile and touch.button in (
                'scrollup', 'scrolldown', 'scrollleft', 'scrollright')):
            return False

        _dir = self.file_system.is_dir(entry.path)
        dirselect = self.dirselect

        if _dir and dirselect and touch.is_double_tap:
            self.open_entry(entry)
            return

        if self.multiselect:
            if entry.path in self.selection:
                self.selection.remove(entry.path)
            else:
                if _dir and not self.dirselect:
                    self.open_entry(entry)
                    return
                self.selection.append(entry.path)
        else:
            if _dir and not self.dirselect:
                return
            self.selection = [abspath(join(self.path, entry.path)), ]

    def entry_released(self, entry, touch):
        '''(internal) This method must be called by the template when an entry
        is touched by the user.

        .. versionadded:: 1.1.0
        '''
        if (
            'button' in touch.profile and touch.button in (
                'scrollup', 'scrolldown', 'scrollleft', 'scrollright')):
            return False
        if not self.multiselect:
            if self.file_system.is_dir(entry.path) and not self.dirselect:
                self.open_entry(entry)
            elif touch.is_double_tap:
                if self.dirselect and self.file_system.is_dir(entry.path):
                    return
                else:
                    self.dispatch('on_submit', self.selection, touch)

    def open_entry(self, entry):
        try:
            # Just check if we can list the directory. This is also what
            # _add_file does, so if it fails here, it would also fail later
            # on. Do the check here to prevent setting path to an invalid
            # directory that we cannot list.
            self.file_system.listdir(entry.path)
        except OSError:
            entry.locked = True
        else:
            # If entry.path is to jump to previous directory, update path with
            # parent directory
            self.path = abspath(join(self.path, entry.path))
            self.selection = [self.path, ] if self.dirselect else []

    def _apply_filters(self, files):
        if not self.filters:
            return files
        filtered = []
        for filt in self.filters:
            if isinstance(filt, collections.Callable):
                filtered.extend([fn for fn in files if filt(self.path, fn)])
            else:
                filtered.extend([fn for fn in files if fnmatch(fn, filt)])
        if not self.filter_dirs:
            dirs = [fn for fn in files if self.file_system.is_dir(fn)]
            filtered.extend(dirs)
        return list(set(filtered))

    def get_nice_size(self, fn):
        '''Pass the filepath. Returns the size in the best human readable
        format or '' if it is a directory (Don't recursively calculate size).
        '''
        if self.file_system.is_dir(fn):
            return ''
        try:
            size = self.file_system.getsize(fn)
        except OSError:
            return '--'

        for unit in filesize_units:
            if size < 1024.0:
                return '%1.0f %s' % (size, unit)
            size /= 1024.0

    def _update_files(self, *args, **kwargs):
        # trigger to start gathering the files in the new directory
        # we'll start a timer that will do the job, 10 times per frames
        # (default)
        self._gitems = []
        self._gitems_parent = kwargs.get('parent', None)
        self._gitems_gen = self._generate_file_entries(
            path=kwargs.get('path', self.path),
            parent=self._gitems_parent)

        # cancel any previous clock if exist
        ev = self._create_files_entries_ev
        if ev is not None:
            ev.cancel()

        # show the progression screen
        self._hide_progress()
        if self._create_files_entries():
            # not enough for creating all the entries, all a clock to continue
            # start a timer for the next 100 ms
            if ev is None:
                ev = self._create_files_entries_ev = Clock.schedule_interval(
                    self._create_files_entries, .1)
            ev()

    def _get_file_paths(self, items):
        return [file.path for file in items]

    def _create_files_entries(self, *args):
        # create maximum entries during 50ms max, or 10 minimum (slow system)
        # (on a "fast system" (core i7 2700K), we can create up to 40 entries
        # in 50 ms. So 10 is fine for low system.
        start = time()
        finished = False
        index = total = count = 1
        while time() - start < 0.05 or count < 10:
            try:
                index, total, item = next(self._gitems_gen)
                self._gitems.append(item)
                count += 1
            except StopIteration:
                finished = True
                break
            except TypeError:  # in case _gitems_gen is None
                finished = True
                break

        # if this wasn't enough for creating all the entries, show a progress
        # bar, and report the activity to the user.
        if not finished:
            self._show_progress()
            self._progress.total = total
            self._progress.index = index
            return True

        # we created all the files, now push them on the view
        self._items = items = self._gitems
        parent = self._gitems_parent
        if parent is None:
            self.dispatch('on_entries_cleared')
            for entry in items:
                self.dispatch('on_entry_added', entry, parent)
        else:
            parent.entries[:] = items
            for entry in items:
                self.dispatch('on_subentry_to_entry', entry, parent)
        self.files[:] = self._get_file_paths(items)

        # stop the progression / creation
        self._hide_progress()
        self._gitems = None
        self._gitems_gen = None
        ev = self._create_files_entries_ev
        if ev is not None:
            ev.cancel()
        return False

    def cancel(self, *largs):
        '''Cancel any background action started by filechooser, such as loading
        a new directory.

        .. versionadded:: 1.2.0
        '''
        ev = self._create_files_entries_ev
        if ev is not None:
            ev.cancel()

        self._hide_progress()
        if len(self._previous_path) > 1:
            # if we cancel any action, the path will be set same as the
            # previous one, so we can safely cancel the update of the previous
            # path.
            self.path = self._previous_path[-2]

            ev = self._update_files_ev
            if ev is not None:
                ev.cancel()

    def _show_progress(self):
        if self._progress:
            return
        cls = self.progress_cls
        if isinstance(cls, string_types):
            cls = Factory.get(cls)
        self._progress = cls(path=self.path)
        self._progress.value = 0
        self.add_widget(self._progress)

    def _hide_progress(self):
        if self._progress:
            self.remove_widget(self._progress)
            self._progress = None

    def _generate_file_entries(self, *args, **kwargs):
        # Generator that will create all the files entries.
        # the generator is used via _update_files() and _create_files_entries()
        # don't use it directly.
        is_root = False
        path = kwargs.get('path', self.path)
        have_parent = kwargs.get('parent', None) is not None

        # Add the components that are always needed
        if self.rootpath:
            rootpath = realpath(self.rootpath)
            path = realpath(path)
            if not path.startswith(rootpath):
                self.path = rootpath
                return
            elif path == rootpath:
                is_root = True
        else:
            if platform == 'win':
                is_root = splitdrive(path)[1] in (sep, altsep)
            elif platform in ('macosx', 'linux', 'android', 'ios'):
                is_root = normpath(expanduser(path)) == sep
            else:
                # Unknown fs, just always add the .. entry but also log
                Logger.warning('Filechooser: Unsupported OS: %r' % platform)
        # generate an entries to go back to previous
        if not is_root and not have_parent:
            back = '..' + sep
            pardir = self._create_entry_widget(dict(
                name=back, size='', path=back, controller=ref(self),
                isdir=True, parent=None, sep=sep, get_nice_size=lambda: ''))
            yield 0, 1, pardir

        # generate all the entries for files
        try:
            for index, total, item in self._add_files(path):
                yield index, total, item
        except OSError:
            Logger.exception('Unable to open directory <%s>' % self.path)
            self.files[:] = []

    def _create_entry_widget(self, ctx):
        template = self.layout._ENTRY_TEMPLATE\
            if self.layout else self._ENTRY_TEMPLATE
        return Builder.template(template, **ctx)

    def _add_files(self, path, parent=None):
        path = expanduser(path)

        files = []
        fappend = files.append
        for f in self.file_system.listdir(path):
            try:
                # In the following, use fully qualified filenames
                fappend(normpath(join(path, f)))
            except UnicodeDecodeError:
                Logger.exception('unable to decode <{}>'.format(f))
            except UnicodeEncodeError:
                Logger.exception('unable to encode <{}>'.format(f))
        # Apply filename filters
        files = self._apply_filters(files)
        # Sort the list of files
        files = self.sort_func(files, self.file_system)
        is_hidden = self.file_system.is_hidden
        if not self.show_hidden:
            files = [x for x in files if not is_hidden(x)]
        self.files[:] = files
        total = len(files)
        wself = ref(self)
        for index, fn in enumerate(files):

            def get_nice_size():
                # Use a closure for lazy-loading here
                return self.get_nice_size(fn)

            ctx = {'name': basename(fn),
                   'get_nice_size': get_nice_size,
                   'path': fn,
                   'controller': wself,
                   'isdir': self.file_system.is_dir(fn),
                   'parent': parent,
                   'sep': sep}
            entry = self._create_entry_widget(ctx)
            yield index, total, entry

    def entry_subselect(self, entry):
        if not self.file_system.is_dir(entry.path):
            return
        self._update_files(path=entry.path, parent=entry)

    def close_subselection(self, entry):
        for subentry in entry.entries:
            self.dispatch('on_remove_subentry', subentry, entry)


class FileChooserListView(FileChooserController):
    '''Implementation of a :class:`FileChooserController` using a list view.

    .. versionadded:: 1.9.0
    '''
    _ENTRY_TEMPLATE = 'FileListEntry'


class FileChooserIconView(FileChooserController):
    '''Implementation of a :class:`FileChooserController` using an icon view.

    .. versionadded:: 1.9.0
    '''
    _ENTRY_TEMPLATE = 'FileIconEntry'


class FileChooser(FileChooserController):
    '''Implementation of a :class:`FileChooserController` which supports
    switching between multiple, synced layout views.

    The FileChooser can be used as follows:

    .. code-block:: kv

        BoxLayout:
            orientation: 'vertical'

            BoxLayout:
                size_hint_y: None
                height: sp(52)

                Button:
                    text: 'Icon View'
                    on_press: fc.view_mode = 'icon'
                Button:
                    text: 'List View'
                    on_press: fc.view_mode = 'list'

            FileChooser:
                id: fc
                FileChooserIconLayout
                FileChooserListLayout

    .. versionadded:: 1.9.0
    '''

    manager = ObjectProperty()
    '''
    Reference to the :class:`~kivy.uix.screenmanager.ScreenManager` instance.

    manager is an :class:`~kivy.properties.ObjectProperty`.
    '''

    _view_list = ListProperty()

    def get_view_list(self):
        return self._view_list

    view_list = AliasProperty(get_view_list, bind=('_view_list',))
    '''
    List of views added to this FileChooser.

    view_list is an :class:`~kivy.properties.AliasProperty` of type
    :class:`list`.
    '''

    _view_mode = StringProperty()

    def get_view_mode(self):
        return self._view_mode

    def set_view_mode(self, mode):
        if mode not in self._view_list:
            raise ValueError('unknown view mode %r' % mode)
        self._view_mode = mode

    view_mode = AliasProperty(
        get_view_mode, set_view_mode, bind=('_view_mode',))
    '''
    Current layout view mode.

    view_mode is an :class:`~kivy.properties.AliasProperty` of type
    :class:`str`.
    '''

    @property
    def _views(self):
        return [screen.children[0] for screen in self.manager.screens]

    def __init__(self, **kwargs):
        super(FileChooser, self).__init__(**kwargs)

        self.manager = ScreenManager()
        super(FileChooser, self).add_widget(self.manager)

        self.trigger_update_view = Clock.create_trigger(self.update_view)

        self.fbind('view_mode', self.trigger_update_view)

    def add_widget(self, widget, **kwargs):
        if widget is self._progress:
            super(FileChooser, self).add_widget(widget, **kwargs)
        elif hasattr(widget, 'VIEWNAME'):
            name = widget.VIEWNAME + 'view'
            screen = Screen(name=name)
            widget.controller = self
            screen.add_widget(widget)
            self.manager.add_widget(screen)

            self.trigger_update_view()
        else:
            raise ValueError(
                'widget must be a FileChooserLayout,'
                ' not %s' % type(widget).__name__)

    def rebuild_views(self):
        views = [view.VIEWNAME for view in self._views]
        if views != self._view_list:
            self._view_list = views
            if self._view_mode not in self._view_list:
                self._view_mode = self._view_list[0]
            self._trigger_update()

    def update_view(self, *args):
        self.rebuild_views()

        sm = self.manager
        viewlist = self._view_list
        view = self.view_mode
        current = sm.current[:-4]

        viewindex = viewlist.index(view) if view in viewlist else 0
        currentindex = viewlist.index(current) if current in viewlist else 0

        direction = 'left' if currentindex < viewindex else 'right'

        sm.transition.direction = direction
        sm.current = view + 'view'

    def _create_entry_widget(self, ctx):
        return [Builder.template(view._ENTRY_TEMPLATE, **ctx)
                for view in self._views]

    def _get_file_paths(self, items):
        if self._views:
            return [file[0].path for file in items]
        return []

    def _update_item_selection(self, *args):
        for viewitem in self._items:
            selected = viewitem[0].path in self.selection
            for item in viewitem:
                item.selected = selected

    def on_entry_added(self, node, parent=None):
        for index, view in enumerate(self._views):
            view.dispatch(
                'on_entry_added',
                node[index], parent[index] if parent else None)

    def on_entries_cleared(self):
        for view in self._views:
            view.dispatch('on_entries_cleared')

    def on_subentry_to_entry(self, subentry, entry):
        for index, view in enumerate(self._views):
            view.dispatch('on_subentry_to_entry', subentry[index], entry)

    def on_remove_subentry(self, subentry, entry):
        for index, view in enumerate(self._views):
            view.dispatch('on_remove_subentry', subentry[index], entry)

    def on_submit(self, selected, touch=None):
        view_mode = self.view_mode
        for view in self._views:
            if view_mode == view.VIEWNAME:
                view.dispatch('on_submit', selected, touch)
                return


if __name__ == '__main__':
    from kivy.app import App
    from pprint import pprint
    import textwrap
    import sys

    root = Builder.load_string(textwrap.dedent('''\
    BoxLayout:
        orientation: 'vertical'

        BoxLayout:
            size_hint_y: None
            height: sp(52)

            Button:
                text: 'Icon View'
                on_press: fc.view_mode = 'icon'
            Button:
                text: 'List View'
                on_press: fc.view_mode = 'list'

        FileChooser:
            id: fc

            FileChooserIconLayout
            FileChooserListLayout
    '''))

    class FileChooserApp(App):

        def build(self):
            v = root.ids.fc
            if len(sys.argv) > 1:
                v.path = sys.argv[1]

            v.bind(selection=lambda *x: pprint("selection: %s" % x[1:]))
            v.bind(path=lambda *x: pprint("path: %s" % x[1:]))

            return root

    FileChooserApp().run()
