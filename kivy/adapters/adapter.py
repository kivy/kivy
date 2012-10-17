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

    # These pertain to item views:
    cls = ObjectProperty(None)
    template = ObjectProperty(None)
    args_converter = ObjectProperty(None)

    def __init__(self, **kwargs):
        if 'args_converter' in kwargs:
            self.args_converter = kwargs['args_converter']
        else:
            self.args_converter = list_item_args_converter

        super(Adapter, self).__init__(**kwargs)

        if self.cls is None and self.template is None:
            raise Exception('A cls or template must be defined')
        if self.cls is not None and self.template is not None:
            raise Exception('Cannot use cls and template at the same time')

    def get_count(self):  #pragma: no cover
        raise NotImplementedError

    def get_item(self, index):  #pragma: no cover
        raise NotImplementedError

    def get_view(self, index):  #pragma: no cover
        raise NotImplementedError
