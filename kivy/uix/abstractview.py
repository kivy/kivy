'''
Abstract View
=============

.. versionadded:: 1.5

The :class:`AbstractView` widget has an adapter property for an adapter that
mediates to data, and an item_view_instances dict property that holds views
managed by the adapter.

'''

__all__ = ('AbstractView', )

from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty, DictProperty


class AbstractView(FloatLayout):
    '''View using an Adapter as a data provider
    '''

    adapter = ObjectProperty(None)
    '''The adapter can be one of several defined in kivy/adapters. The most
    common example is the ListAdapter used for managing data items in a list.
    '''

    item_view_instances = DictProperty({})
    '''View instances for data items are instantiated and managed in the
    associated adapter. Here we maintain a dictionary containing the view
    instances keyed to the indices in the data.

    Effectively, this dictionary works as a cache, only asking for a view from
    the adapter if one is not already stored for the requested index.
    '''

    def set_item_view(self, index, item_view):
        pass

    def get_item_view(self, index):
        item_view_instances = self.item_view_instances
        if index in item_view_instances:
            return item_view_instances[index]
        item_view = self.adapter.get_view(index)
        if item_view:
            item_view_instances[index] = item_view
        return item_view
