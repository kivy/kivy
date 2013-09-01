__all__ = ('selection_update_methods',
           'selection_schemes',
           'binding_modes',
           'binding_transforms', )


# TODO: Python 3.4 has an Enum. How to use and work with 2.7?
#       And, is this the best implementation?
#       See ('http://stackoverflow.com/questions/36932/'
#            'how-can-i-represent-an-enum-in-python)
class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError


class SelectionUpdateMethodsEnum(Enum):
    '''An enum used in the Selection class, to configure how updating of model
    data items is to be done:

        * NOTIFY:

            - Use Kivy's events system to notify observers of selectable
              items for changes (Set initial value, but after that, update via
              bindings).

        * SET:

            - When selection of view item happens, propagate to the associated
              item by direct call.

    Set selection_update_method in combination with setting selection_scheme.
    See the SelectionSchemesEnum class here, and the Selection class.
    '''
    def __init__(self):
        super(SelectionUpdateMethodsEnum, self).__init__([
            'NOTIFY', 'SET'])


class SelectionSchemesEnum(Enum):
    '''An enum used in the Selection class, with choices:

        * VIEW_ON_DATA:

            - selection state is loaded from data for view creation

            - data selection IS NOT updated from selection on views

        * VIEW_DRIVEN:

            - selection state is loaded from data for view creation

            - data selection IS updated from selection on views

        * DATA_DRIVEN:

            - selection state is loaded from data for view creation

            - view selection is updated from selection on data

            - view selection in the UI may be inactive, or may augment
              selection driven by data

        * DATA_VIEW_COUPLED:

            - selection state is loaded from data for view creation

            - view selection is updated from selection on data

            - data selection is updated from selection on views

        * OBJECT:

            - selection for a single set of objects, which can be anything

    .. versionadded:: 1.8

    '''

    def __init__(self):
        super(SelectionSchemesEnum, self).__init__([
            'VIEW_ON_DATA', 'VIEW_DRIVEN', 'DATA_DRIVEN',
            'DATA_VIEW_COUPLED', 'OBJECT'])


class BindingModeEnum(Enum):
    '''An enum used for choices of binding mode:

        * ONE_WAY:

            - the normal to-object binding (This is the default, if omitted)

        * TWO_WAY:

            - bidirectional binding between two objects

        * FIRST_ITEM:

            - bind to list, but use the first item for value
    '''
    #
    # TODO: Implement TWO_WAY.
    #
    # TODO: SproutCore was inspirational for this work, but the following
    #       treatment seems good: ('http://msdn.microsoft.com/en-us/library/'
    #                              'system.windows.data.bindingmode.aspx.')
    #
    # Their OneWayToSource, seems the equivalent of REVERSE, but why couldn't
    # another binding be done instead?
    #
    # Do we need a ONE_TIME like theirs?
    #
    def __init__(self):
        super(BindingModeEnum, self).__init__([
            'ONE_WAY', 'FIRST_ITEM', 'TWO-WAY'])


class BindingTransformsEnum(Enum):
    '''An enum for TransformProperty op choices, which select between:

        * TRANSFORM:

            - TransformProperty

        * FILTER:

            - FilterProperty

        * MAP:

            - MapProperty
    '''
    def __init__(self):
        super(BindingTransformsEnum, self).__init__([
            'TRANSFORM', 'FILTER', 'MAP'])


selection_update_methods = SelectionUpdateMethodsEnum()
selection_schemes = SelectionSchemesEnum()
binding_modes = BindingModeEnum()
binding_transforms = BindingTransformsEnum()
