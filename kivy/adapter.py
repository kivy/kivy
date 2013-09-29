'''
Adapter
=======

.. versionadded:: 1.5

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

An :class:`~kivy.adapters.adapter.Adapter` is a bridge between data and
an :class:`~kivy.uix.abstractview.AbstractView` or one of its subclasses, such
as a :class:`~kivy.uix.listview.ListView`.

Arguments:

* *data*, for any sort of data to be used in a view. For an
  :class:`~kivy.adapters.adapter.Adapter`, data can be an object as well as a
  list, dict, etc. For a :class:`~kivy.adapters.listadapter.ListAdapter`, data
  should be a list. For a :class:`~kivy.adapters.dictadapter.DictAdapter`,
  data should be a dict.

* *list_item_class*, for a list key class to use to instantiate list item view
  instances.

* *args_converter*, a function to transform the data argument
  sets, in preparation for either a list_item_class instantiation.  If no
  args_converter is provided, a default one, that assumes that the data items
  are strings, is used.

.. versionchanged:: 1.8

    Removed bind_triggers_to_view().

    Reduced documentation for template, which is deprecated.

    Renamed cls to list_item_class, to be more explicit, and to avoid conflict
    in lang.py.

'''

__all__ = ('Adapter', )

import collections
from inspect import isclass

from kivy.event import EventDispatcher
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import DictProperty
from kivy.properties import ObjectProperty


class Adapter(EventDispatcher):
    '''An :class:`~kivy.adapters.adapter.Adapter` is a bridge between data and
    an :class:`~kivy.uix.abstractview.AbstractView` or one of its subclasses,
    such as a :class:`~kivy.uix.listview.ListView`.

    .. versionadded:: 1.5

    .. versionchanged:: 1.8.0

        Selection code was pulled out of ListAdapter and put separately as a
        mixin. Now adapters have to choose whether or not to mix it in. In a
        related move, cached_views and related code were moved from ListAdapter
        to this base class. This is what adapters do -- they create and cache
        views in a kind of helper system for collection style views. In
        contrast, traditional controllers do not perform this role, and are
        simpler.

        create_view() now handles additional arguments that may come from
        get_data_item(), specifically for the dictionary key added to the args
        of the DictAdapter args_converter.
    '''

    data = ObjectProperty(None)
    '''
    The data for which a view is to be constructed using the list_item_class
    provided, together with the args_converter provided or the default
    args_converter.

    In this base class, data is an ObjectProperty, so it could be used for a
    wide variety of single-view needs.

    Subclasses may override it in order to use another data type, such as a
    :class:`~kivy.properties.ListProperty` or
    :class:`~kivy.properties.DictProperty` as appropriate. For example, in a
    :class:`~.kivy.adapters.listadapter.ListAdapter`, data is a
    :class:`~kivy.properties.ListProperty`.

    :data:`data` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.

    .. versionadded:: 1.5

    '''

    list_item_class = ObjectProperty(None)
    '''
    A class for instantiating a given view item.

    :data:`list_item_class` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.

    .. versionadded:: 1.5

    '''

    template = ObjectProperty(None)
    '''
    A template for instantiating a given view item.

    :data:`template` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.

    .. versionadded:: 1.5

    .. versionchanged:: 1.8

        Templates have been deprecated. Use dynamic classes instead.
    '''

    args_converter = ObjectProperty(None)
    '''
    A function that prepares an args dict for the list_item_class from a data
    item.

    If an args_converter is not provided, a default one is set that assumes
    simple content in the form of a list of strings.

    :data:`args_converter` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.

    .. versionadded:: 1.5

    '''

    cached_views = DictProperty({})
    '''View instances for data items are instantiated and managed by the
    adapter. Here we maintain a dictionary containing the view
    instances keyed to the indices in the data.

    This dictionary works as a cache. get_view() only asks for a view from
    the adapter if one is not already stored for the requested index.

    :data:`cached_views` is a :class:`~kivy.properties.DictProperty` and
    defaults to {}.

    .. versionadded:: 1.5

    '''

    def __init__(self, **kwargs):

        super(Adapter, self).__init__(**kwargs)

        if 'args_converter' not in kwargs:
            self.args_converter = lambda row_index, x: {'text': x,
                                                        'size_hint_y': None,
                                                        'height': 25}

    def get_view_from_item(self, item):

        data = self.data_binding.source.data
        if item in data:
            return self.get_view(data.index(item))
        return None

    def get_view(self, index):

        if index in self.cached_views:
            return self.cached_views[index]
        item_view = self.create_view(index)
        if item_view:
            self.cached_views[index] = item_view

        return item_view

    def get_count(self):
        pass

    def get_data_item(self, index):
        '''This method is responsible for returning a single data item,
        whatever that means, for a given adapter. The result is used in view
        creation, where it is passed as the argument to the args_converter.
        '''
        pass

    def additional_args_converter_args(self, index):
        '''An adapter subclass needs to implement this method to return any
        additional args needed, in addition to the data item itself, which is
        returned in a separate call to get_data_item().

        .. versionadded:: 1.8

        '''
        pass

    def create_view(self, index):
        '''This method fetches the data_item at the index, and a builds a view
        from it. The view is is an instance of self.list_item_class, made from
        arguments parpared by self.args_converter(). This method is used by
        :class:`kivy.adapters.listadapter.ListAdapter` and
        :class:`kivy.adapters.dictadapter.DictListAdapter`.
        '''

        data = self.data_binding.source.data
        if not isinstance(data, collections.Iterable):
            if index != 0:
                return None

        elif index < 0 or index > len(data) - 1:
            return None

        data_item = self.get_data_item(index)

        if data_item is None:
            return None

        item_args = self.args_converter(
                index, data_item, *self.additional_args_converter_args(index))

        item_args['index'] = index

        if isinstance(self.list_item_class, str):
            self.list_item_class = Factory.get(self.list_item_class)
            if not isclass(self.list_item_class):
                raise Exception(('In kv, list_item_class must be a string '
                                 'with the name of a class in scope for the '
                                 'reference in the kv definition, or a class '
                                 'reference in Python.'))
        if self.list_item_class:
            view_instance = self.list_item_class(**item_args)
        else:
            view_instance = Builder.template(self.template, **item_args)

        if hasattr(self.data_binding.source, 'handle_selection'):
            if hasattr(view_instance, 'bind_composite'):
                view_instance.bind_composite(
                        self.data_binding.source.handle_selection)
            else:
                view_instance.bind(
                        on_release=self.data_binding.source.handle_selection)

        data_item_ksel = self.get_data_item_ksel(data_item)

        # Always load selection from data.
        if data_item_ksel and data_item_ksel.is_selected():

            if hasattr(self.data_binding.source, 'select_item'):
                self.data_binding.source.select_item(view_instance,
                                                     add_to_selection=False)

        if data_item_ksel:
            if hasattr(view_instance, 'ksel'):
                data_item_ksel.bind_to_ksel(view_instance.ksel)

#           if self.selection_update_method == selection_update_methods.NOTIFY:
#
#                if self.selection_scheme == selection_schemes.VIEW_ON_DATA:
#                    # One-way binding. To.
#                    ksel.bind_to_ksel(view_instance.ksel)
#                elif self.selection_scheme == selection_schemes.VIEW_DRIVEN:
#                    # One-way binding. From.
#                    ksel.bind_from_ksel(view_instance.ksel)
#                elif self.selection_scheme == selection_schemes.DATA_DRIVEN:
#                    # One-way binding. To.
#                    ksel.bind_to_ksel(view_instance.ksel)
#                elif (self.selection_scheme
#                        == selection_schemes.DATA_VIEW_COUPLED):
#                    # Two-way binding. Both.
#                    ksel.bind_to_ksel(view_instance.ksel)
#                    ksel.bind_from_ksel(view_instance.ksel)

        return view_instance

    def get_data_item_ksel(self, data_item):
        from kivy.models import SelectableDataItem

        data_item_ksel = None

        if isinstance(data_item, SelectableDataItem):
            data_item_ksel = data_item.ksel
        elif hasattr(data_item, 'ksel'):
            data_item_ksel = data_item.ksel
        elif isinstance(data_item, dict) and 'ksel' in data_item:
            data_item_ksel = data_item['ksel']

        return data_item_ksel
