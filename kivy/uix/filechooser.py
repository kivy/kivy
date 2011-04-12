"""
FileChooser
===========

.. versionadded:: 1.0.5

.. warning:

    This is experimental and subject to change as long as this warning notice is
    present.
"""


from kivy.clock import Clock
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.treeview import TreeViewNode
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty, ListProperty, BooleanProperty, \
                            ObjectProperty


from sys import platform
from os import getcwdu, listdir
from os.path import basename, getsize, isdir, join, sep, normpath, dirname, \
                    samefile
from fnmatch import filter as fnfilter


def is_hidden_unix(fn):
    return basename(fn).startswith('.')


def is_hidden_win(fn):
    # Import that module here as it's not available on non-windows machines.
    # See http://bit.ly/i9klJE except that the attributes are defined in
    # win32file not win32com (bug on page).
    # Note: For some reason this doesn't work after a os.chdir(), no matter to
    #       what directory you change from where. Windows weirdness.
    from win32file import FILE_ATTRIBUTE_HIDDEN, GetFileAttributesEx
    attribs = GetFileAttributesEx(fn)
    return attribs[0] & FILE_ATTRIBUTE_HIDDEN


def alphanumeric_folders_first(files):
    return sorted(f for f in files if isdir(f)) + \
           sorted(f for f in files if not isdir(f))


class FileChooserController(FloatLayout):
    _ENTRY_TEMPLATE = None

    path = StringProperty(u'/')
    '''
    :class:`~kivy.properties.StringProperty`, defaults to current working
    directory as unicode string. Specifies the path on the filesystem that
    this controller should look at.
    '''

    filter = StringProperty('')
    '''
    :class:`~kivy.properties.StringProperty`, defaults to '', equal to '*'.
    The filter is applied the files in the directory, e.g. '*.png'.
    The filter is not reset when the path changes, you need to do that yourself
    if you want that. You can use the following patterns:

      Pattern	| Meaning
      ----------+---------------------------------
      *	        | matches everything
      ?	        | matches any single character
      [seq]	| matches any character in seq
      [!seq]	| matches any character not in seq
    '''

    filter_dirs = BooleanProperty(False)
    '''
    :class:`~kivy.properties.BooleanProperty`, defaults to False.
    Indicate whether filter should also apply to directories.
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
    filter.
    '''

    show_hidden = BooleanProperty(False)
    '''
    :class:`~kivy.properties.BooleanProperty`, defaults to False.
    Determines whether hidden files and folders should be shown.
    '''

    def __init__(self, **kwargs):
        self.register_event_type('on_entry_added')
        self.register_event_type('on_entries_cleared')
        self.register_event_type('on_subentry_to_entry')
        self.register_event_type('on_remove_subentry')
        super(FileChooserController, self).__init__(**kwargs)

        if platform in ('darwin', 'linux2'):
            self.is_hidden = is_hidden_unix
        elif platform == 'win32':
            self.is_hidden = is_hidden_win
        else:
            raise NotImplementedError('Only available for Linux, OSX and Win')

        self.bind(path=self._trigger_update,
                  filter=self._trigger_update)
        self._trigger_update()

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

    def select_entry(self, entry):
        entry.selected = not entry.selected

    def open_entry(self, entry):
        if isdir(entry.path):
            try:
                # Just check if we can list the directory. This is also what
                # _add_file does, so if it fails here, it would also fail later
                # on. Do the check here to prevent setting path to an invalid
                # directory that we cannot list.
                listdir(unicode(entry.path))
            except OSError, e:
                Logger.exception(e)
                entry.locked = True
            else:
                self.path = join(self.path, entry.path)

    def _apply_filter(self, files):
        if not self.filter:
            return files
        filtered = fnfilter(files, self.filter)
        if not self.filter_dirs:
            dirs = [f for f in files if isdir(f)]
            return dirs + filtered
        return filtered

    def get_nice_size(self, fn):
        '''
        Pass the filepath. Returns the size in the best human readable
        format or '' if it's a directory (Don't recursively calculate size.).
        '''
        if isdir(fn):
            return ''
        try:
            size = getsize(fn)
        except OSError, e:
            Logger.exception(e)
            return '--'

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return "%1.0f %s" % (size, unit)
            size /= 1024.0

    def _update_files(self, *args):
        # Clear current files
        self.dispatch('on_entries_cleared')

        # Add the components that are always needed
        is_root = samefile(self.path, u'/')
        if not is_root:
            back = '..' + sep
            pardir = Builder.template(self._ENTRY_TEMPLATE, **dict(name=back,
                size='', path=back, controller=self, isdir=True, parent=None,
                sep=sep, get_nice_size=lambda: ''))
            self.dispatch('on_entry_added', pardir)
        self._add_files(self.path)

    def _add_files(self, path, parent=None):
        # Make sure we're using unicode in case of non-ascii chars in filenames.
        # listdir() returns unicode if you pass it unicode.
        files = listdir(unicode(path))
        # In the following, use fully qualified filenames
        files = [normpath(join(path, f)) for f in files]
        # Apply filename filters
        files = self._apply_filter(files)
        # Sort the list of files
        files = self.sort_func(files)
        # Add the files
        if parent:
            parent.entries = []
        for file in files:
            if not self.show_hidden and self.is_hidden(file):
                continue

            def get_nice_size():
                # Use a closure for lazy-loading here
                return self.get_nice_size(file)

            ctx = {'name': basename(file),
                   'get_nice_size': get_nice_size,
                   'path': file,
                   'controller': self,
                   'isdir': isdir(file),
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
        except OSError, e:
            Logger.exception(e)
            entry.locked = True
            return
        for subentry in subentries:
            self.dispatch('on_subentry_to_entry', subentry, entry)

    def close_subselection(self, entry):
        for subentry in entry.entries:
            self.dispatch('on_remove_subentry', subentry, entry)


class FileChooserListView(FileChooserController):
    _ENTRY_TEMPLATE = 'FileListEntry'


class FileChooserIconView(FileChooserController):
    _ENTRY_TEMPLATE = 'FileIconEntry'


if __name__ == '__main__':
    from kivy.app import App
    class FileChooserApp(App):
        def build(self):
            pos = (100, 100)
            size_hint = (None, None)
            size = (300, 400)
            return FileChooserListView(pos=pos, size=size, size_hint=size_hint)
            #return FileChooserIconView(pos=pos, size=size, size_hint=size_hint)
    FileChooserApp().run()
