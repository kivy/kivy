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

from kivy.adapters.args_converters import list_item_args_converter
from kivy.event import EventDispatcher
from kivy.lang import Builder
from kivy.models import SelectableDataItem
from kivy.properties import DictProperty
from kivy.properties import ObjectProperty


class Adapter(EventDispatcher):
    '''An :class:`~kivy.adapters.adapter.Adapter` is a bridge between data and
    an :class:`~kivy.uix.abstractview.AbstractView` or one of its subclasses,
    such as a :class:`~kivy.uix.listview.ListView`.

    .. versionchanged:: 1.8.0

        Selection code was pulled out of ListAdapter and put separately as a
        mixin. Now adapters have to choose whether or not to mix it in. In a
        related move, cached_views and related code were moved from ListAdapter
        to this base class. This is what adapters do -- they create and cache
        views in a kind of helper system for collection style views. In contrast,
        traditional controllers do not perform this role, and are simpler.

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

    def bind_triggers_to_view(self, func):
        '''
        .. deprecated:: 1.8

             The data changed system was changed to use variants of
             ObservableList/Dict that dispatch after individual operations,
             passing information about what changed to a data_changed()
             handler, which should be implemented by observers of adapters.
        '''

        self.bind(data=func)

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

        The default return, prior to Kivy version 1.8, was only the data
        item. In newer Kivy, the return is a tuple with the data item in the
        first position, along with additional items, per adapter.
        '''
        pass

    def create_view(self, index):
        '''This method is used by :class:`kivy.adapters.adapter.Adapter` and
        :class:`kivy.adapters.simplelistadapter.SimpleListAdapter`.  Here we
        create bindings for the data item and its children back to
        self.handle_selection(), and do other selection-related tasks to keep
        item views in sync with the data.
        '''

        data_item_ret = self.get_data_item(index)

        # Backwards compatibility: get_data_item() returns either the data item
        # alone, prior to Kivy 1.8, or a tuple with the data item in the first
        # position in later versions.
        if not isinstance(data_item_ret, tuple):
            item = data_item_ret
        else:
            item = data_item_ret[0]

        if item is None:
            return None

        # data_item_ret could contain additional items needed by the converter,
        # such as the dictionary key within sorted_keys of DictAdapter. The
        # first argument is the index, and the second the data item, followed
        # by any additional args.

        # Inspect the args_converter, which could be a function, method, or a
        # lambda, with a varying number of arguments, to make the call to the
        # args_converter in a backwards-compatible way.
        args_converter_spec = inspect.getargspec(self.args_converter)

        num_args = len(args_converter_spec.args)

        # functions or methods vs. lambdas
        if args_converter_spec.args[0] == 'self':
            num_args -= 1

        # The else handles the post Kivy 1.8 allowance for additional args, for
        # example, for DictAdapter.
        if num_args <= 2:
            item_args = self.args_converter(index, item)
        else:
            item_args = self.args_converter(index, item, *data_item_ret[1:])

        item_args['index'] = index

        # Finally, create the view with the prepared arguments.
        if self.cls:
            view_instance = self.cls(**item_args)
        else:
            view_instance = Builder.template(self.template, **item_args)

        # This adapter could be using selection. If it is, and if
        # sync_with_model_data, the view should reflect the state of selection
        # in the data item.
        if hasattr(self, 'selection') and self.sync_with_model_data:

            # The data item must be a subclass of SelectableDataItem, or must
            # have an is_selected boolean or function, so it has is_selected
            # available.  If is_selected is unavailable on the data item, an
            # exception is raised.

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
