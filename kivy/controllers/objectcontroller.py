'''
ObjectController
----------------

The ObjectController class holds a single object in the data property. This
object can be anything, including a collection.

The default update() method for setting data will set any single objects to
data, and will set the first item of a list to data.

Methods in an object controller can transform the data item in various ways to
build an API for it.

.. versionadded:: 1.8

'''

from kivy.controllers.controller import Controller

__all__ = ('ObjectController', )


class ObjectController(Controller):

    def __init__(self, **kwargs):
        super(ObjectController, self).__init__(**kwargs)

    # Enhance for bindings to list controllers. Look at how ListAdapter, for
    # example checks if data is a controller, then does a swap and set,
    # followed by bind after instantiation.

    # Add transformation methods.

    def update(self, *args):
        # args:
        #
        #     controller args[0]
        #     value      args[1]
        #     op_info    args[2]

        value = args[1]

        if isinstance(value, list):
            if value:
                self.data = value[0]
            else:
                self.data = None
        else:
            self.data = value
