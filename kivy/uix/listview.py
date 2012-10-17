'''
List View
===========

.. versionadded:: 1.5

The :class:`ListView` widget provides a scrollable/pannable viewport that is
clipped at the scrollview's bounding box, which contains a list of
list item view instances.

:class:`ListView` implements AbstractView as a vertical scrollable list.
From AbstractView we have these properties and methods:

    - adapter, an instance of SimpleListAdapter, ListAdapter, or DictAdapter

    - item_view_instances, a dict with indices as keys to the list item view
      instances created in the adapter

    - set_item_view() and get_item_view() methods to list item view instances

Basic Example
-------------

Here we make a listview with 100 items.

    from kivy.uix.listview import ListView
    from kivy.uix.gridlayout import GridLayout


    class MainView(GridLayout):

        def __init__(self, **kwargs):
            kwargs['cols'] = 2
            kwargs['size_hint'] = (1.0, 1.0)
            super(MainView, self).__init__(**kwargs)

            list_view = ListView(
                item_strings=[str(index) for index in xrange(100)])

            self.add_widget(list_view)


    if __name__ == '__main__':
        from kivy.base import runTouchApp
        runTouchApp(MainView(width=800))

Using a ListAdapter
-------------------

Behind the scenes, the basic example above uses
uses :class:`SimpleListAdapter`. When the constructor for
:class:`ListView` sees that only a list of strings is provided as an argument,
called item_strings, it creates an instance of :class:`SimpleListAdapter` with
the list of strings.

Simple in :class:`SimpleListAdapter` means: WITHOUT SELECTION SUPPORT -- it is
just a scrollable list of items, which do not respond to touch events.

To use :class:`SimpleListAdaper` explicitly in creating a ListView instance,
do:

    simple_list_adapter = \
        SimpleListAdapter(data=["Item #{0}".format(i) for i in xrange(100)],
                          cls=Label)
    list_view = ListView(adapter=simple_list_adapter)

SelectionSupport: ListAdapter and DictAdapter
---------------------------------------------

For many uses of a list, the data is more than a simple list or strings, or
selection functionality is needed.  :class:`ListAdapter` and
:class:`DictAdapter` each subclass :class:`SelectionSupport`.

See the :class:`ListAdapter` docs for details, but here we have synopses of
its arguments:

    - data: a list of Python class instances or dicts that must have
            a text property and an is_selected property.

            When working with classes as data items, the is_selected property
            is provided by :class:`SelectableDataItem`, which is intended to
            be used as a mixin:

                MyCustomDataItem(SelectableDataItem):
                    def __init__(self, **kwargs):
                        super(MyCustomDataItem, self).__init__(**kwargs)
                        self.text = kwargs.get('name', '')
                        # etc.

                data = [MyCustomDataItem(name=n) for n in ['Bill', 'Sally']

            Or, you may wish to provide a simple list of dicts:

                data = \
                    [{'text': str(i), 'is_selected': False} for i in [1,2,3]]

    - cls: a Kivy view that is to be instantiated for each list item. There
           are several built-in types available, including ListItemLabel and
           ListItemButton, or you can easily make your own.

    or

    - template: the name of a Kivy language (kv) template that defines the
                view

    NOTE: Pick only one, cls or template, to provide as an argument.

    - args_converter: a function that takes a list item object as input, and
                      uses the object to build and return an args dict, ready
                      to be used in a call to instantiate the item view cls or
                      template. In the case of cls, the args dict acts as a
                      kwargs object. For a template, it is treated as a context
                      (ctx), but is essentially similar in form. See the
                      examples and docs for template operation.

    - selection_mode: a string for: 'single', 'multiple' or others (See docs).

    - allow_empty_selection: a boolean, which if False, the default, forces
                             there to always be a selection, if there is data
                             available. If True, selection happens only as a
                             result of user action.

In narrative, we can summarize with:

    A listview's list adapter takes data items and uses an args_converter
    function to transform them into arguments for making list item view
    instances, using either a cls or a kv template.

In a graphic, a summary of the relationship between a listview and its
list adapter, looks like this:

    -                    ------------------- ListAdapter --------------------
    -                    |                                                  |
    -                    | <list item views> (cls or template) <data items> |
    -   ListView   -->   |                           [args_converter]       |
    -                    |                                                  |
    -                    |           <<< selection handling >>>             |
    -                    |                                                  |
    -                    ----------------------------------------------------

:class:`DictAdapter` has the same arguments and requirements as ListAdapter,
except for two things:

    1) There is an additional argument, sorted_keys, which must meet the
       requirements of normal python dictionary keys.

    2) The data argument is not a list of class instances, it is, as you would
       expect, a dict. Keys in the dict must include the keys in the
       sorted_keys argument, but they may form a superset of the keys in
       sorted_keys. Values may be class instances or dicts -- these follow the
       same rules as the items of the data argument, described above for
       :class:`ListAdapter`.

Using an Args Converter
-----------------------

:class:`ListView` allows use of built-in list item views, such as
:class:`ListItemButton`, your own custom item view class, or a custom kv
template. Whichever type of list item view is used, an args_converter function
is needed to prepare, per list data item, args for either a cls or template.

Here is an args_converter for use with the built-in :class:`ListItemButton`,
specified as a normal Python function:

    def args_converter(an_obj):
        return {'text': an_obj.text,
                'size_hint_y': None,
                'height': 25}

    and as a lambda:

    args_converter = lambda an_obj: {'text': an_obj.text,
                                     'size_hint_y': None,
                                     'height': 25}

In args converter example above, the data item is assumed to be an object
(class instance), hence the reference an_obj.text.

Here is an example of an args converter that works with list data items that
are dicts:

    args_converter = lambda obj: {'text': a_dict['text'],
                                  'size_hint_y': None,
                                  'height': 25}

So, it is the responsibility of the developer to code the args_converter
according to the data at hand.

**An args converter used with cls argument**

Inside the :class:`ListView` code, the args converter function is used with the
provided view argument, in this case cls:

    cls(**args_converter(data_item))

Here, if cls is ListItemButton, it would be equivalent to:

    ListItemButton(text=an_obj.text, size_hint_y=None, height=25)

for each list data item.

**An args converter used with a template argument**

In the case of a kv template used as a list item view, the args_converter will
provide the context for the template, not really an args dict strictly
speaking, but it looks the same inside :class:`ListView`:

    template(**args_converter(data_item))

The only difference between this args converter and the one above is
that the reference is to a dictionary (a_dict['text']), vs. reference to a
class instance (an_obj.text).

An Example ListView
-------------------

Now, to some example code:

    from kivy.adapters.list_adapter import ListAdapter
    from kivy.uix.listview import ListItemButton, ListView

    data = [{'text': str(i), 'is_selected': False} for i in xrange(100)]

    args_converter = lambda rec: {'text': rec['text'],
                                  'size_hint_y': None,
                                  'height': 25}

    list_adapter = ListAdapter(data=data,
                               args_converter=args_converter,
                               cls=ListItemButton,
                               selection_mode='single',
                               allow_empty_selection=False)

    list_view = ListView(adapter=list_adapter)

This listview will show 100 buttons with 0..100 labels. The args converter
function works on dict items in the data. ListItemButton views will be
intantiated from the args converted by args_converter for each data item. The
listview will only allow single selection -- additional touches will be
ignored. When the listview is first shown, the first item will already be
selected, because allow_empty_selection is False.

Uses for Selection
------------------

In the previous example, we saw how a listview gains selection support just by
using ListAdapter, which subclasses SelectionSupport.

What can we do with selection? Combining selection with the system of bindings
in Kivy, we can build a wide range of user interface designs.

We could change the data items to contain the names of dog breeds, and connect
the selection of dog breed to the display of details in another view, which
would update automatically. This is done via a binding to the
on_selection_change event:

    list_adapter.bind(on_selection_change=my_selection_reactor_function)

where my_selection_reaction_function() does whatever is needed for the update.

We could change the selection_mode of the listview to 'multiple' for a list of
answers to a multiple-choice question that has several correct answers. A
color swatch view could be bound to selection change, as above, so that it
turns green as soon as the correct choices are made, unless the number of
touches exeeds a limit, and it bombs out.

We could chain together three listviews, where selection in the first
controls the items shown in the second, and selection in the second controls
the items shown in the third. If allow_empty_selection were set to False for
these listviews, a dynamic system, a "cascade" from one list to the next,
would result. Several examples show such "cascading" behavior.

More Examples
-------------

There are so many ways that listviews and related functionality can be used,
that we have only scratched the surface here. For on-disk examples, see:

    kivy/examples/widgets/lists/list_*.py
'''

__all__ = ('ListView', )

from kivy.event import EventDispatcher
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.adapters.listadapter import SimpleListAdapter
from kivy.adapters.mixins.selection import SelectableView
from kivy.uix.abstractview import AbstractView
from kivy.properties import ObjectProperty, DictProperty, \
        NumericProperty, ListProperty, BooleanProperty
from kivy.lang import Builder
from math import ceil, floor


class ListItemButton(SelectableView, Button):
    selected_color = ListProperty([1., 0., 0., 1])
    deselected_color = None

    def __init__(self, **kwargs):
        super(ListItemButton, self).__init__(**kwargs)

        # Set deselected_color to be default Button bg color.
        self.deselected_color = self.background_color

    def select(self, *args):
        self.background_color = self.selected_color
        if type(self.parent) is CompositeListItem:
            self.parent.select_from_child(self, *args)

    def deselect(self, *args):
        self.background_color = self.deselected_color
        if type(self.parent) is CompositeListItem:
            self.parent.deselect_from_child(self, *args)

    def select_from_composite(self, *args):
        self.background_color = self.selected_color

    def deselect_from_composite(self, *args):
        self.background_color = self.deselected_color

    def __repr__(self):
        return self.text


class ListItemLabel(SelectableView, Label):

    def __init__(self, **kwargs):
        super(ListItemLabel, self).__init__(**kwargs)

    def select(self, *args):
        self.bold = True
        if type(self.parent) is CompositeListItem:
            self.parent.select_from_child(self, *args)

    def deselect(self, *args):
        self.bold = False
        if type(self.parent) is CompositeListItem:
            self.parent.deselect_from_child(self, *args)

    def select_from_composite(self, *args):
        self.bold = True

    def deselect_from_composite(self, *args):
        self.bold = False

    def __repr__(self):
        return self.text


class CompositeListItem(SelectableView, BoxLayout):

    background_color = ListProperty([1, 1, 1, 1])
    '''ListItem sublasses Button, which has background_color, but
    for a composite list item, we must add this property.
    '''

    selected_color = ListProperty([1., 0., 0., 1])
    deselected_color = ListProperty([.33, .33, .33, 1])

    representing_cls = ObjectProperty([])
    '''Which component view class, if any, should represent for the
    composite list item in __repr__()?
    '''

    def __init__(self, **kwargs):
        super(CompositeListItem, self).__init__(**kwargs)

        # Example data:
        #
        #    'cls_dicts': [{'cls': ListItemButton,
        #                   'kwargs': {'text': "Left",
        #                              'merge_text': True,
        #                              'delimiter': '-'}},
        #                   'cls': ListItemLabel,
        #                   'kwargs': {'text': "Middle",
        #                              'merge_text': True,
        #                              'delimiter': '-',
        #                              'is_representing_cls': True}},
        #                   'cls': ListItemButton,
        #                   'kwargs': {'text': "Right",
        #                              'merge_text': True,
        #                              'delimiter': '-'}}]}

        # There is an index to the data item this composite list item view
        # represents. Get it from kwargs and pass it along to children in the
        # loop below.
        index = kwargs['index']
        print 'COMPOSITE list item index', index

        for cls_dict in kwargs['cls_dicts']:
            cls = cls_dict['cls']
            cls_kwargs = cls_dict['kwargs']

            cls_kwargs['index'] = index

            if 'selection_target' not in cls_kwargs:
                cls_kwargs['selection_target'] = self

            if 'merge_text' in cls_kwargs:
                if cls_kwargs['merge_text'] is True:
                    if 'text' in cls_kwargs:
                        if 'delimiter' in cls_kwargs:
                            cls_kwargs['text'] = "{0}{1}{2}".format(
                                    cls_kwargs['text'],
                                    cls_kwargs['delimiter'],
                                    kwargs['text'])
                        else:
                            cls_kwargs['text'] = "{0}{1}".format(
                                    cls_kwargs['text'],
                                    kwargs['text'])
                elif 'text' not in cls_kwargs:
                    cls_kwargs['text'] = kwargs['text']
            elif 'text' not in cls_kwargs:
                cls_kwargs['text'] = kwargs['text']

            if 'is_representing_cls' in cls_kwargs:
                self.representing_cls = cls

            self.add_widget(cls(**cls_kwargs))

    def select(self, *args):
        self.background_color = self.selected_color

    def deselect(self, *args):
        self.background_color = self.deselected_color

    def select_from_child(self, child, *args):
        for c in self.children:
            if c is not child:
                c.select_from_composite(*args)

    def deselect_from_child(self, child, *args):
        for c in self.children:
            if c is not child:
                c.deselect_from_composite(*args)

    def __repr__(self):
        if self.representing_cls is not None:
            return str(self.representing_cls)
        else:
            return 'unknown'


Builder.load_string('''
<ListView>:
    container: container
    ScrollView:
        pos: root.pos
        on_scroll_y: root._scroll(args[1])
        do_scroll_x: False
        GridLayout:
            cols: 1
            id: container
            size_hint_y: None
''')


class ListView(AbstractView, EventDispatcher):

    divider = ObjectProperty(None)
    '''[TODO] Not used.
    '''

    divider_height = NumericProperty(2)
    '''[TODO] Not used.
    '''

    container = ObjectProperty(None)
    '''The container is a GridLayout widget held within a ScrollView widget.
    (See the associated kv block in the Builder.load_string() setup). Item
    view instances managed and provided by the adapter are added to this
    container. The container is cleared with a call to clear_widgets() when
    the list is rebuilt by the populate() method. A padding Widget instance
    is also added as needed, depending on the row height calculations.
    '''

    row_height = NumericProperty(None)
    '''The row_height property is calculated on the basis of the height of the
    container and the count of items.
    '''

    item_strings = ListProperty([])
    '''If item_strings is provided, create an instance of
    :class:`SimpleListAdapter` with this list of strings, and use it to manage
    a no-selection list.
    '''

    scrolling = BooleanProperty(False)
    '''If the scroll_to() method is called while scrolling operations are
    happening, a call recursion error can occur. scroll_to() checks to see that
    scrolling is False before calling populate(). scroll_to() dispatches a
    scrolling_complete event, which sets scrolling back to False.
    '''

    _index = NumericProperty(0)
    _sizes = DictProperty({})
    _count = NumericProperty(0)

    _wstart = NumericProperty(0)
    _wend = NumericProperty(None)

    def __init__(self, **kwargs):
        # Intercept for the adapter property, which would pass through to
        # AbstractView, to check for its existence. If it doesn't exist, we
        # assume that the data list is to be used with SimpleListAdapter
        # to make a simple list. If it does exist, and data was also
        # provided, raise an exception, because if an adapter is provided, it
        # should be a fully-fledged adapter with its own data.
        if 'adapter' not in kwargs:
            if 'item_strings' not in kwargs:
                raise Exception('ListView: input needed, or an adapter')
            list_adapter = SimpleListAdapter(data=kwargs['item_strings'],
                                             cls=Label)
            kwargs['adapter'] = list_adapter

        super(ListView, self).__init__(**kwargs)

        self.adapter.owning_view = self

        self._trigger_populate = Clock.create_trigger(self._spopulate, -1)
        # [TODO] Is this "hard" scheme needed -- better way?
        self._trigger_hard_populate = \
                Clock.create_trigger(self._hard_spopulate, -1)
        self.bind(size=self._trigger_populate,
                  pos=self._trigger_populate,
                  adapter=self._trigger_populate)

        self.register_event_type('on_scroll_complete')

        # The adapter does not necessarily use the data property for its
        # primary key, so we let it set up the binding. This is associated
        # with selection operations, which :class:`SimpleListAdapter` does
        # not support, so we check if the function is available.
        if hasattr(self.adapter, 'bind_primary_key_to_func'):
            self.adapter.bind_primary_key_to_func(self._trigger_hard_populate)

        # If our adapter supports selection, check the allow_empty_selection
        # property and ensure selection if needed.
        if hasattr(self.adapter, 'check_for_empty_selection'):
            self.adapter.check_for_empty_selection()

    def _scroll(self, scroll_y):
        if self.row_height is None:
            return
        scroll_y = 1 - min(1, max(scroll_y, 0))
        container = self.container
        mstart = (container.height - self.height) * scroll_y
        mend = mstart + self.height

        # convert distance to index
        rh = self.row_height
        istart = int(ceil(mstart / rh))
        iend = int(floor(mend / rh))

        istart = max(0, istart - 1)
        iend = max(0, iend - 1)

        if istart < self._wstart:
            rstart = max(0, istart - 10)
            self.populate(rstart, iend)
            self._wstart = rstart
            self._wend = iend
        elif iend > self._wend:
            self.populate(istart, iend + 10)
            self._wstart = istart
            self._wend = iend + 10

    def _spopulate(self, *dt):
        self.populate()

    def _hard_spopulate(self, *dt):
        print 'hard_populate', dt
        self.item_view_instances = {}
        self.populate()
        self.adapter.check_for_empty_selection()

    def populate(self, istart=None, iend=None):
        print 'populate', self, istart, iend
        container = self.container
        sizes = self._sizes
        rh = self.row_height

        # ensure we know what we want to show
        if istart is None:
            istart = self._wstart
            iend = self._wend

        # clear the view
        container.clear_widgets()

        # guess only ?
        if iend is not None:

            # fill with a "padding"
            fh = 0
            for x in xrange(istart):
                fh += sizes[x] if x in sizes else rh
            container.add_widget(Widget(size_hint_y=None, height=fh))

            # now fill with real item_view
            index = istart
            while index <= iend:
                print '----- ListView get_item_view, iend, index', iend, index
                item_view = self.get_item_view(index)
                index += 1
                if item_view is None:
                    continue
                sizes[index] = item_view.height
                container.add_widget(item_view)
        else:
            available_height = self.height
            real_height = 0
            index = self._index
            count = 0
            while available_height > 0:
                print '----- ListView get_item_view, index', index
                item_view = self.get_item_view(index)
                if item_view is None:
                    break
                sizes[index] = item_view.height
                index += 1
                count += 1
                container.add_widget(item_view)
                available_height -= item_view.height
                real_height += item_view.height

            self._count = count

            # extrapolate the full size of the container from the size
            # of item_view_instances
            if count:
                container.height = \
                    real_height / count * self.adapter.get_count()
                if self.row_height is None:
                    self.row_height = real_height / count

    def scroll_to(self, index=0):
        if not self.scrolling:
            self.scrolling = True
            self._index = index
            self.populate()
            self.dispatch('on_scroll_complete')

    def on_scroll_complete(self, *args):
        self.scrolling = False
