'''
Adapter
=======

.. versionadded:: 1.5

'''

from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.adapters.args_converters import list_item_args_converter


class Adapter(EventDispatcher):
    '''Adapter is a bridge between an AbstractView and data.
    '''

    data = ObjectProperty(None)
    '''
    The data for which a view is to be constructed using either the cls or
    template provided, using an args_converter provided or a default args
    converter.

    In this base class, data is an ObjectProperty, so it could be used for a
    wide variety of single-view needs.

    Subclasses may override to another data type, such as ListProperty or
    DictProperty, as appropriate. For example, in ListAdapter, data is a
    ListProperty.
    '''

    cls = ObjectProperty(None)
    '''
    A class for instantiating a given view item. (Use this or template).
    '''

    template = ObjectProperty(None)
    '''
    A kv template for instantiating a given view item. (Use this or cls).
    '''

    args_converter = ObjectProperty(None)
    '''
    A function that prepares an args dict for the cls or kv template to build
    a view from a data item.

    If an args_converter is not provided, a default one is set that assumes
    simple content in the form of a list of strings.
    '''

    def __init__(self, **kwargs):

        if 'data' not in kwargs:
            raise Exception('adapter: input must include data argument')

        if 'cls' in kwargs:
            if 'template' in kwargs:
                raise Exception('adapter: cannot use cls and template at the same time')
            elif not kwargs['cls']:
                raise Exception('adapter: a cls or template must be defined')
        else:
            if 'template' in kwargs:
                if not kwargs['template']:
                    raise Exception('adapter: a cls or template must be defined')
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

    def get_view(self, index):  #pragma: no cover
        item_args = self.args_converter(self.data)

        if self.cls:
            instance = self.cls(**item_args)
            return instance
        else:
            return Builder.template(self.template, **item_args)
