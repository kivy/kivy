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


'''

__all__ = ('Adapter', )

import inspect

from kivy.event import EventDispatcher
from kivy.properties import DictProperty
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.adapters.models import SelectableDataItem
from kivy.adapters.selection import Selection
from kivy.adapters.args_converters import list_item_args_converter


class Adapter(Selection, EventDispatcher):
    '''An :class:`~kivy.adapters.adapter.Adapter` is a bridge between data and
    an :class:`~kivy.uix.abstractview.AbstractView` or one of its subclasses,
    such as a :class:`~kivy.uix.listview.ListView`.

    .. versionchanged:: 1.8.0

        Selection code was pulled out of ListAdapter and pushed down here, so
        now all adapters have selection functionality. cached_views and related
        code was also moved here.
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

    :data:`template` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
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

    cached_views = DictProperty({})
    '''View instances for data items are instantiated and managed by the
    adapter. Here we maintain a dictionary containing the view
    instances keyed to the indices in the data.

    This dictionary works as a cache. get_view() only asks for a view from
    the adapter if one is not already stored for the requested index.

    :data:`cached_views` is a :class:`~kivy.properties.DictProperty` and
    defaults to {}.
    '''

    def __init__(self, **kwargs):

        if not 'data' in kwargs:
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

        if not 'args_converter' in kwargs:
            self.args_converter = list_item_args_converter

    # TODO: Mark as deprecated.
    def bind_triggers_to_view(self, func):
        self.bind(data=func)

    def get_view(self, index):
        if index in self.cached_views:
            return self.cached_views[index]
        item_view = self.create_view(index)
        if item_view:
            self.cached_views[index] = item_view

        return item_view

    def get_count(self):
        return len(self.data)

    def get_data_item(self, index):
        if index < 0 or index >= len(self.data):
            return None
        return self.data[index]

    def create_view(self, index):
        '''This method is more complicated than the one in
        :class:`kivy.adapters.adapter.Adapter` and
        :class:`kivy.adapters.simplelistadapter.SimpleListAdapter`, because
        here we create bindings for the data item and its children back to
        self.handle_selection(), and do other selection-related tasks to keep
        item views in sync with the data.
        '''
        item = self.get_data_item(index)
        if item is None:
            return None

        item_args = self.args_converter(index, item)

        item_args['index'] = index

        if self.cls:
            view_instance = self.cls(**item_args)
        else:
            view_instance = Builder.template(self.template, **item_args)

        if self.propagate_selection_to_data:
            # The data item must be a subclass of SelectableDataItem, or must
            # have an is_selected boolean or function, so it has is_selected
            # available.  If is_selected is unavailable on the data item, an
            # exception is raised.
            #
            if isinstance(item, SelectableDataItem):
                if item.is_selected:
                    self.handle_selection(view_instance)
            elif type(item) == dict and 'is_selected' in item:
                if item['is_selected']:
                    self.handle_selection(view_instance)
            elif hasattr(item, 'is_selected'):
                # TODO: Change this to use callable().
                if (inspect.isfunction(item.is_selected)
                        or inspect.ismethod(item.is_selected)):
                    if item.is_selected():
                        self.handle_selection(view_instance)
                else:
                    if item.is_selected:
                        self.handle_selection(view_instance)
            else:
                msg = "ListAdapter: unselectable data item for {0}"
                raise Exception(msg.format(index))

        view_instance.bind(on_release=self.handle_selection)

        if self.bind_selection_to_children:
            for child in view_instance.children:
                child.bind(on_release=self.handle_selection)

        return view_instance
