"""
FileChooser
===========

.. warning:

    This is experimental and subject to change as long as this warning notice is
    present.
"""


from kivy.lang import Builder
from kivy.logger import Logger
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.treeview import TreeViewNode
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty, ListProperty


from os import getcwdu, listdir
from os.path import basename, getsize, isdir, join, sep, normpath, dirname, \
                    samefile
from fnmatch import filter as fnfilter


class FileChooserController(FloatLayout):
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

    files = ListProperty([])
    '''
    Read-only :class:`~kivy.properties.ListProperty`.
    The list of files in the directory specified by path after applying the
    filter.
    '''

    def __init__(self, **kwargs):
        self.register_event_type('on_entry_added')
        self.register_event_type('on_entries_cleared')
        self.register_event_type('on_subentry_to_entry')
        self.register_event_type('on_remove_subentry')
        super(FileChooserController, self).__init__(**kwargs)
        self.bind(path=self._trigger_update,
                  filter=self._trigger_update)
        self._trigger_update()

    def _trigger_update(self, *args):
        self._update_files()

    def on_entry_added(self, node, parent=None):
        pass

    def on_entries_cleared(self):
        pass

    def on_subentry_to_entry(self, subentry, entry):
        pass

    def on_remove_subentry(self, subentry, entry):
        pass

    def open_entry(self, entry):
        if isdir(entry.path):
            self.path = join(self.path, entry.path)

    def _apply_filter(self, files):
        if not self.filter:
            return files
        return fnfilter(files, self.filter)

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
            pardir = Builder.template('FileEntry', dict(name=back, size='',
                path=back, controller=self, isdir=True, parent=None, sep=sep,
                get_nice_size=lambda: ''))
            self.dispatch('on_entry_added', pardir)
        self._add_files(self.path)

    def _add_files(self, path, parent=None):
        # Make sure we're using unicode in case of non-ascii chars in filenames
        self.files = self._apply_filter(listdir(unicode(path)))
        # Add the files
        if parent:
            parent.entries = []
        n = 0
        for file in self.files:
            file = normpath(join(path, file))
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
            entry = Builder.template('FileEntry', ctx)
            if not parent:
                self.dispatch('on_entry_added', entry, parent)
            else:
                parent.entries.append(entry)
        if parent:
            return parent.entries

    def entry_subselect(self, entry):
        if not isdir(entry.path):
            return
        for subentry in self._add_files(entry.path, entry):
            self.dispatch('on_subentry_to_entry', subentry, entry)

    def close_subselection(self, entry):
        for subentry in entry.entries:
            self.dispatch('on_remove_subentry', subentry, entry)


class FileChooserListView(FileChooserController):
    pass


if __name__ == '__main__':
    from kivy.app import App
    class FileChooserApp(App):
        def build(self):
            return FileChooserListView()
    FileChooserApp().run()
