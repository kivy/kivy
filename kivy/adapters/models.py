'''
SelectableDataItem
==================

.. versionadded:: 1.5

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

Data Models
-----------

Kivy is open about the type of data used in applications built with
the system. However, base classes are sometimes needed to ensure data conforms
to the requirements of some parts of the system.

A :class:`SelectableDataItem` is a basic Python data model class that can be
used as a mixin to build data objects that are compatible with Kivy's
:class:`~kivy.adapters.adapter.Adapter`
and selection system, which works with views such as a
:class:`~kivy.uix.listview.ListView`. The boolean
property is_selected is a requirement.

The default operation of the selection system is to not propogate selection in
views such as ListView to the underlying data -- selection is by default a
view-only operation. However, in some cases, it is useful to propogate
selection to the actual data items.

You may, of course, build your own Python data model system as the backend for
a Kivy application. For instance, to use the Google App Engine datamodeling
system with Kivy, this class could be redefined as::

    from google.appengine.ext import db

    class MySelectableDataItem(db.Model):
        ... other properties
        is_selected = db.BooleanProperty()

It is easy to build such a class with plain Python.

'''

__all__ = ('SelectableDataItem', )


class SelectableDataItem(object):
    '''
    A mixin class containing requirements for selection operations.

    This is the is_selected boolean property.
    '''

    def __init__(self, **kwargs):
        super(SelectableDataItem, self).__init__()

        self._is_selected = kwargs.get('is_selected', False)

    @property
    def is_selected(self):
        """Is the data item selected"""
        return self._is_selected

    @is_selected.setter
    def is_selected(self, value):
        self._is_selected = value
