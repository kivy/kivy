'''
ObjectAdapter
=============

.. versionadded:: 1.4

'''

from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.adapters.adapter import Adapter


class ObjectAdapter(Adapter):
    '''ObjectAdapter is an adapter around a simple Python object.

    From Adapter, ObjectAdapter gets these properties:

        Use only one:

            - cls, for a list item class to use to instantiate a view
                   instance

            - template, a kv template to use to instantiate a view
                        instance

        - args_converter, an optional function to transform the object
                          in preparation for either a cls instantiation,
                          or a kv template invocation
    '''

    obj = ObjectProperty(None)
    '''The obj property contains the object (can be a string) that will be
    used directly if no args_converter function is provided. If there is an
    args_converter, the object will be passed to it, for instantiation of the
    view class (cls) instance based on it.
    '''

    property_binding = ObjectProperty(None)
    '''A tuple with the object and its property, (object, property)
    '''

    selection_binding = ObjectProperty(None)
    '''A list adapter, whose selection will be used to get obj.
    '''

    def __init__(self, **kwargs):
        if not self.args_check(**kwargs):
            msg = 'adapter args: obj, selection_binding, OR property_binding'
            raise Exception(msg)
        super(ObjectAdapter, self).__init__(**kwargs)

        if self.selection_binding is not None:
            if len(self.selection_binding.selection) > 0:
                self.obj = self.selection_binding.selection[0]
            self.selection_binding.bind(
                    on_selection_change=self.update_from_selection)
        elif self.property_binding is not None:
            owner,prop = self.property_binding
            self.obj = owner.prop
            owner.bind(prop=self.update_from_property)

    def args_check(self, **kwargs):
        found = []
        if 'obj' in kwargs:
            found.append('obj')
        if 'selection_binding' in kwargs:
            found.append('selection_binding')
        if 'property_binding' in kwargs:
            found.append('property_binding')
        if len(found) > 1:
            return False
        return True

    def get_view(self):
        if self.obj is None:
            return None

        obj_args = None
        if self.args_converter:
            obj_args = self.args_converter(self.obj)
        else:
            obj_args = self.obj

        if self.cls:
            print 'CREATE VIEW FOR', self.obj
            print 'obj_args', obj_args
            instance = self.cls(**obj_args)
            return instance
        else:
            return Builder.template(self.template, **obj_args)

    def update_from_selection(self, adapter, *args):
        print 'update_from_selection', adapter, args
        if len(adapter.selection) > 0:
            self.obj = adapter.selection[0]
        else:
            self.obj = ''

    def update_from_property(self, owner, *args):
        print 'update_from_property', owner, args
        prop = self.property_binding[1]
        self.obj = owner.prop
