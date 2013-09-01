'''
ObjectAdapter
===========

.. versionadded:: 1.8

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

A :class:`ObjectAdapter` is an adapter around a python object.

From :class:`~kivy.adapters.adapter.Adapter`, a
:class:`~kivy.adapters.listadapter.ObjectAdapter` gets cls, template, and
args_converter properties.

'''

__all__ = ('ObjectAdapter', )

from kivy.adapters.adapter import Adapter
from kivy.controllers.utils import parse_binding
from kivy.controllers.utils import bind_binding

from kivy.selection import Selection


class ObjectAdapter(Selection, Adapter):
    '''A :class:`~kivy.adapters.listadapter.ObjectAdapter` is an adapter around
    a python object.

    .. versionadded:: 1.8

    '''

    # data is an ObjectProperty defined in the Adapter class.

    __events__ = ('on_data_change', )

    def __init__(self, **kwargs):

        data_binding, kwargs = parse_binding('data', kwargs)
        selection_binding, kwargs = parse_binding('selection', kwargs)

        super(ObjectAdapter, self).__init__(**kwargs)

        if data_binding:
            bind_binding(self, data_binding)
        if selection_binding:
            bind_binding(self, selection_binding)

        self.bind(data=self.data_changed)

    def additional_args_converter_args(self, index):
        return ()

    def get_data_item(self, index):
        return self.data

    def data_changed(self, *args):
        self.cached_views.clear()
        self.initialize_selection()
        self.dispatch('on_data_change')

    def update_data_from_first_item(self, *args):
        l = args[1]
        if l:
            self.data = l[0]

    def update_selection_from_first_item(self, *args):
        l = args[1]
        if l:
            self.selection = [l[0]]

    def on_data_change(self, *args):
        pass
