'''
ObjectAdapter
=============

.. versionadded:: 1.4

:class:`ObjectAdapter` is an adapter around a Python object, which can be a
string, a list, or any sort of object. Often the object is a string used as a
key for selection operations.

From Adapter, ObjectAdapter gets these properties:

    Use only one:

        - cls, for a list item class to use to instantiate a view
               instance

        - template, a kv template to use to instantiate a view
                    instance

    - args_converter, an optional function to transform the object
                      in preparation for either a cls instantiation,
                      or a kv template invocation

:class:`ObjectAdapter` gets its obj property from either a direct obj argument
or the obj_bind_from argument, either a (cls,property) tuple or a
list_adapter. If (cls, property) is provided, a binding is set up from
cls.property to self.update_from_property(). If a list_adapter is provided,
the first object in the list_adapter's selection, if it exists, is bound to
the alternative update method, self.update_from_selection(). So, selection
mode for the list adapter is assumed to be single-selection; if there are
multiple objects in the list adapter's selection, only the first is taken as
obj.

Having the obj binding handled this way generalizes, and relieves from the
developer the task of setting the binding up post-instantiation. If the obj is
not provided directly, a binding has to be set up, but this way it is done
more explictly, with specification in the arguments.

:class:`ObjectAdapter` has a get_view() method that works like the one in
:class:`ListAdapter`. get_view() builds a view instance using either a class
provided in the cls argument or using a kv template. If an args_converter
function is provided, it is applied to the obj to create obj_args for the
instantiation. Otherwise, the obj itself is taken as obj_args.
'''

from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.adapters.adapter import Adapter


class ObjectAdapter(Adapter):

    obj = ObjectProperty(None)
    '''The obj property contains the object (can be a string) that will be
    used directly if no args_converter function is provided. If there is an
    args_converter, the object will be passed to it, for instantiation of the
    view class (cls) instance based on it.
    '''

    obj_bind_from = ObjectProperty(None)
    '''This is the "from" side of a binding to get obj. It can be one of
    these two choices:
    
        - a tuple with a cls and a property (cls, property), that
          is used to set up a binding from cls.property to self.update
    
        - a list adapter, whose selection will be used to set up a binding
          from list_adapter.selection[0]
    '''

    def __init__(self, **kwargs):
        if 'obj' in kwargs and 'obj_bind_from' in kwargs:
            raise Exception('object adapter args: obj itself or obj_bind_from'
        if 'obj' not in kwargs and 'obj_bind_from' not in kwargs:
            raise Exception('object adapter: need obj or obj_bind_from arg'
        super(ObjectAdapter, self).__init__(**kwargs)

        if type(self.obj_bind_from) == 'tuple':
            cls,prop = self.obj_bind_from
            self.obj = cls.prop
            cls.bind(prop=self.update_from_property)
        elif self.obj_bind_from is not None:
            if len(self.obj_bind_from.selection) > 0:
                self.obj = self.obj_bind_from.selection[0]
            self.obj_bind_from.bind(
                    on_selection_change=self.update_from_selection)

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

    def update_from_property(self, cls, *args):
        print 'update_from_property', cls, args
        prop = self.obj_bind_from[1]
        self.obj = cls.prop
