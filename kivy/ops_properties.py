from UserList import UserList
from kivy.event import EventDispatcher
from kivy.properties import DictProperty
from kivy.properties import ObjectProperty


class ListOpInfo(object):
    def __init__(self, op_name, start_index, end_index):
        self.op_name = op_name
        self.start_index = start_index
        self.end_index = end_index


class RecordingObservableList(EventDispatcher, UserList):
    '''This class is used as a cls argument to
    :class:`~kivy.properties.ListProperty` as an alternative to the default
    :class:`~kivy.properties.ObservableList`.

    :class:`~kivy.adapters.list_ops.RecordingObservableList` is used to record
    change info about a list instance, in a more detailed, per-op manner than a
    :class:`~kivy.properties.ObservableList` instance, which dispatches grossly
    for any change, but with no info about the change.

    Range-observing and granular (per op) data is stored in op_info and
    sort_op_info for use by an observer.
    '''

    lp = ObjectProperty(None)
    owner = ObjectProperty(None)

    op_info = ObjectProperty(None)
    sort_op_info = ObjectProperty(None)
    sort_largs = ObjectProperty(None)
    sort_kwds = ObjectProperty(None)

    presort_indices_and_items = DictProperty({})
    '''This temporary association has keys as the indices of the adapter's
    cached_views and the adapter's data items, for use in post-sort widget
    reordering.  It is set by the adapter when needed.  It is cleared by the
    adapter at the end of its sort op callback.
    '''

    def __init__(self, *largs):
        # largs are:
        #
        #     ListProperty instance
        #     Owner instance (e.g., an adapter)
        #     value
        #
        super(RecordingObservableList, self).__init__()
        self.lp = largs[0]
        self.owner = largs[1]
        self.data = largs[2]

    def set(self, val):
        self.__set__(val)

    def __set__(self, val):
        self.data = val
        self.op_info = ListOpInfo('ROL_set', 0, 0)

    # TODO: setitem and delitem are supposed to handle slices, instead of the
    #       deprecated setslice() and delslice() methods.
    def __setitem__(self, key, value):
        self.data.__setitem__(key, value)
        self.op_info = ListOpInfo('ROL_setitem', key, key)

    def __delitem__(self, key):
        self.data.__delitem__(key)
        self.op_info = ListOpInfo('ROL_delitem', key, key)

    def __setslice__(self, *largs):
        #
        # Python docs:
        #
        #     operator.__setslice__(a, b, c, v)
        #
        #     Set the slice of a from index b to index c-1 to the sequence v.
        #
        #     Deprecated since version 2.6: This function is removed in Python
        #     3.x. Use setitem() with a slice index.
        #
        start_index = largs[0]
        end_index = largs[1] - 1
        self.data.__setslice__(*largs)
        self.op_info = ListOpInfo('ROL_setslice', start_index, end_index)

    def __delslice__(self, *largs):
        # Delete the slice of a from index b to index c-1. del a[b:c],
        # where the args here are b and c.
        # Also deprecated.
        start_index = largs[0]
        end_index = largs[1] - 1
        self.data.__delslice__(*largs)
        self.op_info = ListOpInfo('ROL_delslice', start_index, end_index)

    def __iadd__(self, *largs):
        start_index = len(self)
        end_index = start_index + len(largs) - 1
        self.data.__iadd__(*largs)
        self.op_info = ListOpInfo('ROL_iadd', start_index, end_index)

    def __imul__(self, *largs):
        num = largs[0]
        start_index = len(self)
        end_index = start_index + (len(self) * num)
        self.data.__imul__(*largs)
        self.op_info = ListOpInfo('ROL_imul', start_index, end_index)

    def append(self, *largs):
        index = len(self)
        self.data.append(*largs)
        self.op_info = ListOpInfo('ROL_append', index, index)

    def remove(self, *largs):
        index = self.index(largs[0])
        self.data.remove(*largs)
        self.op_info = ListOpInfo('ROL_remove', index, index)

    def insert(self, *largs):
        index = largs[0]
        self.data.insert(*largs)
        self.op_info = ListOpInfo('ROL_insert', index, index)

    def pop(self, *largs):
        if largs:
            index = largs[0]
        else:
            index = len(self) - 1
        result = self.data.pop(*largs)
        self.op_info = ListOpInfo('ROL_pop', index, index)
        return result

    def extend(self, *largs):
        start_index = len(self)
        end_index = start_index + len(largs[0]) - 1
        self.data.extend(*largs)
        self.op_info = ListOpInfo('ROL_extend', start_index, end_index)

    def start_sort_op(self, op, *largs, **kwds):
        self.sort_largs = largs
        self.sort_kwds = kwds
        self.sort_op = op

        # Trigger the "sort is starting" callback to the adapter, so it can do
        # pre-sort writing of the current arrangement of indices and data.
        self.sort_op_info = ListOpInfo('ROL_sort_start', 0, 0)

    def finish_sort_op(self):
        largs = self.sort_largs
        kwds = self.sort_kwds
        sort_op = self.sort_op

        # Perform the sort.
        if sort_op == 'ROL_sort':
            self.data.sort(*largs, **kwds)
        else:
            self.data.reverse(*largs)

        # Finalize. Will go back to adapter for handling cached_views,
        # selection, and prep for triggering data_changed on ListView.
        self.op_info = ListOpInfo(sort_op, 0, len(self) - 1)

    def sort(self, *largs, **kwds):
        self.start_sort_op('ROL_sort', *largs, **kwds)

    def reverse(self, *largs):
        self.start_sort_op('ROL_reverse', *largs)


class ListOpHandler(object):
    '''A :class:`ListOpHandler` reacts to the following operations that are
    possible for a RecordingObservableList (ROL) instance, categorized as
    follows:

        Adding and inserting:

            ROL_append
            ROL_extend
            ROL_insert

        Applying operator:

            ROL_iadd
            ROL_imul

        Setting:

            ROL_setitem
            ROL_setslice

        Deleting:

            ROL_delitem
            ROL_delslice
            ROL_remove
            ROL_pop

        Sorting:

            ROL_sort
            ROL_reverse
    '''

    def data_changed(self, *args):
        '''This method receives the callback for a data change to
        self.source_list, and calls the appropriate methods, reacting to
        cover the possible operation events listed above.
        '''
        pass
