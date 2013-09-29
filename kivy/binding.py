from collections import Iterable

from kivy.enums import binding_modes
#from kivy.event import EventDispatcher
from kivy.properties import AliasProperty
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.uix.widget import Widget

__all__ = ('Binding', )


#class Binding(EventDispatcher):
# TODO: Changed to Widget for kv. Change kv?
class Binding(Widget):
    '''The Binding class is used in constructing arguments to controllers,
    adapters, widgets, and other containers of properties, for which bindings
    need to be done between properties.

    The transform param can be one of:

        TransformProperty - apply func to source/prop, where source/prop can be
                            anything, such as a simple object, a list, a dict,
                            etc., but with the source/prop acted on as an
                            object (FilterProperty and MapProperty, in
                            contrast, apply the func to each item in a list).

                          - the calling signature for the transform func is
                            func(source, prop)

        FilterProperty - apply func as a filter() on source/prop, where
                         source/prop needs to be an iterable

                       - the calling signature for the filter func is
                         func(item), for each item in the source/prop list

        MapProperty - apply func as a map() on source/prop, where source/prop
                      needs to be an iterable

                    - the calling signature for the map func is func(item), for
                      each item in the source/prop list

    '''

    target = ObjectProperty(None)
    target_prop = StringProperty('data')
    source = ObjectProperty(None)
    prop = StringProperty('data')
    mode = StringProperty(binding_modes.ONE_WAY)
    transform = ObjectProperty(None, allownone=True)

    _value = ObjectProperty(None, allownone=True)

    def get_value(self):
        return self._value

    def set_value(self, value):
        if not hasattr(self.source, self.prop):
            self._value = None
        if isinstance(value, Binding):
            self._value = value.get_value()
        else:
            v = value
            if self.mode == binding_modes.FIRST_ITEM:
                if v and isinstance(value, Iterable):
                    v = value[0]
                else:
                    v = None
            self._value = self.transform(v) if self.transform else v

    value = AliasProperty(get_value, set_value)

    def __init__(self, **kwargs):

        super(Binding, self).__init__(**kwargs)

        if not self.source or not self.prop:
            return

        print 'Binding', self.source, self.prop
        self.source.bind(**{self.prop: self.setter('value')})

    def bind_to(self, target, target_prop):
        self.bind(_value=target.setter(target_prop))

    def bind_callback(self, callback):
        self.bind(_value=callback)


class DataBinding(Binding):

    def __init__(self, **kwargs):
        kwargs['target_prop'] = 'data'
        super(DataBinding, self).__init__(**kwargs)


class SelectionBinding(Binding):

    def __init__(self, **kwargs):
        kwargs['target_prop'] = 'selection'
        super(SelectionBinding, self).__init__(**kwargs)
