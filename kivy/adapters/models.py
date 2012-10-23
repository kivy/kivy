'''
Data Models
===========

Kivy is open about the type of data used in applications built with
the system. However, base classes are optionally needed to conform data to
requirements of some parts of the system.

:class:`SelectableDataItem` is a basic `Python data model`_ class that can be
used as a mixin to build data objects that are compatible with Kivy's adapter
and selection system, which works with views such as ListView. The boolean
property is_selected is the requirement.

The default operation of the selection system is to not propogate selection in
views such as ListView to the underlying data -- selection is by default a
view-only operation. However, in some cases, it is useful to propogate
selection to the actual data items.

You may, of course, build your own Python data model system as the backend for
a Kivy application. For instance, to use the `Google App Engine datamodeling`_
system with Kivy, this class could be redefined as:

    from google.appengine.ext import db

    class SelectableDataItem(db.Model):
        ... other properties
        is_selected = db.BooleanProperty()

.. _Python data model: http://docs.python.org/reference/datamodel.html

.. _Google App Engine datamodeling:
https://developers.google.com/appengine/docs/python/datastore/datamodeling
'''

class SelectableDataItem(object):
    '''
    A mixin class containing requirements for selection operations.

    This is the is_selected boolean.
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
