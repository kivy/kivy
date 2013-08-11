'''
SimpleListAdapter
=================

.. versionadded:: 1.5

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

The :class:`~kivy.adapters.simplelistadapter.SimpleListAdapter` is used for
basic lists. For example, it can be used for displaying a list of read-only
strings that do not require user interaction. It does not do selection.

.. versionchanged:: 1.8.0

    Changed the class to subclass Adapter, which now contains view caching
    and related code.
'''

__all__ = ('SimpleListAdapter', )

from kivy.adapters.adapter import Adapter
from kivy.adapters.args_converters import list_item_args_converter
from kivy.event import EventDispatcher
from kivy.properties import ListProperty
from kivy.properties import ObjectProperty
from kivy.lang import Builder


class SimpleListAdapter(EventDispatcher):
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

    :data:`data` is a :class:`~kivy.properties.ListProperty` and
    defaults to [].
    '''

    cls = ObjectProperty(None)
    '''
    A class for instantiating a given view item (Use this or template).

    :data:`cls` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    template = ObjectProperty(None)
    '''
    A kv template for instantiating a given view item (Use this or cls).

    :data:`template` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    args_converter = ObjectProperty(None)
    '''
    A function that prepares an args dict for the cls or kv template to build
    a view from a data item.

    If an args_converter is not provided, a default one is set that assumes
    simple content in the form of a list of strings.

    :data:`args_converter` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    def __init__(self, **kwargs):
        if 'data' not in kwargs:
            raise Exception('list adapter: input must include data argument')
        if type(kwargs['data']) not in (tuple, list):
            raise Exception('list adapter: data must be a tuple or list')
        super(SimpleListAdapter, self).__init__(**kwargs)

        if not 'args_converter' in kwargs:
            self.args_converter = list_item_args_converter

    def get_count(self):
        return len(self.data)

    def get_data_item(self, index):
        if index < 0 or index >= len(self.data):
            return None
        # The return is a tuple, with the data item first.
        return self.data[index],

    # Returns a view instance for an item.
    def get_view(self, index):
        ret = self.get_data_item(index)
        if ret is None:
            return None

        item, = ret

        if item is None:
            return None

        item_args = self.args_converter(index, item)

        if self.cls:
            instance = self.cls(**item_args)
            return instance
        else:
            return Builder.template(self.template, **item_args)
