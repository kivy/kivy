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

from kivy.binding import Binding
from kivy.controllers.controller import Controller
from kivy.enums import binding_modes
from kivy.enums import binding_transforms
from kivy.properties import ObjectProperty
from kivy.properties import TransformInitInfo
from kivy.properties import TransformProperty

__all__ = ('TransformController, TransformListController', )


class TransformController(Controller):
    '''
    data, which is defined as an ObjectProperty in the Controller superclass,
    can be any Controller, including a list, a dict, etc. transform is a
    TransformProperty, which by default will operated on a sibling property
    called data.  transform has a default func as a lambda that simply sets the
    item, with no transform applied. Set transform.func if a transform should
    be applied.
    '''
    subject = ObjectProperty(None, allownone=True)
    data = TransformProperty(subject='subject',
                             op=binding_transforms.TRANSFORM,
                             func=lambda data: data)

    def __init__(self, **kwargs):

        data_binding, kwargs = self.handle_initial_value('data', kwargs)

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
            self.bind_binding(self, data_binding)

    def handle_initial_value(self, arg_name, kwargs):

        binding = None

        if arg_name in kwargs:
            val = kwargs[arg_name]

            if isinstance(val, Binding):

                binding = kwargs[arg_name]
                binding.target_prop = arg_name

                # If the property name was not provided, assume it is 'data',
                # which is the main property name in controllers.
                if not binding.prop:
                    binding.prop = 'data'

                if binding.mode is None:
                    binding.mode = binding_modes.ONE_WAY

                prop_val = val.get_value()

                if binding.mode == binding_modes.FIRST_ITEM:
                    if prop_val and isinstance(prop_val, collections.Iterable):
                        prop_val = prop_val[0]
                    else:
                        prop_val = None

                kwargs[arg_name] = prop_val

            elif isinstance(val, tuple):

                # TODO: Additional checks, for owner and prop?
                if len(val) == 2:
                    owner, prop = val
                    kwargs[arg_name] = getattr(owner, prop)
                    binding = Binding(source=owner, prop=prop)

            else:
                if not isinstance(val, list):
                    raise Exception(('Argument {} was not provided with a '
                                     'list, an (owner, prop) tuple value nor '
                                     'a Binding with source, prop, other '
                                     'args.').format(arg_name))

        return binding, kwargs

    def bind_binding(self, target, binding):

        binding.target = target

        if binding.mode == binding_modes.ONE_WAY:

            if binding.transform:
                binding.source.bind(
                    **{binding.prop: binding.transform})

        elif binding.mode == binding_modes.TWO_WAY:

            if binding.transform:
                binding.source.bind(
                    **{binding.prop: binding.transform})

            binding.target.bind(
                **{binding.target_prop: binding.source.setter(binding.prop)})

        elif binding.mode == binding_modes.FIRST_ITEM:

            if binding.transform:
                binding.source.bind(
                    **{binding.prop: binding.transform})

        return binding
