import collections

from kivy.binding import Binding
from kivy.enums import binding_modes

__all__ = ('parse_binding', 'bind_binding')


def parse_binding(arg_name, kwargs):

    binding = None

    if arg_name in kwargs:
        val = kwargs[arg_name]

        if isinstance(val, Binding):
            binding = kwargs[arg_name]
            binding.target_prop = arg_name

            # If the property name was not provided, assume it is 'data', which
            # is the most common property name in controllers and adapters.
            if not binding.prop:
                binding.prop = 'data'

            if binding.mode is None:
                binding.mode = binding_modes.ONE_WAY

            prop_val = getattr(binding.source, binding.prop)

            if binding.mode == binding_modes.FIRST_ITEM:
                if prop_val and isinstance(prop_val, collections.Iterable):
                    prop_val = prop_val[0]
                else:
                    prop_val = None

            kwargs[arg_name] = prop_val

        elif isinstance(val, tuple):

            owner, prop = val
            kwargs[arg_name] = getattr(owner, prop)

    return binding, kwargs


def bind_binding(target, binding):

    binding.target = target

    if binding.mode == binding_modes.ONE_WAY:
        binding.source.bind(
            **{binding.prop: binding.target.setter(binding.target_prop)})
    elif binding.mode == binding_modes.FIRST_ITEM:
        if binding.target_prop == 'data':
            binding.source.bind(
                **{binding.prop: binding.target.update_data_from_first_item})
        elif binding.target_prop == 'subject':
            binding.source.bind(
                **{binding.prop: binding.target.update_subject_from_first_item})
        elif binding.target_prop == 'selection':
            binding.source.bind(
                **{binding.prop:
                    binding.target.update_selection_from_first_item})
        elif binding.target_prop == 'sorted_keys':
            binding.source.bind(
                **{binding.prop:
                    binding.target.update_sorted_keys_from_first_item})

    return binding
