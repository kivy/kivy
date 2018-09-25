'''
SelectableView
==============

.. deprecated:: 1.10.0
    The feature has been deprecated.

This module houses the :class:`SelectableView` mixin class. This is used by
the :class:`~kivy.uix.listview.ListView` and it's associated
:mod:`Adapters <kivy.adapters>` to provide selection behaviour
when presenting large lists.

'''

from kivy.properties import NumericProperty, BooleanProperty
from kivy.utils import deprecated


class SelectableView(object):
    '''The :class:`SelectableView` mixin is used with list items and other
    classes that are to be instantiated in a list view or other classes
    which use a selection-enabled adapter such as ListAdapter. select() and
    deselect() can be overridden with display code to mark items as
    selected or not, if desired.
    '''

    index = NumericProperty(-1)
    '''The index into the underlying data list or the data item this view
    represents.
    '''

    is_selected = BooleanProperty(False)
    '''A SelectableView instance carries this property which should be kept
    in sync with the equivalent property the data item represents.
    '''

    @deprecated
    def __init__(self, **kwargs):
        super(SelectableView, self).__init__(**kwargs)

    def select(self, *args):
        '''The list item is responsible for updating the display when
        being selected, if desired.
        '''
        self.is_selected = True

    def deselect(self, *args):
        '''The list item is responsible for updating the display when
        being unselected, if desired.
        '''
        self.is_selected = False
