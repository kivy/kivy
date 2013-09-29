__all__ = ('binding_modes',
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
    # Their OneWayToSource, seems the equivalent of a reverse, but why couldn't
    # another binding be done instead?
    #
    # Do we need a ONE_TIME like theirs? SproutCore has something like this,
    # for when you want to have something happen once. Kivy has something
    # already for schedule...
    #
    def __init__(self):
        super(BindingModeEnum, self).__init__([
            'ONE_WAY', 'FIRST_ITEM', 'TWO_WAY'])


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


binding_modes = BindingModeEnum()
binding_transforms = BindingTransformsEnum()
