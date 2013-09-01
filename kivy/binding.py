from kivy.enums import binding_modes
from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty

__all__ = ('Binding', )


class Binding(EventDispatcher):
    '''The Binding class is used in constructing arguments to controllers,
    adapters, widgets, and other containers of properties, for which bindings
    need to be done between properties.

    In Kivy versions < 1.8, you would instantiate the container, then set up
    bindings. Use of the Binding class is a different way of accomplishing the
    same thing.

    Prior to Kivy 1.8, you might do:

        list_adapter_one = ListAdapter(data=[ some data ],
                                       allow_empty_selection=False,
                                       selection_mode='multiple',
                                       other params, ...)

        list_adapter_two = ListAdapter(data=[],
                                       other params, ...)

        list_adapter_one.bind(selection=list_adapter_two.setter('data')

    With Kivy 1.8, you can do this instead:

        list_adapter_one = ListAdapter(data=[ some data ],
                                       allow_empty_selection=False,
                                       selection_mode='multiple',
                                       other params, ...)

        list_adapter_two = ListAdapter(data=Binding(source=list_adapter_one,
                                                    prop='selection')
                                       other params, ...)

    That is only one line difference, but it changes the mental model a little
    bit, and opens up other possibilities, and there can be more line savings.

    There is a transform param for Binding for a function that is to be applied
    to the bound property before it is set on the target. For example, if we
    want to bind to list_adapter_one's selection, but filter the items for,
    say, their bool value for something:

        list_adapter_two = ListAdapter(
                data=Binding(source=list_adapter_one,
                             prop='selection',
                             transform=FilterProperty(lamda d: d.bool))
                other params, ...)

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

    For short functions, as above, lambda works well. A normal function can
    also be used:

        def my_big_filter(item):
            app = App.app()
            return item.bool and (item.factor1 * item_factor2) > app.threshold

        list_adapter_two = ListAdapter(
                data=Binding(source=list_adapter_one,
                             prop='selection',
                             transform=FilterProperty(my_big_filter))
                other params, ...)

    In even more advanced use, if the filter function needs to make
    calculations from dependencies, specify those dependencies in the
    FilterProperty as (owner, prop_name) tuples:

        app = App.app()

        def my_bigger_filter(item):
            if (item.bool
                    and (item.factor1 * item_factor2) > app.threshold
                    and item.rate > app.monitor.minimum_rate
                    and item.rate < app.monitor.system_limit):
                return True
            return False

        list_adapter_two = ListAdapter(
            data=Binding(
                source=list_adapter_one,
                prop='selection',
                transform=FilterProperty(my_bigger_filter,
                                         bind=[(app, 'threshold'),
                                               (app.monitor, 'minimum_rate',
                                               (app.monitor, 'system_limit')))
                other params, ...)

    Now the data will be filtered by my_bigger_filter(), which will be
    re-applied whenever app.threshold, or app.monitor.minimum_rate or
    app.monitor.system_limit change.

    The Binding class is also useful in situations where bindings need to be
    stored, and reconnected, reapplied. For this reason, there are target and
    target_prop attributes.
    '''

    target = ObjectProperty(None)
    target_prop = StringProperty('')
    source = ObjectProperty(None)
    prop = StringProperty('')
    mode = StringProperty(binding_modes.ONE_WAY)
    transform = ObjectProperty(None, allownone=True)
