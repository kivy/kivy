__all__ = ('SimpleListAdapter', )

from kivy.adapters.args_converters import list_item_args_converter
from kivy.adapters.listadapter import ListAdapter
from kivy.properties import ObjectProperty


class SimpleListAdapter(ListAdapter):
    args_converter = ObjectProperty(list_item_args_converter)
