'''
Abstract View
=============

.. versionadded:: 1.5

The :class:`AbstractView` widget has an adapter property for an adapter that
mediates to data. The adapter manages an item_view_instances dict property
that holds views for each data item, operating as a cache.

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
