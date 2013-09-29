'''
ObjectController
----------------

The ObjectController class holds a single Controller in the data property. This
Controller can be anything, including a collection.

The default update() method for setting data will set any single Controllers to
data, and will set the first item of a list to data.

Methods in an Controller controller can transform the data item in various ways
to build an API for it.

.. versionadded:: 1.8

'''
from kivy.binding import DataBinding
from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty

__all__ = ('ObjectController', )


class ObjectController(EventDispatcher):

    data = ObjectProperty(None, allownone=True)
    data_binding = ObjectProperty(None, allownone=True)

    __events__ = ('on_data_change', )

    def __init__(self, **kwargs):

        if 'data_binding' not in kwargs:
            kwargs['data_binding'] = DataBinding()

        super(ObjectController, self).__init__(**kwargs)

        self.data_binding.bind_to(self, 'data')
        self.bind(data=self.data_changed)

    def on_data_change(self, *args):
        '''on_data_change() is the default handler for the on_data_change
        event.
        '''
        pass

    def data_changed(self, *args):
        self.dispatch('on_data_change')
