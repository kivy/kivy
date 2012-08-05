##[TODO LIST for kivy uix-listview]:
#
#    - *** FIXED *** Initial selection is apparently working in the associated
#      ListAdapter but the listview display does not show the initial
#      selection (red, in example code). After the listview has been clicked
#      for the first manual selection, the updating of selected items (in red)
#      works.
#
#    - Explain why multiple levels of abstraction are needed. (Adapter,
#      ListAdapter, AbstractView, ListView) -- Tie discussion to inspiration
#      for Adapter and related classes:
#
#          http://developer.android.com/reference/android/\
#              widget/Adapter.html#getView(int,%20android/\
#              .view.View,%20android.view.ViewGroup)
#
#      There is now an ASCII drawing of the relationship between ListView and
#      ListAdapter, as it is now, in the docs below.
#
#    - Divider isn't used (yet).
#
#    - Consider adding an associated SortableItem mixin, to be used by list
#      item classes in a manner similar to the SelectableItem mixin.
#
#    - Consider a sort_by property. Review the use of the items property.
#      (Presently items is a list of strings -- are these just the
#       strings representing the item_view_instances, which are instances of
#       the provided cls input argument?). If so, formalize and document.
#
#    - Work on item_view_instances marked [TODO] in the code.
#
#    Examples (in examples/widgets):
#
#    - Improve examples:
#        - *** DONE *** Add fruit images.
#
#    - Add an example where selection doesn't just change background color
#      or font, but animates.
#
#    Other Possibilities:
#
#    - Consider a horizontally scrolling variant.
#
#    - Is it possible to have dynamic item_view height, for use in a
#      master-detail listview in this manner?
#
#        http://www.zkoss.org/zkdemo/grid/master_detail
#
#      (Would this be a new widget called MasterDetailListView, or would the
#       listview widget having a facility for use in this way?)
#
#      (See the list_disclosure.py file as a start.)
#
#    - Make a separate master-detail example that works like an iphone-style
#      animated "source list" that has "disclosure" buttons per item_view, on
#      the right, that when clicked will expand to fill the entire listview
#      area (useful on mobile devices especially). Similar question as above --
#      would listview be given expanded functionality or would this become
#      another kind of "master-detail" widget?)

'''
List View
===========

.. versionadded:: 1.4

The :class:`ListView` widget provides a scrollable/pannable viewport that is
clipped at the scrollview's bounding box, which contains a list of
list item view instances.

:class:`ListView` implements AbstractView as a vertical scrollable list.
From AbstractView we have these properties and methods:

    - adapter (an instance of SimpleListAdapter, or ListAdapter or one of its
      subclasses here)

    - item_view_instances, a dict with indices as keys to the list item view
      instances created in the ListAdapter

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

If you were to dig deeper into the basic example above, you would find that it
uses :class:`SimpleListAdapter` behind the scenes. When the constructor for
:class:`ListView` sees that only a list of strings is provided as an argument
called item_strings, it creates an instance of :class:`SimpleListAdapter` with
the list of strings. Otherwise, :class:`ListView` must be provide with some
variant of ListAdapter.

Simple in the example above means: WITHOUT SELECTION SUPPORT -- it is just a
scrollable list of items, which do not respond to touch events.

If you wanted to use :class:`SimpleListAdaper` explicitly in creating a ListView
instance, you could do:

    simple_list_adapter = \
        SimpleListAdapter(data=["Item #{0}".format(i) for i in xrange(100)],
                          cls=Label)
    list_view = ListView(adapter=simple_list_adapter)

For most uses of a list, however, selection support IS needed. Selection
support is built in to :class:`ListAdapter`. :class:`ListAdapter` and its
subclasses offer support for building moderately to highly complex listviews
with selection support.

See the :class:`ListAdapter` docs for details, but here we have synopses of
its arguments:

    - data: the list of objects, be they strings or other objects, that are
            used as the primary source of item data for the list items

    - cls: the Kivy view that is to be instantiated for each list item. There
           are several built-in types available, including ListItemLabel and
           ListItemButton, or you can easily make your own.

    - template: another way of building a Kivy view for a list item, taking
                adavantage of the flexibility of the kv language.

    NOTE: Pick only one, cls or template, as argument to :class:`ListAdapter`.

    - args_converter: a function that takes a list item object (which is often
                      just a string) as input, and operates to use the object
                      in some fashion to build and return an args dict, ready
                      to be used in a call to instantiate the item view cls
                      or template. In the case of cls, the args dict acts as a
                      kwargs object. For a template, it is treated as a
                      context (ctx), but is essentially similar in form. See
                      the examples and docs for template operation.

    - selection arguments: These include:

          selection_mode='single', 'multiple' or others (See docs), and

          allow_empty_selection=False, which forces there to always be a
                                       selection, if there is data available,
                                       or =True, if selection is to be
                                       restricted to happen as a result of
                                       user action.

In narrative, we can summarize with:

    A listview's list adapter takes data items and uses an args_converter
    function to transform them into arguments for making list item view
    classes, using either a provided cls or a kv template.

In a graphic, a summary of the relationship between a listview and its
list adapter, looks something like this:

    -                    ------------------- ListAdapter --------------------
    -                    |                                                  |
    -                    | <list item views> (cls or template) <data items> |
    -   ListView   -->   |                           [args_converter]       |
    -                    |                                                  |
    -                    |           <<< selection handling >>>             |
    -                    |                                                  |
    -                    ----------------------------------------------------

The Kivy view used for list items can be totally custom, but for an example,
we can start with a list item as a button, using the :class:`ListItemButton`
class, and the list_item_args_converter, available in kivy.adapters.util. Here
is its definition:

    list_item_args_converter = lambda x: {'text': x,
                                          'size_hint_y': None,
                                          'height': 25}

list_item_args_converter() takes a data item (x, a string in this usage), and
prepares an args dict (to be used as kwargs for cls/ctx for template) with x
as the text value, and the other two default arguments for layout. It is easy
to make your own args converter, more complicated that this one.

Now, to the example code:

    from kivy.adapters.list_adapter import ListAdapter
    from kivy.adapters.util import list_item_args_converter
    from kivy.uix.listview import ListItem, ListView

    data = ["Item {0}".format(index) for index in xrange(100)]

    list_adapter = ListAdapter(data=data,
                               args_converter=list_item_args_converter,
                               selection_mode='single',
                               allow_empty_selection=False,
                               cls=ListItemButton)
    list_view = ListView(adapter=list_adapter)

This listview will show 100 buttons with a "Item 0", "Item 1", etc. labels.
The listview will only allow single selection -- additional touches will be
ignored. When the listview is first shown, the first item will already be
selected, because we set allow_empty_selection=False.

Selection in ListAdapter, for ListView
--------------------------------------

In the previous example, we saw how a listview gains selection support just by
using ListAdapter.

What can we do with selection? The possibilities are wide-ranging.

We could change the data item strings to be the names of dog breeds, and we
could bind the selection to the display of details for the selected dog breed
in another view, which would update in realtime.

We could change the selection_mode to 'multiple' and put up a list of answers
in a multiple-choice question that has several correct answers. A realtime
color swatch view could be bound to selection, turning green as soon as the
correct choices are made, unless the number of touches exeeds a limit, and it
bombs out.

We could chain together three listviews, where selection in the first
controls the items shown in the second, and selection in the second controls
the items shown in the third. If allow_empty_selection were set to False for
these listviews, a dynamic system, a "cascade" from one list to the next,
would result.

And so on.

To bind to selection of a :class:ListAdapter instance, bind to the
on_selection_change event:

    list_adapter.bind(on_selection_change=my_selection_reactor_function)

Ideas for Selection Ops
-----------------------

The examples below, and the on-disk working examples, illustrate ways to use
:class:`ListView` and list adapters. Here are some other ideas for operations
that happen when on_selection_change fires:

    - Use a search directive phrase set in a text box, and find items,
      relative to the current selection, items with time values within a
      certain range, or items that have a greater length of text than that of
      the current selection, and so on.

    - Select items that qualify against a hard-wired search directive.

    - Select items by proximity to the current selected item, say for finding
      three items above and below it.

    - Select items because they are owned by the same user that owns the
      current selected item.

Composite List Item Example
---------------------------

Let's say you would like to make a listview with composite list item views
consisting of a button on the left, a label in the middle, and a second button
on the right. Perhaps the buttons could be made as toggle buttons for two
separate properties pertaining to the label. We add default buttons and a
label in this example.

    from kivy.adapters.listadapter import ListAdapter
    from kivy.uix.listview import ListItemButton, ListItemLabel, \
            CompositeListItem, ListView
    from kivy.uix.gridlayout import GridLayout


    class MainView(GridLayout):

        def __init__(self, **kwargs):
            kwargs['cols'] = 2
            kwargs['size_hint'] = (1.0, 1.0)
            super(MainView, self).__init__(**kwargs)

            # This is quite an involved args_converter, so we should go
            # through the details. x here is a data item object, be it
            # a string for a typical usage, as here, or some other object.
            # x will become the text value when the class used in this
            # example, CompositeListItem, is instantiated with the args
            # returned by this converter. All of the rest, for size_hint_y,
            # height, and the cls_dicts list, will be passed in the call
            # to instantiate CompositeListItem for a data item. Inside the
            # constructor of CompositeListItem is special-handling code that
            # uses cls_dicts to create, in turn, the component items in the
            # composite. This is a similar approach to using a kv template,
            # which you might wish to explore also.
            args_converter = \
                lambda x: \
                    {'text': x,
                     'size_hint_y': None,
                     'height': 25,
                     'cls_dicts': [{'cls': ListItemButton,
                                    'kwargs': {'text': "Left",
                                               'merge_text': True,
                                               'delimiter': '-'}},
                                   {'cls': ListItemLabel,
                                    'kwargs': {'text': "Middle",
                                               'merge_text': True,
                                               'delimiter': '-',
                                               'is_representing_cls': True}},
                                   {'cls': ListItemButton,
                                    'kwargs': {'text': "Right",
                                               'merge_text': True,
                                               'delimiter': '-'}}]}

            # First, some strings as data items:
            item_strings = ["{0}".format(index) for index in xrange(100)]

            # And now the list adapter, constructed with the item_strings as
            # the data, and our args_converter() that will operate one each
            # item in the data to produce list item view instances from the
            # :class:`CompositeListItem` class.
            list_adapter = ListAdapter(data=item_strings,
                                       args_converter=args_converter,
                                       selection_mode='single',
                                       allow_empty_selection=False,
                                       cls=CompositeListItem)

            # Use the adapter in our ListView:
            list_view = ListView(adapter=list_adapter)

            self.add_widget(list_view)


    if __name__ == '__main__':
        from kivy.base import runTouchApp
        runTouchApp(MainView(width=800))

Using With kv
-------------

To make a simple list with labels for 100 integers:

    from kivy.adapters.listadapter import ListAdapter
    from kivy.adapters.mixins.selection import SelectableItem
    from kivy.uix.listview import ListView, ListItemButton
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.boxlayout import BoxLayout
    from kivy.lang import Builder
    from kivy.factory import Factory

    Factory.register('SelectableItem', cls=SelectableItem)
    Factory.register('ListItemButton', cls=ListItemButton)

    # Note: If you copy this example, change the triple_quote tag markers to
    #       triple single quotes.
    Builder.load_string(<triple_quotes>
    [CustomListItem@SelectableItem+BoxLayout]:
        size_hint_y: ctx.size_hint_y
        height: ctx.height
        ListItemButton:
            text: ctx.text
    <triple_quotes>)


    class MainView(GridLayout):

        def __init__(self, **kwargs):
            kwargs['cols'] = 1
            kwargs['size_hint'] = (1.0, 1.0)
            super(MainView, self).__init__(**kwargs)

            # Here we create a list adapter with some item strings, passing our
            # CompositeListItem kv template for the list item view, and then we
            # create a listview using this adapter. As we have not provided an
            # args converter to the list adapter, the default args converter
            # will be used. It creates, per list item, an args dict with the
            # text set to the data item (in this case a string label for an
            # integer index), and two default properties: size_hint_y=None and
            # height=25. To customize, make your own args converter and/or
            # customize the kv template.
            list_adapter = ListAdapter(data=[str(i) for i in xrange(100)],
                                       template='CustomListItem')
            list_view = ListView(adapter=list_adapter)

            self.add_widget(list_view)


    if __name__ == '__main__':
        from kivy.base import runTouchApp
        runTouchApp(MainView(width=800))

Cascading Selection Between Lists and Views
-------------------------------------------

A "master-detail" view is a good way to introduce binding of a listview to
another view. We can call the listview the "master" and the second view,
the "detail" view, forming a master-detail pairing. This would fit the dog
breed idea mentioned above, where we wish to show a list of dog breed names,
from which one is selected, and in the second view show the details of the
selected dog breed.

    class DetailView(BoxLayout):
        #
        # DETAILS NOT SHOWN -- has multiple labels for dog breed details in a
        # panel. To see a real example, see the on-disk examples, such as:
        #
        #    kivy/examples/widgets/lists/list_master_detail.py
        #
        #    def dog_breed_changed(self, list_adapter, *args):
        #        #
        #        # Code here for taking list_adapter.selection, a dog breed in
        #        # this case, and populating image views, label views with
        #        # details for the breed, etc., coming from some source, such
        #        # a database lookup.
        #        #
        #        pass
        pass

    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.listview import ListView, ListItemButton
    from kivy.adapters.listadapter import ListAdapter


    class MasterDetailView(GridLayout):

        def __init__(self, items, **kwargs):
            kwargs['cols'] = 2
            kwargs['size_hint'] = (1.0, 1.0)
            super(MasterDetailView, self).__init__(**kwargs)

            args_converter = lambda x: {'text': x,
                                        'size_hint_y': None,
                                        'height': 50}

            list_adapter = ListAdapter(data=['Golden Retriever', 'Bulldog',
                                             'Collie', 'Poodle', 'Bulldog'],
                                       args_converter=args_converter,
                                       selection_mode='single',
                                       allow_empty_selection=False,
                                       cls=ListItemButton)
            master_list_view = ListView(adapter=list_adapter,
                                        size_hint=(.3, 1.0))
            self.add_widget(master_list_view)

            detail_view = DetailView(size_hint=(.7, 1.0))
            self.add_widget(detail_view)

            list_adapter.bind(
                    on_selection_change=detail_view.dog_breed_changed)

            # Force triggering of on_selection_change() for the DetailView, for
            # correct initial display.
            list_adapter.touch_selection()


    if __name__ == '__main__':
        from kivy.base import runTouchApp
        master_detail = MasterDetailView(width=800)
        runTouchApp(master_detail)

More Examples
-------------

There are so many ways that listviews and related functionality can be used,
that we have only scratched the surface here. For on-disk examples like the
ones presented above, plus others that show more complicated use, see:

        kivy/examples/widgets/lists/list_*.py

'''

__all__ = ('ListView', )

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.adapters.listadapter import SimpleListAdapter
from kivy.adapters.mixins.selection import SelectableItem
from kivy.uix.abstractview import AbstractView
from kivy.properties import ObjectProperty, DictProperty, \
        NumericProperty, ListProperty
from kivy.lang import Builder
from math import ceil, floor


class ListItemButton(SelectableItem, Button):
    selected_color = ListProperty([1., 0., 0., 1])
    deselected_color = None

    def __init__(self, **kwargs):
        super(ListItemButton, self).__init__(**kwargs)

        # Set deselected_color to be default Button bg color.
        self.deselected_color = self.background_color

    def select(self, *args):
        self.background_color = self.selected_color

    def deselect(self, *args):
        self.background_color = self.deselected_color

    def __repr__(self):
        return self.text


class ListItemLabel(SelectableItem, Label):

    def __init__(self, **kwargs):
        super(ListItemLabel, self).__init__(**kwargs)

    def select(self, *args):
        self.bold = True

    def deselect(self, *args):
        self.bold = False

    def __repr__(self):
        return self.text


class CompositeListItem(SelectableItem, BoxLayout):

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
                        cls_kwargs['text'] = "{0}{1}{2}".format(
                                cls_kwargs['text'],
                                cls_kwargs['delimiter'],
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


class ListView(AbstractView):

    divider = ObjectProperty(None)
    '''[TODO] Not used.
    '''

    divider_height = NumericProperty(2)
    '''[TODO] Not used.
    '''

    container = ObjectProperty(None)
    '''The container is a GridLayout widget held within a ScrollView widget.
    (See the associated kv block in the Builder.load_string() setup). Item
    view instances managed and provided by the ListAdapter are added to this
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

    _index = NumericProperty(0)
    _sizes = DictProperty({})
    _count = NumericProperty(0)

    _wstart = NumericProperty(0)
    _wend = NumericProperty(None)

    def __init__(self, **kwargs):
        # Intercept for the adapter property, which would pass through to
        # AbstractView, to check for its existence. If it doesn't exist, we
        # assume that the data list is to be used with ListAdapter
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
        self.adapter.bind(data=self._trigger_hard_populate)

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
