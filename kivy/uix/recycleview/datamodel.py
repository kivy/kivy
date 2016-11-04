'''
RecycleView Data Model
======================

.. versionadded:: 1.9.2

The data model part of the RecycleView model-view-controller pattern.

It defines the models (classes) that store the data associated with a
:class:`~kivy.uix.recycleview.RecycleViewBehavior`. Each model (class)
determines how the data is stored and emits requests to the controller
(:class:`~kivy.uix.recycleview.RecycleViewBehavior`) when the data is
modified.
'''

from kivy.properties import ListProperty, ObservableDict, ObjectProperty
from kivy.event import EventDispatcher
from functools import partial

__all__ = ('RecycleDataModelBehavior', 'RecycleDataModel')


def recondition_slice_assign(val, last_len, new_len):
    if not isinstance(val, slice):
        return slice(val, val + 1)

    diff = new_len - last_len

    start, stop, step = val.start, val.stop, val.step
    if stop <= start:
        return slice(0, 0)

    if step is not None and step != 1:
        assert last_len == new_len
        if stop < 0:
            stop = max(0, last_len + stop)
        stop = min(last_len, stop)

        if start < 0:
            start = max(0, last_len + start)
        start = min(last_len, start)

        return slice(start, stop, step)

    if start < 0:
        start = last_len + start
    if stop < 0:
        stop = last_len + stop

    # whatever, too complicated don't try to compute it
    if (start < 0 or stop < 0 or start > last_len or stop > last_len or
            new_len != last_len):
        return None

    return slice(start, stop)


class RecycleDataModelBehavior(object):
    """:class:`RecycleDataModelBehavior` is the base class for the models
    that describes and provides the data for the
    :class:`~kivy.uix.recycleview.RecycleViewBehavior`.

    :Events:
        `on_data_changed`:
            Fired when the data changes. The event may dispatch
            keyword arguments specific to each implementation of the data
            model.
            When dispatched, the event and keyword arguments are forwarded to
            :meth:`~kivy.uix.recycleview.RecycleViewBehavior.\
refresh_from_data`.
    """

    __events__ = ("on_data_changed", )

    recycleview = ObjectProperty(None, allownone=True)
    '''The
    :class:`~kivy.uix.recycleview.RecycleViewBehavior` instance
    associated with this data model.
    '''

    def attach_recycleview(self, rv):
        '''Associates a
        :class:`~kivy.uix.recycleview.RecycleViewBehavior` with
        this data model.
        '''
        self.recycleview = rv
        if rv:
            self.fbind('on_data_changed', rv.refresh_from_data)

    def detach_recycleview(self):
        '''Removes the
        :class:`~kivy.uix.recycleview.RecycleViewBehavior`
        associated with this data model.
        '''
        rv = self.recycleview
        if rv:
            self.funbind('on_data_changed', rv.refresh_from_data)
        self.recycleview = None

    def on_data_changed(self, *largs, **kwargs):
        pass


class RecycleDataModel(RecycleDataModelBehavior, EventDispatcher):
    '''A implementation of :class:`RecycleDataModelBehavior` that keeps the
    data in a indexable list. See :attr:`data`.

    When data changes this class currently dispatches `on_data_changed`  with
    one of the following additional keyword arguments.

    `none`: no keyword argument
        With no additional argument it means a generic data change.
    `removed`: a slice or integer
        The value is a slice or integer indicating the indices removed.
    `appended`: a slice
        The slice in :attr:`data` indicating the first and last new items
        (i.e. the slice pointing to the new items added at the end).
    `inserted`: a integer
        The index in :attr:`data` where a new data item was inserted.
    `modified`: a slice
        The slice with the indices where the data has been modified.
        This currently does not allow changing of size etc.
    '''

    data = ListProperty([])
    '''Stores the model's data using a list.

    The data for a item at index `i` can also be accessed with
    :class:`RecycleDataModel` `[i]`.
    '''

    _last_len = 0

    def __init__(self, **kwargs):
        self.fbind('data', self._on_data_callback)
        super(RecycleDataModel, self).__init__(**kwargs)

    def __getitem__(self, index):
        return self.data[index]

    @property
    def observable_dict(self):
        '''A dictionary instance, which when modified will trigger a `data` and
        consequently an `on_data_changed` dispatch.
        '''
        return partial(ObservableDict, self.__class__.data, self)

    def attach_recycleview(self, rv):
        super(RecycleDataModel, self).attach_recycleview(rv)
        if rv:
            self.fbind('data', rv._dispatch_prop_on_source, 'data')

    def detach_recycleview(self):
        rv = self.recycleview
        if rv:
            self.funbind('data', rv._dispatch_prop_on_source, 'data')
        super(RecycleDataModel, self).detach_recycleview()

    def _on_data_callback(self, instance, value):
        last_len = self._last_len
        new_len = self._last_len = len(self.data)
        op, val = value.last_op

        if op == '__setitem__':
            val = recondition_slice_assign(val, last_len, new_len)
            if val is not None:
                self.dispatch('on_data_changed', modified=val)
            else:
                self.dispatch('on_data_changed')
        elif op == '__delitem__':
            self.dispatch('on_data_changed', removed=val)
        elif op == '__setslice__':
            val = recondition_slice_assign(slice(*val), last_len, new_len)
            if val is not None:
                self.dispatch('on_data_changed', modified=val)
            else:
                self.dispatch('on_data_changed')
        elif op == '__delslice__':
            self.dispatch('on_data_changed', removed=slice(*val))
        elif op == '__iadd__' or op == '__imul__':
            self.dispatch('on_data_changed', appended=slice(last_len, new_len))
        elif op == 'append':
            self.dispatch('on_data_changed', appended=slice(last_len, new_len))
        elif op == 'insert':
            self.dispatch('on_data_changed', inserted=val)
        elif op == 'pop':
            if val:
                self.dispatch('on_data_changed', removed=val[0])
            else:
                self.dispatch('on_data_changed', removed=last_len - 1)
        elif op == 'extend':
            self.dispatch('on_data_changed', appended=slice(last_len, new_len))
        else:
            self.dispatch('on_data_changed')
