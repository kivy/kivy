'''
SimpleListAdapter
=================

.. versionadded:: 1.5

.. warning::

    This widget is still experimental, and his API is subject to change in a
    future version.

:class:`SimpleListAdapter` is for simple lists, such as for showing a
text-only display of strings, or a list of views of some type that have
no user interaction.

'''

__all__ = ('SimpleListAdapter', )

from kivy.adapters.adapter import Adapter
from kivy.properties import ListProperty
from kivy.lang import Builder

class SimpleListAdapter(Adapter):
    ''':class:`SimpleListAdapter` is an adapter around a simple Python list.

    From :class:`Adapter`, :class:`SimpleListAdapter` gets these properties:

        Use only one:

            - cls, for a list item class to use to instantiate item view
                   instances

            - template, a kv template to use to instantiate item view
                        instances

        - args_converter, an optional function to transform data item argument
                          sets, in preparation for either a cls instantiation,
                          or a kv template invocation (If an args_converter is
                          not provided, a default one that assumes simple
                          strings content is set)
    '''

    data = ListProperty([])
    '''The data list property contains a list of objects (can be strings) that
    will be used directly if no args_converter function is provided. If there
    is an args_converter, the data objects will be passed to it, for
    instantiation of item view class (cls) instances from the data.

    :data:`data` is a :class:`~kivy.properties.ListProperty`,
    default to [].
    '''

    def __init__(self, **kwargs):
        if 'data' not in kwargs:
            raise Exception('list adapter: input must include data argument')
        if type(kwargs['data']) not in (tuple, list):
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

        item_args = self.args_converter(item)

        if self.cls:
            instance = self.cls(**item_args)
            return instance
        else:
            return Builder.template(self.template, **item_args)
