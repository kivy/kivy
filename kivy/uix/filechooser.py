'''
FileChooser
===========

.. versionadded:: 1.0.5

.. warning::

    This is experimental and subject to change as long as this warning notice is
    present.
'''


from kivy.clock import Clock
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.utils import platform as core_platform
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty, ListProperty, BooleanProperty, \
                            ObjectProperty
from os import listdir
from os.path import basename, getsize, isdir, join, sep, normpath, \
                    expanduser, altsep, splitdrive
from fnmatch import fnmatch

platform = core_platform()

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
        pass


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
    return sorted(f for f in files if isdir(f)) + \
           sorted(f for f in files if not isdir(f))


class FileChooserController(FloatLayout):
    '''Base for implementing a FileChooser. Don't use that class directly,
    prefer to use one implementation like :class:`FileChooserListView` or
    :class:`FileChooserIconView`.
    '''
    _ENTRY_TEMPLATE = None

    path = StringProperty(u'/')
    '''
    :class:`~kivy.properties.StringProperty`, defaults to current working
    directory as unicode string. Specifies the path on the filesystem that
    this controller should look at.
    '''

    filters = ListProperty([])
    ''':class:`~kivy.properties.ListProperty`, defaults to [], equal to '\*'.
    The filters to be applied to the files in the directory, e.g. ['\*.png'].
    The filters are not reset when the path changes, you need to do that
    yourself if you want that. You can use the following patterns:

      ========== =================================
      Pattern     Meaning
      ========== =================================
      \*         matches everything
      ?          matches any single character
      [seq]      matches any character in seq
      [!seq]     matches any character not in seq
      ========== =================================

    '''

    filter_dirs = BooleanProperty(False)
    '''
    :class:`~kivy.properties.BooleanProperty`, defaults to False.
    Indicate whether filters should also apply to directories.
    '''

    sort_func = ObjectProperty(alphanumeric_folders_first)
    '''
    :class:`~kivy.properties.ObjectProperty`.
    Provide a function to be called with a list of filenames as only argument.
    Return a list of filenames in such a manner that the new list is sorted and
    represents in which order files are supposed to be displayed in the view.
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

    def __init__(self, **kwargs):
        self.register_event_type('on_entry_added')
        self.register_event_type('on_entries_cleared')
        self.register_event_type('on_subentry_to_entry')
        self.register_event_type('on_remove_subentry')
        self.register_event_type('on_submit')
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

        self.bind(path=self._trigger_update,
                  filters=self._trigger_update)
        self._trigger_update()

    def _update_item_selection(self, *args):
        for item in self._items:
            item.selected = item.path in self.selection

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
        if self.multiselect:
            pass
        else:
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
            listdir(unicode(entry.path))
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
            filtered.extend([fn for fn in files if fnmatch(fn, filter)])
        if not self.filter_dirs:
            dirs = [fn for fn in files if isdir(fn)]
            filtered.extend(dirs)
        return list(set(filtered))

    def get_nice_size(self, fn):
        '''
        Pass the filepath. Returns the size in the best human readable
        format or '' if it's a directory (Don't recursively calculate size.).
        '''
        if isdir(fn):
            return ''
        try:
            size = getsize(fn)
        except OSError:
            #Logger.exception(e)
            return '--'

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return "%1.0f %s" % (size, unit)
            size /= 1024.0

    def _update_files(self, *args):
        # Clear current files
        self.dispatch('on_entries_cleared')
        self._items = []

        # Add the components that are always needed
        if platform == 'win':
            is_root = splitdrive(self.path)[1] in (sep, altsep)
        elif platform in ('macosx', 'linux', 'android', 'ios'):
            is_root = normpath(expanduser(self.path)) == sep
        else:
            # Unknown file system; Just always add the .. entry but also log
            Logger.warning('Filechooser: Unsupported OS: %r' % platform)
            is_root = False
        if not is_root:
            back = '..' + sep
            pardir = Builder.template(self._ENTRY_TEMPLATE, **dict(name=back,
                size='', path=back, controller=self, isdir=True, parent=None,
                sep=sep, get_nice_size=lambda: ''))
            self._items.append(pardir)
            self.dispatch('on_entry_added', pardir)
        try:
            self._add_files(self.path)
        except OSError:
            Logger.exception('Unable to open directory <%s>' % self.path)

    def _add_files(self, path, parent=None):
        path = expanduser(path)
        # Make sure we're using unicode in case of non-ascii chars in filenames.
        # listdir() returns unicode if you pass it unicode.
        files = listdir(unicode(path))
        # In the following, use fully qualified filenames
        files = [normpath(join(path, f)) for f in files]
        # Apply filename filters
        files = self._apply_filters(files)
        # Sort the list of files
        files = self.sort_func(files)
        # Add the files
        if parent:
            parent.entries = []
        is_hidden = self.is_hidden
        if not self.show_hidden:
            files = [x for x in files if not is_hidden(x)]
        for fn in files:

            def get_nice_size():
                # Use a closure for lazy-loading here
                return self.get_nice_size(fn)

            ctx = {'name': basename(fn),
                   'get_nice_size': get_nice_size,
                   'path': fn,
                   'controller': self,
                   'isdir': isdir(fn),
                   'parent': parent,
                   'sep': sep}
            entry = Builder.template(self._ENTRY_TEMPLATE, **ctx)
            if not parent:
                self.dispatch('on_entry_added', entry, parent)
            else:
                parent.entries.append(entry)

        self.files = files
        if parent:
            return parent.entries

    def entry_subselect(self, entry):
        if not isdir(entry.path):
            return
        try:
            subentries = self._add_files(entry.path, entry)
        except OSError:
            #Logger.exception(e)
            entry.locked = True
            return
        for subentry in subentries:
            self.dispatch('on_subentry_to_entry', subentry, entry)

    def close_subselection(self, entry):
        for subentry in entry.entries:
            self.dispatch('on_remove_subentry', subentry, entry)


class FileChooserListView(FileChooserController):
    '''Implementation of :class:`FileChooserController` using a list view
    '''
    _ENTRY_TEMPLATE = 'FileListEntry'


class FileChooserIconView(FileChooserController):
    '''Implementation of :class:`FileChooserController` using an icon view
    '''
    _ENTRY_TEMPLATE = 'FileIconEntry'


if __name__ == '__main__':
    from kivy.app import App

    class FileChooserApp(App):

        def build(self):
            pos = (100, 100)
            size_hint = (None, None)
            size = (300, 400)
            return FileChooserListView(pos=pos, size=size, size_hint=size_hint)
            return FileChooserIconView(pos=pos, size=size, size_hint=size_hint)
    FileChooserApp().run()
