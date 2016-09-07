'''
List View
===========

.. versionadded:: 1.5

.. note::

    ListView has been deprecated, use
    :class:`~kivy.uix.recycleview.RecycleView` instead.

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

The :class:`~kivy.uix.listview.ListView` implements an
:class:`~kivy.uix.abstractview.AbstractView` as
a vertical, scrollable,pannable list clipped to the scrollview's bounding box
and contains list item view instances.

The :class:`AbstractView` has one property: :class:`~kivy.adapters.adapter`.
The adapter can be one of the following: a
:class:`~kivy.adapters.simplelistadapter.SimpleListAdapter`, a
:class:`~kivy.adapters.listadapter.ListAdapter` or a
:class:`~kivy.adapters.dictadapter.DictAdapter`. The :class:`Adapter` can make
use of :mod:`~kivy.adapters.args_converters` to prepare you data for passing
into the constructor for each item view instantiation.

For an overview of how all these components fit together, please see the
:mod:`~kivy.adapters` module documentation.

Introduction
------------

Lists are central parts of many software projects. Kivy's approach to lists
includes providing solutions for simple lists, along with a substantial
framework for building lists of moderate to advanced complexity. For a new
user, it can be difficult to ramp up from simple to advanced. For
this reason, Kivy provides an extensive set of examples (with the Kivy package)
that you may wish to run first, to get a taste of the range of functionality
offered. You can tell from the names of the examples that they illustrate the
"ramping up" from simple to advanced:


    * `kivy/examples/widgets/lists/list_simple.py <https://github.com/\
kivy/kivy/tree/master/examples/widgets/lists/list_simple.py>`_
    * `kivy/examples/widgets/lists/list_simple_in_kv.py <https://github.com/\
kivy/kivy/tree/master/examples/widgets/lists/list_simple_in_kv.py>`_
    * `kivy/examples/widgets/lists/list_simple_in_kv_2.py <https://github.com/\
kivy/kivy/tree/master/examples/widgets/lists/list_simple_in_kv_2.py>`_
    * `kivy/examples/widgets/lists/list_master_detail.py <https://github.com/\
kivy/kivy/tree/master/examples/widgets/lists/list_master_detail.py>`_
    * `kivy/examples/widgets/lists/list_two_up.py <https://github.com/\
kivy/kivy/tree/master/examples/widgets/lists/list_two_up.py>`_
    * `kivy/examples/widgets/lists/list_kv.py <https://github.com/\
kivy/kivy/tree/master/examples/widgets/lists/list_kv.py>`_
    * `kivy/examples/widgets/lists/list_composite.py <https://github.com/\
kivy/kivy/tree/master/examples/widgets/lists/list_composite.py>`_
    * `kivy/examples/widgets/lists/list_reset_data.py <https://github.com/\
kivy/kivy/tree/master/examples/widgets/lists/list_reset_data.py>`_
    * `kivy/examples/widgets/lists/list_cascade.py <https://github.com/\
kivy/kivy/tree/master/examples/widgets/lists/list_cascade.py>`_
    * `kivy/examples/widgets/lists/list_cascade_dict.py <https://github.com/\
kivy/kivy/tree/master/examples/widgets/lists/list_cascade_dict.py>`_
    * `kivy/examples/widgets/lists/list_cascade_images.py <https://github.com/\
kivy/kivy/tree/master/examples/widgets/lists/list_cascade_images.py>`_
    * `kivy/examples/widgets/lists/list_ops.py <https://github.com/\
kivy/kivy/tree/master/examples/widgets/lists/list_ops.py>`_

Many of the examples feature selection, some restricting selection to single
selection, where only one item at at time can be selected, and others allowing
multiple item selection. Many of the examples illustrate how selection in one
list can be connected to actions and selections in another view or another list.

Find your own way of reading the documentation here, examining the source code
for the example apps and running the examples. Some may prefer to read the
documentation through first, others may want to run the examples and view their
code. No matter what you do, going back and forth will likely be needed.

Basic Example
-------------

In its simplest form, we make a listview with 100 items::

    from kivy.uix.listview import ListView
    from kivy.base import runTouchApp


    class MainView(ListView):
        def __init__(self, **kwargs):
            super(MainView, self).__init__(
                item_strings=[str(index) for index in range(100)])

    if __name__ == '__main__':
        runTouchApp(MainView())

Or, we could declare the listview using the kv language::

    from kivy.uix.boxlayout import BoxLayout
    from kivy.lang import Builder
    from kivy.base import runTouchApp

    Builder.load_string("""
    <MyListView>:
        ListView:
            item_strings: [str(index) for index in range(100)]
    """)


    class MyListView(BoxLayout):
        pass

    if __name__ == '__main__':
        runTouchApp(MyListView())

Using an Adapter
-------------------

Behind the scenes, the basic example above uses the
:class:`~kivy.adapters.simplelistadapter.SimpleListAdapter`. When the
constructor for the :class:`~kivy.uix.listview.ListView` sees that only a list
of
strings is provided as an argument (called item_strings), it creates a
:class:`~kivy.adapters.simplelistadapter.SimpleListAdapter` using the
list of strings.

"Simple" in :class:`~kivy.adapters.simplelistadapter.SimpleListAdapter` means
*without selection support*. It is a scrollable list of items that does not
respond to touch events.

To use a :class:`SimpleListAdaper` explicitly when creating a ListView instance,
do::

    simple_list_adapter = SimpleListAdapter(
            data=["Item #{0}".format(i) for i in range(100)],
            cls=Label)

    list_view = ListView(adapter=simple_list_adapter)

The instance of :class:`~kivy.adapters.simplelistadapter.SimpleListAdapter` has
a required data argument which contains data items to use for instantiating
:class:`~kivy.uix.label.Label` views for the list view (note the cls=Label
argument). The data items are strings. Each item string is set by the
:class:`~kivy.adapters.simplelistadapter.SimpleListAdapter` as the *text*
argument for each Label instantiation.

You can declare a ListView with an adapter in a kv file with special attention
given to the way longer python blocks are indented::

    from kivy.uix.boxlayout import BoxLayout
    from kivy.base import runTouchApp
    from kivy.lang import Builder

    # Note the special nature of indentation in the adapter declaration, where
    # the adapter: is on one line, then the value side must be given at one
    # level of indentation.

    Builder.load_string("""
    #:import label kivy.uix.label
    #:import sla kivy.adapters.simplelistadapter

    <MyListView>:
        ListView:
            adapter:
                sla.SimpleListAdapter(
                data=["Item #{0}".format(i) for i in range(100)],
                cls=label.Label)
    """)


    class MyListView(BoxLayout):
        pass

    if __name__ == '__main__':
        runTouchApp(MyListView())

ListAdapter and DictAdapter
---------------------------

For most use cases, your data is more complex than a simple list of strings.
Selection functionality is also often needed.
The :class:`~kivy.adapters.listadapter.ListAdapter` and
:class:`~kivy.adapters.dictadapter.DictAdapter` cover these more elaborate
needs.

The :class:`~kivy.adapters.listadapter.ListAdapter` is the base class for
:class:`~kivy.adapters.dictadapter.DictAdapter`, so we can start with it.

Refer to the :class:`~kivy.adapters.listadapter.ListAdapter` docs for details,
but here is a synopsis of its arguments:

* :attr:`~kivy.adapters.adapter.Adapter.data`:
  strings, class instances, dicts, etc. that form the base data
  for instantiating views.

* :attr:`~kivy.adapters.adapter.Adapter.cls`:
  a Kivy view that is to be instantiated for each list item. There
  are several built-in types available, including ListItemLabel and
  ListItemButton, or you can make your own class that mixes in the
  required :class:`~kivy.uix.selectableview.SelectableView`.

* :attr:`~kivy.adapters.adapter.Adapter.template`:
  the name of a Kivy language (kv) template that defines the
  Kivy view for each list item.

.. note::

    Pick only one, cls or template, to provide as an argument.

* :attr:`~kivy.adapters.args_converters`: a function that takes a data item
  object as input and
  uses it to build and return an args dict, ready
  to be used in a call to instantiate item views using the item view cls
  or template. In the case of cls, the args dict becomes a kwargs constructor
  argument. For a template, it is treated as a context
  (ctx) but is essentially similar in form to the kwargs usage.

* :attr:`~kivy.adapters.listadapter.ListAdapter.selection_mode`:
  a string with the value 'single',
  'multiple' or other.

* :attr:`~kivy.adapters.listadapter.ListAdapter.allow_empty_selection`:
  a boolean, which if False (the default), forces
  there to always be a selection if there is data
  available. If True, selection happens only as a
  result of user action.

In narrative, we can summarize as follows:

    A listview's adapter takes data items and uses an args_converter
    function to transform them into arguments for creating list item view
    instances, using either a cls or a kv template.

In a graphic, a summary of the relationship between a listview and its
components can be summarized as follows:

.. image:: images/adapters.png

Please refer to the :mod:`~kivy.adapters` documentation for more details.

A :class:`~kivy.adapters.dictadapter.DictAdapter` has the same arguments and
requirements as a :class:`~kivy.adapters.listadapter.ListAdapter` except for two
things:

1) There is an additional argument, sorted_keys, which must meet the
   requirements of normal python dictionary keys.

2) The data argument is, as you would expect, a dict. Keys in the dict
   must include the keys in the sorted_keys argument, but they may form a
   superset of the keys in sorted_keys. Values may be strings, class
   instances, dicts, etc. (The args_converter uses it accordingly).

Using an Args Converter
-----------------------

A :class:`~kivy.uix.listview.ListView` allows use of built-in list item views,
such as :class:`~kivy.uix.listview.ListItemButton`, your own custom item view
class or a custom kv template. Whichever type of list item view is used, an
:doc:`args_converter <api-kivy.adapters.args_converters>` function is needed to
prepare, per list data item, kwargs for the cls or the ctx for the template.

.. note::

    Only the ListItemLabel, ListItemButton or custom classes like them (and
    not the simple Label or Button classes) are to be used in the listview
    system.

.. warning::

    ListItemButton inherits the `background_normal` and `background_down`
    properties from the Button widget, so the `selected_color` and
    `deselected_color` are not represented faithfully by default.

Here is an args_converter for use with the built-in
:class:`~kivy.uix.listview.ListItemButton` specified as a normal Python
function::

    def args_converter(row_index, an_obj):
        return {'text': an_obj.text,
                'size_hint_y': None,
                'height': 25}

and as a lambda::

    args_converter = lambda row_index, an_obj: {'text': an_obj.text,
                                                'size_hint_y': None,
                                                'height': 25}

In the args converter example above, the data item is assumed to be an object
(class instance), hence the reference an_obj.text.

Here is an example of an args converter that works with list data items that
are dicts::

    args_converter = lambda row_index, obj: {'text': obj['text'],
                                             'size_hint_y': None,
                                             'height': 25}

So, it is the responsibility of the developer to code the args_converter
according to the data at hand. The row_index argument can be useful in some
cases, such as when custom labels are needed.

An Example ListView
-------------------

Now, to some example code::

    from kivy.adapters.listadapter import ListAdapter
    from kivy.uix.listview import ListItemButton, ListView

    data = [{'text': str(i), 'is_selected': False} for i in range(100)]

    args_converter = lambda row_index, rec: {'text': rec['text'],
                                             'size_hint_y': None,
                                             'height': 25}

    list_adapter = ListAdapter(data=data,
                               args_converter=args_converter,
                               cls=ListItemButton,
                               selection_mode='single',
                               allow_empty_selection=False)

    list_view = ListView(adapter=list_adapter)

This listview will show 100 buttons with text of 0 to 100. The args_converter
function converts the dict items in the data and instantiates ListItemButton
views by passing these converted items into it's constructor. The
listview will only allow single selection and the first item will already be
selected as allow_empty_selection is False. For a complete discussion on these
arguments, please see the :class:`~kivy.adapters.listadapter.ListAdapter`
documentation.

The :class:`~kivy.uix.listview.ListItemLabel` works in much the same way as the
:class:`~kivy.uix.listview.ListItemButton`.

Using a Custom Item View Class
------------------------------

The data used in an adapter can be any of the normal Python types or custom
classes, as shown below. It is up to the programmer to assure that the
args_converter performs the appropriate conversions.

Here we make a simple DataItem class that has the required text and
is_selected properties::

    from kivy.uix.listview import ListItemButton
    from kivy.adapters.listadapter import ListAdapter


    class DataItem(object):
        def __init__(self, text='', is_selected=False):
            self.text = text
            self.is_selected = is_selected

    data_items = [DataItem(text='cat'),
                  DataItem(text='dog'),
                  DataItem(text='frog')]

    list_item_args_converter = lambda row_index, obj: {'text': obj.text,
                                                       'size_hint_y': None,
                                                       'height': 25}

    list_adapter = ListAdapter(data=data_items,
                               args_converter=list_item_args_converter,
                               propagate_selection_to_data=True,
                               cls=ListItemButton)

    list_view = ListView(adapter=list_adapter)

The data is passed to the :class:`~kivy.adapters.listadapter.ListAdapter` along
with an args_converter function. The propagation setting means that
the is_selected property for each data item will be set and kept in sync with
the list item views. This setting should be set to True if you wish to
initialize the view with item views already selected.

You may also use the provided :class:`~kivy.adapters.models.SelectableDataItem`
mixin to make a custom class. Instead of the "manually-constructed" DataItem
class above, we could do::

    from kivy.adapters.models import SelectableDataItem

    class DataItem(SelectableDataItem):
        # Add properties here.
        pass

:class:`~kivy.adapters.models.SelectableDataItem` is a simple mixin class that
has an is_selected property.

Using an Item View Template
---------------------------

:class:`~kivy.uix.selectableview.SelectableView` is another simple mixin class that
has required properties for a list item: text, and is_selected. To make your
own template, mix it in as follows::

    from kivy.lang import Builder

    Builder.load_string("""
    [CustomListItem@SelectableView+BoxLayout]:
        size_hint_y: ctx.size_hint_y
        height: ctx.height
        ListItemButton:
            text: ctx.text
            is_selected: ctx.is_selected
    """)

A class called CustomListItem can then be instantiated for each list item. Note
that it subclasses a :class:`~kivy.uix.boxlayout.BoxLayout` and is thus a type
of :mod:`~kivy.uix.layout`. It contains a
:class:`~kivy.uix.listview.ListItemButton` instance.

Using the power of the Kivy language (kv), you can easily build composite list
items: in addition to ListItemButton, you could have a ListItemLabel or a
custom class you have defined and registered via the
:class:`~kivy.factory.Factory`.

An args_converter needs to be constructed that goes along with such a kv
template. For example, to use the kv template above::

    list_item_args_converter = \\
            lambda row_index, rec: {'text': rec['text'],
                                    'is_selected': rec['is_selected'],
                                    'size_hint_y': None,
                                    'height': 25}
    integers_dict = \\
        { str(i): {'text': str(i), 'is_selected': False} for i in range(100)}

    dict_adapter = DictAdapter(sorted_keys=[str(i) for i in range(100)],
                               data=integers_dict,
                               args_converter=list_item_args_converter,
                               template='CustomListItem')

    list_view = ListView(adapter=dict_adapter)

A dict adapter is created with 1..100 integer strings as sorted_keys, and an
integers_dict as data. integers_dict has the integer strings as keys and dicts
with text and is_selected properties. The CustomListItem defined above in the
Builder.load_string() call is set as the kv template for the list item views.
The list_item_args_converter lambda function will take each dict in
integers_dict and will return an args dict, ready for passing as the context
(ctx) for the template.

Using CompositeListItem
-----------------------

The class :class:`~kivy.uix.listview.CompositeListItem` is another option for
building advanced composite list items. The kv language approach has its
advantages, but here we build a composite list view using a plain Python::

    args_converter = lambda row_index, rec: \\
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

    item_strings = ["{0}".format(index) for index in range(100)]

    integers_dict = \\
        {str(i): {'text': str(i), 'is_selected': False} for i in range(100)}

    dict_adapter = DictAdapter(sorted_keys=item_strings,
                               data=integers_dict,
                               args_converter=args_converter,
                               selection_mode='single',
                               allow_empty_selection=False,
                               cls=CompositeListItem)

    list_view = ListView(adapter=dict_adapter)

The args_converter is somewhat complicated, so we should go through the
details. Observe in the :class:`~kivy.adapters.dictadapter.DictAdapter`
instantiation that :class:`~kivy.uix.listview.CompositeListItem` instance is
set as the cls to be instantiated for each list item component. The
args_converter will
make args dicts for this cls. In the args_converter, the first three items,
text, size_hint_y, and height, are arguments for the CompositeListItem itself.
After that you see a cls_dicts list that contains argument sets for each of the
member widgets for this composite: 2
:class:`ListItemButtons <kivy.uix.listview.ListItemButton>` and a
:class:`~kivy.uix.listview.ListItemLabel`. This is a similar approach to
using a kv template described above.

For details on how :class:`~kivy.uix.listview.CompositeListItem` works,
examine the code, looking for how parsing of the cls_dicts list and kwargs
processing is done.

Uses for Selection
------------------

What can we do with selection? Combining selection with the system of bindings
in Kivy, we can build a wide range of user interface designs.

We could make data items that contain the names of dog breeds, and connect
the selection of dog breed to the display of details in another view, which
would update automatically on selection. This is done via a binding to the
:attr:`~kivy.adapters.listadapter.ListAdapter.on_selection_change` event::

    list_adapter.bind(on_selection_change=callback_function)

where callback_function() gets passed the adapter as an argument and does
whatever is needed for the update. See the
example called list_master_detail.py, and imagine that the list on the left
could be a list of dog breeds, and the detail view on the right could show
details for a selected dog breed.

In another example, we could set the selection_mode of a listview to
'multiple', and load it with a list of answers to a multiple-choice question.
The question could have several correct answers. A color swatch view could be
bound to selection change, as above, so that it turns green as soon as the
correct choices are made, unless the number of touches exceeds a limit, then the
answer session could be terminated. See the examples that feature thumbnail
images to get some ideas, e.g. list_cascade_dict.py.

In a more involved example, we could chain together three listviews, where
selection in the first controls the items shown in the second, and selection in
the second controls the items shown in the third. If allow_empty_selection were
set to False for these listviews, a dynamic system of selection "cascading"
from one list to the next, would result.

There are so many ways that listviews and Kivy bindings functionality can be
used, that we have only scratched the surface here. For on-disk examples, see::

    kivy/examples/widgets/lists/list_*.py

Several examples show the "cascading" behavior described above. Others
demonstrate the use of kv templates and composite list views.

'''

__all__ = ('SelectableView', 'ListItemButton', 'ListItemLabel',
           'CompositeListItem', 'ListView', 'ListItemReprMixin')

from kivy.event import EventDispatcher
from kivy.clock import Clock
from kivy.compat import PY2
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.adapters.simplelistadapter import SimpleListAdapter
from kivy.uix.abstractview import AbstractView
from kivy.uix.selectableview import SelectableView
from kivy.properties import ObjectProperty, DictProperty, \
        NumericProperty, ListProperty, BooleanProperty
from kivy.lang import Builder
from kivy.utils import deprecated
from math import ceil, floor


class ListItemReprMixin(Label):
    '''
    The :class:`~kivy.uix.listview.ListItemReprMixin` provides a
    :class:`~kivy.uix.label.Label` with a Python 2/3 compatible string
    representation (*__repr__*). It is intended for internal usage.
    '''
    if PY2:
        def __repr__(self):
            text = self.text.encode('utf-8') if isinstance(self.text, unicode) \
                else self.text
            return '<%s text=%s>' % (self.__class__.__name__, text)
    else:
        def __repr__(self):
            return '<%s text=%s>' % (self.__class__.__name__, self.text)


class ListItemButton(ListItemReprMixin, SelectableView, Button):
    ''':class:`~kivy.uix.listview.ListItemButton` mixes
    :class:`~kivy.uix.selectableview.SelectableView` with
    :class:`~kivy.uix.button.Button` to produce a button suitable for use in
    :class:`~kivy.uix.listview.ListView`.
    '''

    selected_color = ListProperty([1., 0., 0., 1])
    '''
    :attr:`selected_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [1., 0., 0., 1].
    '''

    deselected_color = ListProperty([0., 1., 0., 1])
    '''
    :attr:`deselected_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [0., 1., 0., 1].
    '''

    def __init__(self, **kwargs):
        super(ListItemButton, self).__init__(**kwargs)

        # Set Button bg color to be deselected_color.
        self.background_color = self.deselected_color

    def select(self, *args):
        self.background_color = self.selected_color
        if isinstance(self.parent, CompositeListItem):
            self.parent.select_from_child(self, *args)

    def deselect(self, *args):
        self.background_color = self.deselected_color
        if isinstance(self.parent, CompositeListItem):
            self.parent.deselect_from_child(self, *args)

    def select_from_composite(self, *args):
        self.background_color = self.selected_color

    def deselect_from_composite(self, *args):
        self.background_color = self.deselected_color


# [TODO] Why does this mix in SelectableView -- that makes it work like
#        button, which is redundant.

class ListItemLabel(ListItemReprMixin, SelectableView, Label):
    ''':class:`~kivy.uix.listview.ListItemLabel` mixes
    :class:`~kivy.uix.selectableview.SelectableView` with
    :class:`~kivy.uix.label.Label` to produce a label suitable for use in
    :class:`~kivy.uix.listview.ListView`.
    '''

    def __init__(self, **kwargs):
        super(ListItemLabel, self).__init__(**kwargs)

    def select(self, *args):
        self.bold = True
        if isinstance(self.parent, CompositeListItem):
            self.parent.select_from_child(self, *args)

    def deselect(self, *args):
        self.bold = False
        if isinstance(self.parent, CompositeListItem):
            self.parent.deselect_from_child(self, *args)

    def select_from_composite(self, *args):
        self.bold = True

    def deselect_from_composite(self, *args):
        self.bold = False


class CompositeListItem(SelectableView, BoxLayout):
    ''':class:`~kivy.uix.listview.CompositeListItem` mixes
    :class:`~kivy.uix.selectableview.SelectableView` with :class:`BoxLayout` for a
    generic container-style list item, to be used in
    :class:`~kivy.uix.listview.ListView`.
    '''

    background_color = ListProperty([1, 1, 1, 1])
    '''ListItem subclasses Button, which has background_color, but
    for a composite list item, we must add this property.

    :attr:`background_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [1, 1, 1, 1].
    '''

    selected_color = ListProperty([1., 0., 0., 1])
    '''
    :attr:`selected_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [1., 0., 0., 1].
    '''

    deselected_color = ListProperty([.33, .33, .33, 1])
    '''
    :attr:`deselected_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [.33, .33, .33, 1].
    '''

    representing_cls = ObjectProperty(None)
    '''Which component view class, if any, should represent for the
    composite list item in __repr__()?

    :attr:`representing_cls` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    def __init__(self, **kwargs):
        cls_dicts = kwargs.pop('cls_dicts')
        text = kwargs.pop('text', None)
        index = kwargs['index']
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

        for cls_dict in cls_dicts:
            cls = cls_dict['cls']
            cls_kwargs = cls_dict.get('kwargs', None)

            if cls_kwargs:
                cls_kwargs['index'] = index

                if 'text' not in cls_kwargs and text:
                    cls_kwargs['text'] = text

                if 'is_representing_cls' in cls_kwargs:
                    del cls_kwargs['is_representing_cls']
                    self.representing_cls = cls

                self.add_widget(cls(**cls_kwargs))
            else:
                cls_kwargs = {}
                cls_kwargs['index'] = index
                if text is not None:
                    cls_kwargs['text'] = text
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
            return '<%r>, representing <%s>' % (
                self.representing_cls, self.__class__.__name__)
        else:
            return '<%s>' % (self.__class__.__name__)


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
    ''':class:`~kivy.uix.listview.ListView` is a primary high-level widget,
    handling the common task of presenting items in a scrolling list.
    Flexibility is afforded by use of a variety of adapters to interface with
    data.

    The adapter property comes via the mixed in
    :class:`~kivy.uix.abstractview.AbstractView` class.

    :class:`~kivy.uix.listview.ListView` also subclasses
    :class:`EventDispatcher` for scrolling. The event *on_scroll_complete* is
    used in refreshing the main view.

    For a simple list of string items, without selection, use
    :class:`~kivy.adapters.simplelistadapter.SimpleListAdapter`. For list items
    that respond to selection, ranging from simple items to advanced
    composites, use :class:`~kivy.adapters.listadapter.ListAdapter`. For an
    alternate powerful adapter, use
    :class:`~kivy.adapters.dictadapter.DictAdapter`, rounding out the choice
    for designing highly interactive lists.

    :Events:
        `on_scroll_complete`: (boolean, )
            Fired when scrolling completes.
    '''

    divider = ObjectProperty(None)
    '''[TODO] Not used.
    '''

    divider_height = NumericProperty(2)
    '''[TODO] Not used.
    '''

    container = ObjectProperty(None)
    '''The container is a :class:`~kivy.uix.gridlayout.GridLayout` widget held
    within a :class:`~kivy.uix.scrollview.ScrollView` widget.  (See the
    associated kv block in the Builder.load_string() setup). Item view
    instances managed and provided by the adapter are added to this container.
    The container is cleared with a call to clear_widgets() when the list is
    rebuilt by the populate() method. A padding
    :class:`~kivy.uix.widget.Widget` instance is also added as needed,
    depending on the row height calculations.

    :attr:`container` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    row_height = NumericProperty(None)
    '''The row_height property is calculated on the basis of the height of the
    container and the count of items.

    :attr:`row_height` is a :class:`~kivy.properties.NumericProperty` and
    defaults to None.
    '''

    item_strings = ListProperty([])
    '''If item_strings is provided, create an instance of
    :class:`~kivy.adapters.simplelistadapter.SimpleListAdapter` with this list
    of strings, and use it to manage a no-selection list.

    :attr:`item_strings` is a :class:`~kivy.properties.ListProperty` and
    defaults to [].
    '''

    scrolling = BooleanProperty(False)
    '''If the scroll_to() method is called while scrolling operations are
    happening, a call recursion error can occur. scroll_to() checks to see that
    scrolling is False before calling populate(). scroll_to() dispatches a
    scrolling_complete event, which sets scrolling back to False.

    :attr:`scrolling` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    _index = NumericProperty(0)
    _sizes = DictProperty({})
    _count = NumericProperty(0)

    _wstart = NumericProperty(0)
    _wend = NumericProperty(-1)

    __events__ = ('on_scroll_complete', )

    @deprecated
    def __init__(self, **kwargs):
        # Check for an adapter argument. If it doesn't exist, we
        # check for item_strings in use with SimpleListAdapter
        # to make a simple list.
        if 'adapter' not in kwargs:
            if 'item_strings' not in kwargs:
                # Could be missing, or it could be that the ListView is
                # declared in a kv file. If kv is in use, and item_strings is
                # declared there, then item_strings will not be set until after
                # __init__(). So, the data=[] set will temporarily serve for
                # SimpleListAdapter instantiation, with the binding to
                # item_strings_changed() handling the eventual set of the
                # item_strings property from the application of kv rules.
                list_adapter = SimpleListAdapter(data=[],
                                                 cls=Label)
            else:
                list_adapter = SimpleListAdapter(data=kwargs['item_strings'],
                                                 cls=Label)
            kwargs['adapter'] = list_adapter

        super(ListView, self).__init__(**kwargs)

        populate = self._trigger_populate = Clock.create_trigger(
            self._spopulate, -1)
        self._trigger_reset_populate = \
            Clock.create_trigger(self._reset_spopulate, -1)

        fbind = self.fbind
        fbind('size', populate)
        fbind('pos', populate)
        fbind('item_strings', self.item_strings_changed)
        fbind('adapter', populate)

        bind_adapter = self._trigger_bind_adapter = Clock.create_trigger(
            lambda dt: self.adapter.bind_triggers_to_view(
                self._trigger_reset_populate),
            -1)
        fbind('adapter', bind_adapter)

        # The bindings setup above sets self._trigger_populate() to fire
        # when the adapter changes, but we also need this binding for when
        # adapter.data and other possible triggers change for view updating.
        # We don't know that these are, so we ask the adapter to set up the
        # bindings back to the view updating function here.
        bind_adapter()

    # Added to set data when item_strings is set in a kv template, but it will
    # be good to have also if item_strings is reset generally.
    def item_strings_changed(self, *args):
        self.adapter.data = self.item_strings

    def _scroll(self, scroll_y):
        if self.row_height is None:
            return
        self._scroll_y = scroll_y
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

    def _spopulate(self, *args):
        self.populate()

    def _reset_spopulate(self, *args):
        self._wend = -1
        self.populate()
        # simulate the scroll again, only if we already scrolled before
        # the position might not be the same, mostly because we don't know the
        # size of the new item.
        if hasattr(self, '_scroll_y'):
            self._scroll(self._scroll_y)

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
        if iend is not None and iend != -1:

            # fill with a "padding"
            fh = 0
            for x in range(istart):
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
