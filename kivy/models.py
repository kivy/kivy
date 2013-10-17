'''
Data Models
===========

.. versionadded:: 1.5

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

Data Model Classes
------------------

Kivy is open about the type of data used in applications built with the system.
However, base classes are needed for use with the selection system.

A :class:`SelectableDataItem` can be used as a mixin to build data objects that
are compatible with Kivy's selection system, which works with adapters and
similar classes, and with views such as a :class:`~kivy.uix.listview.ListView`.
The ksel attribute is a requirement.

The default operation of the selection system is to not propogate selection of
view instances in views such as ListView to the underlying data -- selection is
by default a view-only operation (VIEW_ON_DATA selection scheme). However, in
some cases, it is useful to propogate selection to the actual data items, and
vice versa. See the docs for Selection.

You may build your own Python data model system as the backend for a Kivy
application. Add a SelectionTool attr called ksel to implement selection.

For selection schemes involving data items that completely drive selection
(DATA_DRIVEN), or that are in a two-way coupling with views
(DATA_VIEW_COUPLED).

.. versionchanged:: 1.8

    Moved to kivy/, because models are not specific to adapters.

    Added ksel. ksel stands for "Kivy selection" and is an instance of
    SelectionTool, a class containing the selection state and helper methods.

'''

__all__ = ('SelectableDataItem',)

from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.selection import SelectionTool


class SelectableDataItem(EventDispatcher):
    '''A mixin class containing requirements for selection operations.
    '''

    ksel = ObjectProperty(SelectionTool(False))
    '''ksel stands for "Kivy selection" and is an instance of SelectionTool, a
    class containing the selection state and helper methods.

    .. versionadded:: 1.8

    :data:`ksel` is a
    :class:`~kivy.properties.ObjectProperty`, default to SelectionTool(False).
    '''

    def __init__(self, **kwargs):
        super(SelectableDataItem, self).__init__(**kwargs)
        if 'ksel' not in kwargs:
            self.ksel = SelectionTool(False)


class SelectableStringItem(SelectableDataItem):
    text = StringProperty('')

    def __init__(self, **kwargs):
        super(SelectableStringItem, self).__init__(**kwargs)
