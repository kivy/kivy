'''
Adapter
=======

.. versionadded:: 1.5

.. deprecated:: 1.10.0
    The feature has been deprecated.

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

An :class:`~kivy.adapters.adapter.Adapter` is a bridge between data and
an :class:`~kivy.uix.abstractview.AbstractView` or one of its subclasses, such
as a :class:`~kivy.uix.listview.ListView`.

The following arguments can be passed to the contructor to initialise the
corresponding properties:

* :attr:`~Adapter.data`: for any sort of data to be used in a view. For an
  :class:`~kivy.adapters.adapter.Adapter`, data can be an object as well as a
  list, dict, etc. For a :class:`~kivy.adapters.listadapter.ListAdapter`, data
  should be a list. For a :class:`~kivy.adapters.dictadapter.DictAdapter`,
  data should be a dict.

* :attr:`~Adapter.cls`: the class used to instantiate each list item view
  instance (Use this or the template argument).

* :attr:`~Adapter.template`: a kv template to use to instantiate each list item
  view instance (Use this or the cls argument).

* :attr:`~Adapter.args_converter`: a function used to transform the data items
  in preparation for either a cls instantiation or a kv template
  invocation. If no args_converter is provided, the data items are assumed
  to be simple strings.

Please refer to the :mod:`~kivy.adapters` documentation for an overview of how
adapters are used.

'''

__all__ = ('Adapter', )

from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.adapters.args_converters import list_item_args_converter
from kivy.factory import Factory
from kivy.compat import string_types
from kivy.utils import deprecated


class Adapter(EventDispatcher):
    '''An :class:`~kivy.adapters.adapter.Adapter` is a bridge between data and
    an :class:`~kivy.uix.abstractview.AbstractView` or one of its subclasses,
    such as a :class:`~kivy.uix.listview.ListView`.
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

    :attr:`data` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    cls = ObjectProperty(None)
    '''
    A class for instantiating a given view item (Use this or template). If this
    is not set and neither is the template, a :class:`~kivy.uix.label.Label`
    is used for the view item.

    :attr:`cls` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    template = ObjectProperty(None)
    '''
    A kv template for instantiating a given view item (Use this or cls).

    :attr:`template` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    args_converter = ObjectProperty(None)
    '''
    A function that prepares an args dict for the cls or kv template to build
    a view from a data item.

    If an args_converter is not provided, a default one is set that assumes
    simple content in the form of a list of strings.

    :attr:`args_converter` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    @deprecated
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

        if 'args_converter' in kwargs:
            self.args_converter = kwargs['args_converter']
        else:
            self.args_converter = list_item_args_converter

        super(Adapter, self).__init__(**kwargs)

    def bind_triggers_to_view(self, func):
        self.bind(data=func)

    def get_data_item(self):
        return self.data

    def get_cls(self):
        '''
        .. versionadded:: 1.9.0

        Returns the widget type specified by self.cls. If it is a
        string, the :class:`~kivy.factory.Factory` is queried to retrieve the
        widget class with the given name, otherwise it is returned directly.
        '''
        cls = self.cls
        if isinstance(cls, string_types):
            try:
                cls = getattr(Factory, cls)
            except AttributeError:
                raise AttributeError(
                    'Listadapter cls widget does not exist.')
        return cls

    def get_view(self, index):  # pragma: no cover
        item_args = self.args_converter(self.data)

        cls = self.get_cls()
        if cls:
            return cls(**item_args)
        else:
            return Builder.template(self.template, **item_args)
