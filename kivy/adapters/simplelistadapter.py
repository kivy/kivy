'''
SimpleListAdapter
=================

.. versionadded:: 1.5

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

The :class:`~kivy.adapters.simplelistadapter.SimpleListAdapter` is used for
basic lists. For example, it can be used for displaying a list of read-only
strings that do not require user interaction.

'''

__all__ = ('SimpleListAdapter', )

from kivy.adapters.adapter import Adapter
from kivy.properties import ListProperty
from kivy.lang import Builder


class SimpleListAdapter(Adapter):
    '''A :class:`~kivy.adapters.simplelistadapter.SimpleListAdapter` is an
    adapter around a Python list.

    From :class:`~kivy.adapters.adapter.Adapter`, the
    :class:`~kivy.adapters.simplelistadapter.ListAdapter` gets cls, template,
    and args_converter properties.
    '''

    data = ListProperty([])
    '''The data list property contains a list of objects (which can be strings)
    that will be used directly if no args_converter function is provided. If
    there is an args_converter, the data objects will be passed to it for
    instantiating the item view class instances.

    :attr:`data` is a :class:`~kivy.properties.ListProperty` and
    defaults to [].
    '''

    def __init__(self, **kwargs):
        if 'data' not in kwargs:
            raise Exception('list adapter: input must include data argument')
        if not isinstance(kwargs['data'], list) and \
                not isinstance(kwargs['data'], tuple):
            raise Exception('list adapter: data must be a tuple or list')
        super(SimpleListAdapter, self).__init__(**kwargs)

    def get_count(self):
        return len(self.data)

    def get_data_item(self, index):
        if index < 0 or index >= len(self.data):
            return None
        return self.data[index]

    # Returns a view instance for an item.
    def get_view(self, index):
        item = self.get_data_item(index)

        if item is None:
            return None

        item_args = self.args_converter(index, item)

        cls = self.get_cls()
        if cls:
            instance = cls(**item_args)
            return instance
        else:
            return Builder.template(self.template, **item_args)
