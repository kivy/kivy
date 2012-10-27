'''
Adapter
=======

.. versionadded:: 1.5

.. warning::

    This widget is still experimental, and his API is subject to change in a
    future version.

:class:`~kivy.adapters.adapter.Adapter` is a bridge between data and
:class:`~kivy.uix.abstractview.AbstractView` or one of its subclasses, such as
:class:`~kivy.uix.listview.ListView`.

Arguments:

* *data*, for any sort of data to be used in a view. In
  :class:`~kivy.adapters.adapter.Adapter`, data can be an object, as well as a
  list, dict, etc. For :class:`~kivy.adapters.listadapter.ListAdapter`, data
  is a list, and for :class:`~kivy.adapters.dictadapter.DictAdapter`, it is a
  dict.

* *cls*, for a list key class to use to instantiate key view
  instances (Use this or the template argument)

* *template*, a kv template to use to instantiate key view instances (Use
  this or the cls argument)

* *args_converter*, a function to transform data item argument
  sets, in preparation for either a cls instantiation, or a kv template
  invocation. If no args_converter is provided, a default one is set, that
  assumes that the data items are strings.


'''

__all__ = ('Adapter', )

from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.adapters.args_converters import list_item_args_converter


class Adapter(EventDispatcher):
    ''':class:`~kivy.adapters.adapter.Adapter` is a bridge between data and
    :class:`~kivy.uix.abstractview.AbstractView` or one of its subclasses,
    such as :class:`~kivy.uix.listview.ListView`.
    '''

    data = ObjectProperty(None)
    '''
    The data for which a view is to be constructed using either the cls or
    template provided, using an args_converter provided or a default args
    converter.

    In this base class, data is an ObjectProperty, so it could be used for a
    wide variety of single-view needs.

    Subclasses may override to another data type, such as
    :class:`~kivy.properties.ListProperty` or
    :class:`~kivy.properties.DictProperty, as appropriate. For example, in
    :class:`~.kivy.adapters.listadapter.ListAdapter, data is a
    :class:`~kivy.properties.ListProperty`.

    :data:`data` is an :class:`~kivy.properties.ObjectProperty`, default
    to None.
    '''

    cls = ObjectProperty(None)
    '''
    A class for instantiating a given view item. (Use this or template).

    :data:`cls` is an :class:`~kivy.properties.ObjectProperty`, default
    to None.
    '''

    template = ObjectProperty(None)
    '''
    A kv template for instantiating a given view item. (Use this or cls).

    :data:`template` is an :class:`~kivy.properties.ObjectProperty`, default
    to None.
    '''

    args_converter = ObjectProperty(None)
    '''
    A function that prepares an args dict for the cls or kv template to build
    a view from a data item.

    If an args_converter is not provided, a default one is set that assumes
    simple content in the form of a list of strings.

    :data:`args_converter` is an :class:`~kivy.properties.ObjectProperty`,
    default to None.
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

        if 'args_converter' in kwargs:
            self.args_converter = kwargs['args_converter']
        else:
            self.args_converter = list_item_args_converter

        super(Adapter, self).__init__(**kwargs)

    def bind_triggers_to_view(self, func):
        self.bind(data=func)

    def get_data_item(self):
        return self.data

    def get_view(self, index):  # pragma: no cover
        item_args = self.args_converter(self.data)

        if self.cls:
            instance = self.cls(**item_args)
            return instance
        else:
            return Builder.template(self.template, **item_args)
