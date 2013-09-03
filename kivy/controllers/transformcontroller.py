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
import collections

from kivy.controllers.controller import Controller
from kivy.controllers.utils import parse_binding
from kivy.controllers.utils import bind_binding
from kivy.enums import binding_transforms
from kivy.properties import ObjectProperty
from kivy.properties import TransformInitInfo
from kivy.properties import TransformProperty

__all__ = ('TransformController', )


class TransformController(Controller):
    '''
    data, which is defined as an ObjectProperty in the Controller superclass,
    can be any Controller, including a list, a dict, etc. transform is a
    TransformProperty, which by default will operated on a sibling property
    called data.  The transform TransformProperty has a default func as a
    lambda that simply sets the item, with no transform applied. Set
    transform.func if a transform should be applied.
    '''
    subject = ObjectProperty(None, allownone=True)
    data = TransformProperty(subject='subject',
                             op=binding_transforms.TRANSFORM,
                             func=lambda data: data)

    def __init__(self, **kwargs):

        data_binding, kwargs = parse_binding('data', kwargs)

        if data_binding:
            if data_binding.transform:
                if isinstance(data_binding.transform, tuple):
                    if len(data_binding.transform) == 2:
                        op, func = data_binding.transform
                    else:
                        op = binding_transforms.TRANSFORM
                        func = data_binding.transform[0]
                else:
                    op = binding_transforms.TRANSFORM
                    func = data_binding.transform

                data_binding.target_prop = 'subject'
                kwargs['subject'] = kwargs.pop('data')
                kwargs['data'] = TransformInitInfo(op, func)

        super(TransformController, self).__init__(**kwargs)

        if data_binding:
            bind_binding(self, data_binding)

    def update_data_from_first_item(self, *args):
        l = args[1]
        if l:
            self.data = l[0]

    def update_subject_from_first_item(self, *args):
        # Set data as the first item.
        d = args[1]
        if isinstance(d, collections.Iterable):
            if d:
                self.subject = d[0]
