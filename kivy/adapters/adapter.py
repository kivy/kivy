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

* *cls*, for a list key class to use to instantiate list item view
  instances (Use this or the template argument).

* *template*, a kv template to use to instantiate list item view instances (Use
  this or the cls argument).

* *args_converter*, a function to transform the data argument
  sets, in preparation for either a cls instantiation or a kv template
  invocation. If no args_converter is provided, a default one, that
  assumes that the data items are strings, is used.

.. versionchanged:: 1.8

    Removed bind_triggers_to_view().

'''

__all__ = ('Adapter', )

import collections

from kivy.adapters.args_converters import list_item_args_converter
from kivy.event import EventDispatcher
from kivy.lang import Builder
from kivy.properties import DictProperty
from kivy.properties import ObjectProperty
from kivy.selection import selection_schemes
from kivy.selection import selection_update_methods


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
    The data for which a view is to be constructed using either the cls or
    template provided, together with the args_converter provided or the default
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

    cls = ObjectProperty(None)
    '''
    A class for instantiating a given view item (Use this or template).

    :data:`cls` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.

    .. versionadded:: 1.5

    '''

    template = ObjectProperty(None)
    '''
    A kv template for instantiating a given view item (Use this or cls).

    :data:`template` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.

    .. versionadded:: 1.5

    '''

    args_converter = ObjectProperty(None)
    '''
    A function that prepares an args dict for the cls or kv template to build
    a view from a data item.

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

        if 'data' not in kwargs:
            raise Exception('adapter: input must include data argument')

        if 'cls' in kwargs:
            if 'template' in kwargs:
                msg = 'adapter: cannot use cls and template at the same time'
                raise Exception(msg)
            elif not kwargs['cls']:
                raise Exception('adapter: a cls or template must be defined')
        else:
            if 'template' in kwargs:
                if not kwargs['template']:
                    msg = 'adapter: a cls or template must be defined'
                    raise Exception(msg)
            else:
                raise Exception('adapter: a cls or template must be defined')

        super(Adapter, self).__init__(**kwargs)

        if 'args_converter' not in kwargs:
            self.args_converter = list_item_args_converter

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
        from it. The view is is an instance of self.cls, made from arguments
        parpared by self.args_converter(). This method is used by
        :class:`kivy.adapters.listadapter.ListAdapter` and
        :class:`kivy.adapters.dictadapter.DictListAdapter`.
        '''

        if not isinstance(self.data, collections.Iterable):
            if index != 0:
                return
        elif index < 0 or index > len(self.data) - 1:
            return None

        data_item = self.get_data_item(index)

        if data_item is None:
            return None

        item_args = self.args_converter(
                index, data_item, *self.additional_args_converter_args(index))

        item_args['index'] = index

        if self.cls:
            view_instance = self.cls(**item_args)
        else:
            view_instance = Builder.template(self.template, **item_args)

        view_instance.bind(on_release=self.handle_selection)

        ksel = None

        from kivy.models import SelectableDataItem

        if isinstance(data_item, SelectableDataItem):
            ksel = data_item.ksel
        elif hasattr(data_item, 'ksel'):
            ksel = data_item.ksel
        elif isinstance(data_item, dict) and 'ksel' in data_item:
            ksel = data_item['ksel']

        # Always load selection from data.
        if ksel and ksel.is_selected():
            self.handle_selection(view_instance)

        if ksel:

            if self.selection_update_method == selection_update_methods.NOTIFY:

                if self.selection_scheme == selection_schemes.VIEW_ON_DATA:
                    # One-way binding. To.
                    ksel.bind_to_ksel(view_instance.ksel)
                elif self.selection_scheme == selection_schemes.VIEW_DRIVEN:
                    # One-way binding. From.
                    ksel.bind_from_ksel(view_instance.ksel)
                elif self.selection_scheme == selection_schemes.DATA_DRIVEN:
                    # One-way binding. To.
                    ksel.bind_to_ksel(view_instance.ksel)
                elif (self.selection_scheme
                        == selection_schemes.DATA_VIEW_COUPLED):
                    # Two-way binding. Both.
                    ksel.bind_to_ksel(view_instance.ksel)
                    ksel.bind_from_ksel(view_instance.ksel)

        return view_instance

    def update_from_first_item(self, *args):
        l = args[1]
        if l:
            self.data = l[0]
