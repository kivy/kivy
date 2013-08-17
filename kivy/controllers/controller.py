'''
Controller
----------

The Controller class is the base class for controllers. It adds a data
ObjectProperty, which may be redefined in subclasses.

The update() method is the default callback for updating data.

.. versionadded:: 1.8

'''

from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty

__all__ = ('Controller', )


class Controller(EventDispatcher):

    data = ObjectProperty(None, allownone=True)

    def update(self, *args):
        pass
