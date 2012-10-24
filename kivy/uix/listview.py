'''
List View
===========

.. versionadded:: 1.5

.. warning::

    This widget is still experimental, and his API is subject to change in a
    future version.

The :class:`ListView` widget provides a scrollable/pannable viewport that is
clipped at the scrollview's bounding box, which contains a list of
list item view instances.

:class:`ListView` implements :class:`AbstractView` as a vertical scrollable
list. :class:`AbstractView` has one property, adapter. :class:`ListView` sets
adapter to one of: :class:`SimpleListAdapter`, :class:`ListAdapter`, or
:class`DictAdapter`.


    :Events:
        `on_scroll_complete`: (boolean, )
            Fired when scrolling completes.

Basic Example
-------------

In its simplest form, we make a listview with 100 items::

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

Using an Adapter
-------------------

Behind the scenes, the basic example above uses :class:`SimpleListAdapter`.
When the constructor for :class:`ListView` sees that only a list of strings is
provided as an argument, called item_strings, it creates an instance of
:class:`SimpleListAdapter` with the list of strings.

Simple in :class:`SimpleListAdapter` means: *without selection support*. It is
a scrollable list of items that do not respond to touch events.

To use :class:`SimpleListAdaper` explicitly in creating a ListView instance,
do::

    simple_list_adapter = SimpleListAdapter(
            data=["Item #{0}".format(i) for i in xrange(100)],
            cls=Label)

    list_view = ListView(adapter=simple_list_adapter)

The instance of :class:`SimpleListAdapter` has a required data argument, which
contains data items to use as the basis for list items, along with a cls
argument for the class to be instantiated for each list item from the data.

ListAdapter and DictAdapter
---------------------------

For many uses of a list, the data is more than a simple list of strings and
selection functionality is often needed.  :class:`ListAdapter` and
:class:`DictAdapter` each contain functionality for selection.

See the :class:`ListAdapter` docs for details, but here are synopses of
its arguments:

* *data*: strings, class instances, dicts, etc. that form the basis data
  for instantiating view item classes.

* *cls*: a Kivy view that is to be instantiated for each list item. There
  are several built-in types available, including ListItemLabel and
  ListItemButton, or you can easily make your own.

* *template*: the name of a Kivy language (kv) template that defines the
  Kivy view for each list item.

.. note::

    Pick only one, cls or template, to provide as an argument.

* *args_converter*: a function that takes a data item object as input, and
  uses it to build and return an args dict, ready
  to be used in a call to instantiate the item view cls or
  template. In the case of cls, the args dict acts as a
  kwargs object. For a template, it is treated as a context
  (ctx), but is essentially similar in form. See the
  examples and docs for template use.

* *selection_mode*: a string for: 'single', 'multiple' or others (See docs).

* *allow_empty_selection*: a boolean, which if False, the default, forces
  there to always be a selection, if there is data
  available. If True, selection happens only as a
  result of user action.

In narrative, we can summarize with:

    A listview's adapter takes data items and uses an args_converter
    function to transform them into arguments for making list item view
    instances, using either a cls or a kv template.

In a graphic, a summary of the relationship between a listview and its
list adapter, looks like this::

    -                    ------------ ListAdapter or DictAdapter ------------
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

2) The data argument is, as you would expect, a dict. Keys in the dict
   must include the keys in the sorted_keys argument, but they may form a
   superset of the keys in sorted_keys. Values may be strings, class
   instances, dicts, etc. (The args_converter uses it, accordingly).

Using an Args Converter
-----------------------

:class:`ListView` allows use of built-in list item views, such as
:class:`ListItemButton`, your own custom item view class, or a custom kv
template. Whichever type of list item view is used, an args_converter function
is needed to prepare, per list data item, args for either a cls or template.

Here is an args_converter for use with the built-in :class:`ListItemButton`,
specified as a normal Python function::

    def args_converter(an_obj):
        return {'text': an_obj.text,
                'size_hint_y': None,
                'height': 25}

    and as a lambda:

    args_converter = lambda an_obj: {'text': an_obj.text,
                                     'size_hint_y': None,
                                     'height': 25}

In the args converter example above, the data item is assumed to be an object
(class instance), hence the reference an_obj.text.

Here is an example of an args converter that works with list data items that
are dicts::

    args_converter = lambda obj: {'text': a_dict['text'],
                                  'size_hint_y': None,
                                  'height': 25}

So, it is the responsibility of the developer to code the args_converter
according to the data at hand.

An Example ListView
-------------------

Now, to some example code::

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

:class:`ListItemLabel` works much the same way as :class:`ListItemButton`.

Using a Custom Item View Class
------------------------------

The data used in an adapter can be any of the normal Python types, such as
strings, class instances, dictionaries, etc. It is up to the programmer to
assure that the args_converter has appropriate functionality.

Here we make a simple DataItem class that has the required text and
is_selected properties::

    from kivy.uix.listview import ListItemButton

    class DataItem(object):
        def __init__(self, text='', is_selected=False):
            self.text = text
            self.is_selected = is_selected

    data_items = []
    data_items.append(DataItem(text='cat')
    data_items.append(DataItem(text='dog')
    data_items.append(DataItem(text='frog')

    list_item_args_converter = lambda obj: {'text': obj.text,
                                            'size_hint_y': None,
                                            'height': 25}

    # We will set this data in a ListAdapter along with the list item
    # args_converter function above (lambda), and we set arguments about
    # selection. We will allow single selection, selection in the listview
    # will propagate to the data items -- the is_selected for each data item
    # will be set. And, by having allow_empty_selection=False, when the
    # listview first appears, the first item, 'cat', will already be
    # selected. The list adapter will instantiate a ListItemButton class
    # instance for each data item, using the assigned args_converter.
    list_adapter = ListAdapter(data=data_items,
                               args_converter=list_item_args_converter,
                               selection_mode='single',
                               propagate_selection_to_data=True,
                               allow_empty_selection=False,
                               cls=ListItemButton)

    list_view = ListView(adapter=list_adapter)

The list_vew would then be added to a view with add_widget().

You may also use the provided :class:`SelectableDataItem` mixin to make a
custom class. Instead of the "manually-constructed" DataItem class above,
we could do::

    from kivy.adapters.models import SelectableDataItem

    class DataItem(SelectableDataItem):
        pass

:class:`SelectableDataItem` is a simple mixin class that has the text and
is_selected properties.

Using an Item View Template
---------------------------

:class:`SelectableView` is another simple mixin class that has required
properties for a list item: text, and is_selected. To make your own template,
mix it in as follows::

    from kivy.uix.listview import ListItemButton
    from kivy.uix.listview import SelectableView

    Builder.load_string(<triplequotes>
    [CustomListItem@SelectableView+BoxLayout]:
        size_hint_y: ctx.size_hint_y
        height: ctx.height
        ListItemButton:
            text: ctx.text
            is_selected: ctx.is_selected
    </triplequotes>)

A class called CustomListItem will be instantiated for each list item. Note that
it is a layout, BoxLayout, and is thus a kind of container. It contains a
:class:`ListItemButton` instance.

Using the power of the Kivy language (kv), you can easily build composite list
items -- in addition to ListItemButton, you could have a ListItemLabel, or a
custom class you have defined and registered with the system.

An args_converter needs to be constructed that goes along with such a kv
template. For example, to use the kv template above::

    list_item_args_converter = lambda rec: {'text': rec['text'],
                                            'is_selected': rec['is_selected'],
                                            'size_hint_y': None,
                                            'height': 25}
    integers_dict =
        { str(i): {'text': str(i), 'is_selected': False} for i in xrange(100)}

    # Here we create a dict adapter with 1..100 integer strings as
    # sorted_keys, and an integers_dict as data, passing our
    # CompositeListItem kv template for the list item view.
    dict_adapter = DictAdapter(sorted_keys=[str(i) for i in xrange(100)],
                               data=integers_dict,
                               args_converter=list_item_args_converter,
                               template='CustomListItem')

    # Now we create a list view using this adapter. The args_converter above
    # converts dict attributes to ctx attributes.
    list_view = ListView(adapter=dict_adapter)

The list_vew would then be added to a view with add_widget().

Using CompositeItemView
-----------------------

The class :class:`CompositeItemView` is another option for building complex
composite list items. The kv language approach has its advantages, but here we
build a composite list view using a straight Kivy widget method::

    # This is quite an involved args_converter, so we should go through the
    # details. A CompositeListItem instance is made with the args
    # returned by this converter. The first three, text, size_hint_y,
    # height are arguments for CompositeListItem. The cls_dicts list contains
    # argument sets for each of the member widgets for this composite:
    # ListItemButton and ListItemLabel. This is a similar approach to using a
    # kv template described above.
    args_converter = lambda rec:
            {'text': rec['text'],
             'size_hint_y': None,
             'height': 25,
             'cls_dicts': [{'cls': ListItemButton,
                            'kwargs': {'text': rec['text']}},
                           {'cls': ListItemLabel,
                            'kwargs': {'text': "Middle-{0}".format(rec['text']),
                                       'is_representing_cls': True}},
                           {'cls': ListItemButton,
                            'kwargs': {'text': rec['text']}}]}

    item_strings = ["{0}".format(index) for index in xrange(100)]

    integers_dict =
        { str(i): {'text': str(i), 'is_selected': False} for i in xrange(100)}

    # And now the dict adapter, constructed with the item_strings as
    # the sorted_keys, the integers_dict as data, and our args_converter()
    # that produce list item view instances from the
    # :class:`CompositeListItem` class.
    dict_adapter = DictAdapter(sorted_keys=item_strings,
                               data=integers_dict,
                               args_converter=args_converter,
                               selection_mode='single',
                               allow_empty_selection=False,
                               cls=CompositeListItem)

    list_view = ListView(adapter=dict_adapter)

For details on how :class:`CompositeListItem` works, view the code and look
for parsing of the cls_dicts list and kwargs processing.

Uses for Selection
------------------

What can we do with selection? Combining selection with the system of bindings
in Kivy, we can build a wide range of user interface designs.

We could change the data items to contain the names of dog breeds, and connect
the selection of dog breed to the display of details in another view, which
would update automatically. This is done via a binding to the
on_selection_change event::

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

__all__ = ('SelectableView', 'ListItemButton', 'ListItemLabel',
           'CompositeListItem', 'ListView', )

from kivy.event import EventDispatcher
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.adapters.simplelistadapter import SimpleListAdapter
from kivy.uix.abstractview import AbstractView
from kivy.properties import ObjectProperty, DictProperty, \
        NumericProperty, ListProperty, BooleanProperty
from kivy.lang import Builder
from math import ceil, floor


class SelectableView(object):
    '''The :class:`SelectableView` mixin is used in list item and other
    classes that are to be instantiated in a list view, or another class
    which uses a selection-enabled adapter such as ListAdapter.  select() and
    deselect() are to be overridden with display code to mark items as
    selected or not, if desired.
    '''

    index = NumericProperty(-1)
    '''The index into the underlying data list or the data item this view
    represents.

    :data:`index` is a :class:`~kivy.properties.NumericProperty`, default
    to -1.
    '''

    is_selected = BooleanProperty(False)
    '''A SelectableView instance carries this property, which should be kept
    in sync with the equivalent property in the data item it represents.

    :data:`is_selected` is a :class:`~kivy.properties.BooleanProperty`, default
    to False.
    '''

    def __init__(self, **kwargs):
        super(SelectableView, self).__init__(**kwargs)

    def select(self, *args):
        '''The list item is responsible for updating the display for
        being selected, if desired.
        '''
        self.is_selected = True

    def deselect(self, *args):
        '''The list item is responsible for updating the display for
        being unselected, if desired.
        '''
        self.is_selected = False


class ListItemButton(SelectableView, Button):
    selected_color = ListProperty([1., 0., 0., 1])
    '''
    :data:`selected_color` is a :class:`~kivy.properties.ListProperty`,
    default to [1., 0., 0., 1].
    '''

    deselected_color = ListProperty([0., 1., 0., 1])
    '''
    :data:`selected_color` is a :class:`~kivy.properties.ListProperty`,
    default to [0., 1., 0., 1].
    '''

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

    :data:`background_color` is a :class:`~kivy.properties.ListProperty`,
    default to [1, 1, 1, 1].
    '''

    selected_color = ListProperty([1., 0., 0., 1])
    '''
    :data:`selected_color` is a :class:`~kivy.properties.ListProperty`,
    default to [1., 0., 0., 1].
    '''

    deselected_color = ListProperty([.33, .33, .33, 1])
    '''
    :data:`deselected_color` is a :class:`~kivy.properties.ListProperty`,
    default to [.33, .33, .33, 1].
    '''

    representing_cls = ObjectProperty(None)
    '''Which component view class, if any, should represent for the
    composite list item in __repr__()?

    :data:`representing_cls` is an :class:`~kivy.properties.ObjectProperty`,
    default to None.
    '''

    def __init__(self, **kwargs):
        super(CompositeListItem, self).__init__(**kwargs)

        # Example data:
        #
        #    'cls_dicts': [{'cls': ListItemButton,
        #                   'kwargs': {'text': "Left"}},
        #                   'cls': ListItemLabel,
        #                   'kwargs': {'text': "Middle",
        #                              'is_representing_cls': True}},
        #                   'cls': ListItemButton,
        #                   'kwargs': {'text': "Right"}]

        # There is an index to the data item this composite list item view
        # represents. Get it from kwargs and pass it along to children in the
        # loop below.
        index = kwargs['index']

        for cls_dict in kwargs['cls_dicts']:
            cls = cls_dict['cls']
            cls_kwargs = cls_dict.get('kwargs', None)

            if cls_kwargs:
                cls_kwargs['index'] = index

                if 'selection_target' not in cls_kwargs:
                    cls_kwargs['selection_target'] = self

                if 'text' not in cls_kwargs:
                    cls_kwargs['text'] = kwargs['text']

                if 'is_representing_cls' in cls_kwargs:
                    self.representing_cls = cls

                self.add_widget(cls(**cls_kwargs))
            else:
                cls_kwargs = {}
                if 'text' in kwargs:
                    cls_kwargs['text'] = kwargs['text']
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
            return super(CompositeListItem, self).__repr__()


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

    :data:`container` is an :class:`~kivy.properties.ObjectProperty`,
    default to None.
    '''

    row_height = NumericProperty(None)
    '''The row_height property is calculated on the basis of the height of the
    container and the count of items.

    :data:`row_height` is a :class:`~kivy.properties.NumericProperty`,
    default to None.
    '''

    item_strings = ListProperty([])
    '''If item_strings is provided, create an instance of
    :class:`SimpleListAdapter` with this list of strings, and use it to manage
    a no-selection list.

    :data:`item_strings` is a :class:`~kivy.properties.ListProperty`,
    default to [].
    '''

    scrolling = BooleanProperty(False)
    '''If the scroll_to() method is called while scrolling operations are
    happening, a call recursion error can occur. scroll_to() checks to see that
    scrolling is False before calling populate(). scroll_to() dispatches a
    scrolling_complete event, which sets scrolling back to False.

    :data:`scrolling` is a :class:`~kivy.properties.BooleanProperty`,
    default to False.
    '''

    _index = NumericProperty(0)
    _sizes = DictProperty({})
    _count = NumericProperty(0)

    _wstart = NumericProperty(0)
    _wend = NumericProperty(None)

    def __init__(self, **kwargs):
        # Check for an adapter argument. If it doesn't exist, we
        # assume that item_strings is to be used with SimpleListAdapter
        # to make a simple list. In this case, if item_strings was not
        # provided, raise an exception.
        if 'adapter' not in kwargs:
            if 'item_strings' not in kwargs:
                raise Exception('ListView: item_strings needed or an adapter')

            list_adapter = SimpleListAdapter(data=kwargs['item_strings'],
                                             cls=Label)
            kwargs['adapter'] = list_adapter

        super(ListView, self).__init__(**kwargs)

        self.register_event_type('on_scroll_complete')

        self._trigger_populate = Clock.create_trigger(self._spopulate, -1)

        self.bind(size=self._trigger_populate,
                  pos=self._trigger_populate,
                  adapter=self._trigger_populate)

        # The bindings setup above sets self._trigger_populate() to fire
        # when the adapter changes, but we also need this binding for when
        # adapter.data and other possible triggers change for view updating.
        # We don't know that these are, so we ask the adapter to set up the
        # bindings back to the view updating function here.
        self.adapter.bind_triggers_to_view(self._trigger_populate)

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

    def populate(self, istart=None, iend=None):
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
                item_view = self.adapter.get_view(index)
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
                item_view = self.adapter.get_view(index)
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
            # of view instances in the adapter
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
