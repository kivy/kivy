'''
Adapter
=======

.. versionadded:: 1.4

Notes:

    - Presently, the only subclass is ListAdapter.

    - Explain the design philosophy used here -- something like model-view-
      adapter (MVA) as described here:

          http://en.wikipedia.org/wiki/Model-view-adapter (and link to
            basis article about Java Swing design)

      Using background in references like these, compare to MVC terminology,
      and how Kivy operates to fulfill the roles of mediating and coordinating
      controllers, especially.

    - Consider an associated "object adapter" (a.k.a., "object controller")
      that is bound to selection. It can also subclass Adapter?
'''

from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty
from kivy.lang import Builder


class Adapter(EventDispatcher):
    '''Adapter is a bridge between an AbstractView and data.
    '''

    # These pertain to item views:
    cls = ObjectProperty(None)
    template = ObjectProperty(None)
    args_converter = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Adapter, self).__init__(**kwargs)
        if self.cls is None and self.template is None:
            raise Exception('A cls or template must be defined')
        if self.cls is not None \
                and self.template is not None:
            raise Exception('Cannot use cls and template at the same time')

    def get_count(self):
        raise NotImplementedError()

    def get_item(self, index):
        raise NotImplementedError()

    # Returns a view instance for an item.
    def get_view(self, index):
        item = self.get_item(index)
        if item is None:
            return None

        item_args = None
        if self.args_converter:
            item_args = self.args_converter(item)
        else:
            item_args = item

        if self.cls:
            print 'CREATE VIEW FOR', index
            instance = self.cls(**item_args)
            return instance
        else:
            return Builder.template(self.template, **item_args)
