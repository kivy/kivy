'''
CollectionAdapter
=================

.. versionadded:: 1.5

:class:`CollectionAdapter` is a base class for adapters dedicated to lists or
dicts or other collections of data.
'''

from kivy.properties import ObjectProperty
from kivy.adapters.adapter import Adapter


class CollectionAdapter(Adapter):

    owning_view = ObjectProperty(None)
    '''Management of selection requires manipulation of key view instances,
    which are created in an adapter, but cached in the owning_view, such as a
    :class:`ListView` instance. In some operations at the adapter level,
    access is needed to the views.
    '''

    def __init__(self, **kwargs):
        super(CollectionAdapter, self).__init__(**kwargs)

    def trim_left_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are less than the
        index of the first selected item, if there is selection.
        '''
        pass

    def trim_right_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are greater than
        the index of the last selected item, if there is selection.
        '''
        pass

    def trim_to_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are les than or
        greater than the index of the last selected item, if there is
        selection. This preserves intervening list items within the selected
        range.
        '''
        pass

    def cut_to_sel(self, *args):
        '''Same as trim_to_sel, but intervening list items within the selected
        range are cut also, leaving only list items that are selected.
        '''
        pass
