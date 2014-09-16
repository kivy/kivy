'''
Abstract View
=============

.. versionadded:: 1.5

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

The :class:`~kivy.uix.abstractview.AbstractView` widget has an adapter property
for an adapter that mediates to data. The adapter manages an
item_view_instance dict property that holds views for each data item,
operating as a cache.

'''

__all__ = ('AbstractView', )

from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty


class AbstractView(FloatLayout):
    '''
    View using an :class:`~kivy.adapters.adapter.Adapter` as a data provider.
    '''

    adapter = ObjectProperty(None)
    '''The adapter can be one of several kinds of
    :class:`adapters <kivy.adapters.adapter.Adapter>`. The most
    common example is the :class:`~kivy.adapters.listadapter.ListAdapter` used
    for managing data items in a list.
    '''
