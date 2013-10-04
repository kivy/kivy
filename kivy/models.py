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
However, base classes for data are needed for use with the selection system.

A :class:`SelectableDataItem` can be used as a mixin to build data objects that
are compatible with Kivy's selection system, which works with controllers
and similar classes, and with views such as a
:class:`~kivy.uix.listview.ListView`.  The ksel attribute is a requirement.

A :class:`SelectableStringItem` is a wrapper for a simple string, useful for
simple lists. It contains a text StringProperty.

You may wish to adapt data, in whatever form, by adding a 'ksel' instance to
each item, which is an instance of :class:`kivy.selection.SelectionTool`.

.. versionchanged:: 1.8

    Moved to kivy/, because models are not specific to adapters.

    Added ksel. ksel stands for "Kivy selection" and is an instance of
    SelectionTool, a class containing the selection state and helper methods.

    Added the SelectableStringItem class.
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
