'''
DictView
===========

.. versionadded:: 1.8

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

A :class:`~kivy.uix.dictview.DictView` is a primary high-level widget,
handling the common task of presenting dictionary items in a scrolling list.
Flexibility is afforded by use of a `DictAdapter` to interface with
data.

'''

__all__ = ('DictView', )

from kivy.uix.listview import ListView
from kivy.adapters.dictadapter import DictAdapter
from kivy.properties import ObjectProperty, AliasProperty

class DictView(ListView):
    adapter = ObjectProperty(DictAdapter())
    
    def _get_sorted_keys(self):
        return self.adapter.sorted_keys
        
    sorted_keys = AliasProperty(_get_sorted_keys, None, bind=('adapter',))
