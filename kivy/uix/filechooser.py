'''
FileChooser
===========

.. versionadded:: 1.0.5

.. warning::

    This is experimental and subject to change as long as this warning notice
    is present.

.. versionchanged:: 1.2.0
    In chooser template, the `controller` is not a direct reference anymore,
    but a weak-reference.
    You must update all the notation `root.controller.xxx` to
    `root.controller().xxx`.

Simple example
--------------

main.py

.. include:: ../../examples/RST_Editor/main.py
    :literal:

editor.kv

.. highlight:: kv

.. include:: ../../examples/RST_Editor/editor.kv
    :literal:

'''

__all__ = ('FileChooserListView', 'FileChooserIconView',
           'FileChooserController', 'FileChooserProgressBase')

from weakref import ref
from time import time
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.utils import platform as core_platform
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import (
    StringProperty, ListProperty, BooleanProperty, ObjectProperty,
    NumericProperty)
from os import listdir
from os.path import (
    basename, getsize, isdir, join, sep, normpath, expanduser, altsep,
    splitdrive, realpath)
from fnmatch import fnmatch

platform = core_platform()
filesize_units = ('B', 'KB', 'MB', 'GB', 'TB')

_have_win32file = False
if platform == 'win':
    # Import that module here as it's not available on non-windows machines.
    # See http://bit.ly/i9klJE except that the attributes are defined in
    # win32file not win32com (bug on page).
    # Note: For some reason this doesn't work after a os.chdir(), no matter to
    #       what directory you change from where. Windows weirdness.
    try:
        from win32file import FILE_ATTRIBUTE_HIDDEN, GetFileAttributesEx, error
        _have_win32file = True
    except ImportError:
        Logger.error('filechooser: win32file module is missing')
        Logger.error('filechooser: we cant check if a file is hidden or not')


def is_hidden_unix(fn):
    return basename(fn).startswith('.')


def is_hidden_win(fn):
    if not _have_win32file:
        return False
    try:
        return GetFileAttributesEx(fn)[0] & FILE_ATTRIBUTE_HIDDEN
    except error:
        # This error can occured when a file is already accessed by someone
        # else. So don't return to True, because we have lot of chances to not
        # being able to do anything with it.
        Logger.exception('unable to access to <%s>' % fn)
        return True


def alphanumeric_folders_first(files):
    return (sorted(f for f in files if isdir(f)) +
            sorted(f for f in files if not isdir(f)))


class ForceUnicodeError(Exception):
    pass


class FileChooserProgressBase(FloatLayout):
    '''Base for implementing a progress view. This view is used when too many
    entries need to be created, and are delayed over multiple frames.

    .. versionadded:: 1.2.0
    '''

    path = StringProperty('')
    '''Current path of the FileChooser, read-only.
    '''

    index = NumericProperty(0)
    '''Current index of :data:`total` entries to be loaded.
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


class FileChooserController(FloatLayout):
    '''Base for implementing a FileChooser. Don't use that class directly,
    preferring to use an implementation like :class:`FileChooserListView` or
    :class:`FileChooserIconView`.

    :Events:
        `on_entry_added`: entry, parent
            Fired when a root-level entry is added to the file list.
        `on_entries_cleared`
            Fired when the the entries list is cleared. Usally when the
            root is refreshed.
        `on_subentry_to_entry`: entry, parent
            Fired when a sub-entry is added to an existing entry.
        `on_remove_subentry`: entry, parent
            Fired when entries are removed from an entry. Usually when
            a node is closed.
        `on_submit`: selection, touch
            Fired when a file has been selected with a double-tap.
    '''
    _ENTRY_TEMPLATE = None

    path = StringProperty(u'/')
    '''
    :class:`~kivy.properties.StringProperty`, defaults to current working
    directory as unicode string. Specifies the path on the filesystem that
    this controller should refer to.
    '''

    filters = ListProperty([])
    ''':class:`~kivy.properties.ListProperty`, defaults to [], equal to '\*'.
    The filters to be applied to the files in the directory.

    The filters are not reset when the path changes. You need to do that
    yourself if desired.

    There are two kinds of filters :

    filename patterns : e.g. ['\*.png'].
    You can use the following patterns:

        ========== =================================
        Pattern     Meaning
        ========== =================================
        \*         matches everything
        ?          matches any single character
        [seq]      matches any character in seq
        [!seq]     matches any character not in seq
        ========== =================================

    .. versionchanged:: 1.4.0
        if the filter is a callable (function or method). It will be called
        with the path and the file name as arguments for each file in dir. The
        callable should returns True to indicate a match and False overwise.
    '''

    filter_dirs = BooleanProperty(False)
    '''
    :class:`~kivy.properties.BooleanProperty`, defaults to False.
    Indicates whether filters should also apply to directories.
    '''

    sort_func = ObjectProperty(alphanumeric_folders_first)
    '''
    :class:`~kivy.properties.ObjectProperty`.
    Provides a function to be called with a list of filenames as the only
    argument.  Returns a list of filenames sorted for display in the view.
    '''

    files = ListProperty([])
    '''
    Read-only :class:`~kivy.properties.ListProperty`.
    The list of files in the directory specified by path after applying the
    filters.
    '''

    show_hidden = BooleanProperty(False)
    '''
    :class:`~kivy.properties.BooleanProperty`, defaults to False.
    Determines whether hidden files and folders should be shown.
    '''

    selection = ListProperty([])
    '''
    Read-only :class:`~kivy.properties.ListProperty`.
    The list of files that are currently selected.
    '''

    multiselect = BooleanProperty(False)
    '''
    :class:`~kivy.properties.BooleanProperty`, defaults to False.
    Determines whether user is able to select multiple files.
    '''

    dirselect = BooleanProperty(False)
    '''
    :class:`~kivy.properties.BooleanProperty`, defaults to False.
    Determines whether directories are valid selections.

    .. versionadded:: 1.1.0
    '''

    rootpath = StringProperty(None, allownone=True)
    '''
    Root path to use, instead of the system root path. If set, it will not show
    a ".." directory to go upper the root path. For example, if you set
    rootpath to /Users/foo, the user will be unable to go to /Users, or to any
    other directory not starting with /Users/foo.

    .. versionadded:: 1.2.0

    :class:`~kivy.properties.StringProperty`, defaults to None.
    '''

    progress_cls = ObjectProperty(FileChooserProgress)
    '''Class to use for displaying a progress indicator for filechooser loading

    .. versionadded:: 1.2.0

    :class:`~kivy.properties.ObjectProperty`, defaults to
    :class:`FileChooserProgress`
    '''

    file_encodings = ListProperty(['utf-8', 'latin1', 'cp1252'])
    '''Possible encodings for decoding a filename to unicode. In the case that
    the user has a weird filename, undecodable without knowing it's
    initial encoding, we have no other choice than to guess it.

    Please note that if you encounter an issue because of a missing encoding
    here, we'll be glad to add it to this list.

    .. versionadded:: 1.3.0

    :class:`~kivy.properties.ListProperty`, defaults to ['utf-8', 'latin1',
    'cp1252']
    '''

    def __init__(self, **kwargs):
        self.register_event_type('on_entry_added')
        self.register_event_type('on_entries_cleared')
        self.register_event_type('on_subentry_to_entry')
        self.register_event_type('on_remove_subentry')
        self.register_event_type('on_submit')
        self._progress = None
        super(FileChooserController, self).__init__(**kwargs)

        self._items = []
        self.bind(selection=self._update_item_selection)

        if platform in ('macosx', 'linux', 'android', 'ios'):
            self.is_hidden = is_hidden_unix
        elif platform == 'win':
            self.is_hidden = is_hidden_win
        else:
            raise NotImplementedError('Only available for Linux, OSX and Win'
                                      ' (platform is %r)' % platform)

        self._previous_path = [self.path]
        self.bind(path=self._save_previous_path)
        self.bind(path=self._trigger_update,
                  filters=self._trigger_update,
                  rootpath=self._trigger_update)
        self._trigger_update()

    def _update_item_selection(self, *args):
        for item in self._items:
            item.selected = item.path in self.selection

    def _save_previous_path(self, instance, value):
        path = expanduser(value)
        path = realpath(path)
        if path != value:
            self.path = path
            return
        self._previous_path.append(value)
        self._previous_path = self._previous_path[-2:]

    def _trigger_update(self, *args):
        Clock.unschedule(self._update_files)
        Clock.schedule_once(self._update_files)

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

    def entry_touched(self, entry, touch):
        '''(internal) This method must be called by the template when an entry
        is touched by the user.
        '''
        if (
            'button' in touch.profile and touch.button in (
                'scrollup', 'scrolldown')
        ):
            return False
        if self.multiselect:
            if isdir(entry.path) and touch.is_double_tap:
                self.open_entry(entry)
            else:
                if entry.path in self.selection:
                    self.selection.remove(entry.path)
                else:
                    self.selection.append(entry.path)
        else:
            if isdir(entry.path):
                if self.dirselect:
                    self.selection = [entry.path, ]
            else:
                self.selection = [entry.path, ]

    def entry_released(self, entry, touch):
        '''(internal) This method must be called by the template when an entry
        is touched by the user.

        .. versionadded:: 1.1.0
        '''
        if (
            'button' in touch.profile and touch.button in (
            'scrollup', 'scrolldown')
        ):
            return False
        if not self.multiselect:
            if isdir(entry.path) and not self.dirselect:
                self.open_entry(entry)
            elif touch.is_double_tap:
                if self.dirselect and isdir(entry.path):
                    self.open_entry(entry)
                else:
                    self.dispatch('on_submit', self.selection, touch)

    def open_entry(self, entry):
        try:
            # Just check if we can list the directory. This is also what
            # _add_file does, so if it fails here, it would also fail later
            # on. Do the check here to prevent setting path to an invalid
            # directory that we cannot list.
            try:
                path = entry.path.decode('utf-8')
            except UnicodeEncodeError:
                path = entry.path
                pass
            listdir(path)
        except OSError:
            #Logger.exception(e)
            entry.locked = True
        else:
            self.path = join(self.path, entry.path)
            self.selection = []

    def _apply_filters(self, files):
        if not self.filters:
            return files
        filtered = []
        for filter in self.filters:
            if callable(filter):
                filtered.extend([fn for fn in files if filter(self.path, fn)])
            else:
                filtered.extend([fn for fn in files if fnmatch(fn, filter)])
        if not self.filter_dirs:
            dirs = [fn for fn in files if isdir(fn)]
            filtered.extend(dirs)
        return list(set(filtered))

    def get_nice_size(self, fn):
        '''Pass the filepath. Returns the size in the best human readable
        format or '' if it is a directory (Don't recursively calculate size.).
        '''
        if isdir(fn):
            return ''
        try:
            size = getsize(fn)
        except OSError:
            #Logger.exception(e)
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
        Clock.unschedule(self._create_files_entries)

        # show the progression screen
        self._hide_progress()
        if self._create_files_entries():
            # not enough for creating all the entries, all a clock to continue
            # start a timer for the next 100 ms
            Clock.schedule_interval(self._create_files_entries, .1)

    def _create_files_entries(self, *args):
        # create maximum entries during 50ms max, or 10 minimum (slow system)
        # (on a "fast system" (core i7 2700K), we can create up to 40 entries
        # in 50 ms. So 10 is fine for low system.
        start = time()
        finished = False
        index = total = count = 1
        while time() - start < 0.05 or count < 10:
            try:
                index, total, item = self._gitems_gen.next()
                self._gitems.append(item)
                count += 1
            except StopIteration:
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

        # stop the progression / creation
        self._hide_progress()
        self._gitems = None
        self._gitems_gen = None
        Clock.unschedule(self._create_files_entries)
        return False

    def cancel(self, *largs):
        '''Cancel any background action started by filechooser, such as loading
        a new directory.

        .. versionadded:: 1.2.0
        '''
        Clock.unschedule(self._create_files_entries)
        self._hide_progress()
        if len(self._previous_path) > 1:
            # if we cancel any action, the path will be set same as the
            # previous one, so we can safely cancel the update of the previous
            # path.
            self.path = self._previous_path[-2]
            Clock.unschedule(self._update_files)

    def _show_progress(self):
        if self._progress:
            return
        self._progress = self.progress_cls(path=self.path)
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
        is_root = True
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
                is_root = False
        # generate an entries to go back to previous
        if not is_root and not have_parent:
            back = '..' + sep
            pardir = Builder.template(self._ENTRY_TEMPLATE, **dict(
                name=back, size='', path=back, controller=ref(self),
                isdir=True, parent=None, sep=sep, get_nice_size=lambda: ''))
            yield 0, 1, pardir

        # generate all the entries for files
        try:
            for index, total, item in self._add_files(path):
                yield index, total, item
        except OSError:
            Logger.exception('Unable to open directory <%s>' % self.path)

    def _add_files(self, path, parent=None):
        force_unicode = self._force_unicode
        # Make sure we're using unicode in case of non-ascii chars in
        # filenames.  listdir() returns unicode if you pass it unicode.
        try:
            path = expanduser(path)
            path = force_unicode(path)
        except ForceUnicodeError:
            pass

        files = []
        fappend = files.append
        for fn in listdir(path):
            try:
                fappend(force_unicode(fn))
            except ForceUnicodeError:
                pass
        # In the following, use fully qualified filenames
        files = [normpath(join(path, f)) for f in files]
        # Apply filename filters
        files = self._apply_filters(files)
        # Sort the list of files
        files = self.sort_func(files)
        is_hidden = self.is_hidden
        if not self.show_hidden:
            files = [x for x in files if not is_hidden(x)]
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
                   'isdir': isdir(fn),
                   'parent': parent,
                   'sep': sep}
            entry = Builder.template(self._ENTRY_TEMPLATE, **ctx)
            yield index, total, entry

    def _force_unicode(self, s):
        # the idea is, whatever is the filename, unicode or str, even if the
        # str can't be directly returned as a unicode, return something.
        if type(s) is unicode:
            return s
        encodings = self.file_encodings
        for encoding in encodings:
            try:
                return s.decode(encoding, 'strict')
            except UnicodeDecodeError:
                pass
            except UnicodeEncodeError:
                pass
        raise ForceUnicodeError('Unable to decode %r' % s)

    def entry_subselect(self, entry):
        if not isdir(entry.path):
            return
        self._update_files(path=entry.path, parent=entry)

    def close_subselection(self, entry):
        for subentry in entry.entries:
            self.dispatch('on_remove_subentry', subentry, entry)


class FileChooserListView(FileChooserController):
    '''Implementation of :class:`FileChooserController` using a list view.
    '''
    _ENTRY_TEMPLATE = 'FileListEntry'


class FileChooserIconView(FileChooserController):
    '''Implementation of :class:`FileChooserController` using an icon view.
    '''
    _ENTRY_TEMPLATE = 'FileIconEntry'


if __name__ == '__main__':
    from kivy.app import App
    from pprint import pprint
    import sys

    class FileChooserApp(App):

        def build(self):
            view = FileChooserListView

            if len(sys.argv) > 1:
                v = view(path=sys.argv[1])
            else:
                v = view()

            v.bind(selection=lambda *x: pprint("selection: %s" % x[1:]))
            v.bind(path=lambda *x: pprint("path: %s" % x[1:]))
            return v

    FileChooserApp().run()
