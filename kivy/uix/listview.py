'''
List View
===========

.. versionadded:: 1.4

The :class:`ListView` widget provides a scrollable/pannable viewport that is
clipped at the scrollview's bounding box, which contains a list of
list item view instances.

:class:`ListView` implements AbstractView as a vertical scrollable list.
From AbstractView we have these properties and methods:

    - adapter (an instance of ListAdapter or one of its subclasses here)

    - item_view_instances, a dict with indices as keys to the list item view
      instances created and held in the ListAdapter

    - set_item_view() and get_item_view() methods to list item view instances

Basic Example
-------------

The list items you put in a list view can be totally custom, but to have a
simple button, we may use the :class:`ListItem` class.

Here we make a list view with 100 items.

    from kivy.adapters.list_adapter import ListAdapter
    from kivy.uix.listview import ListItem, ListView

    data = ["Item {0}".format(index) for index in xrange(100)]

    # A list view needs a list adapter to provide a mediating service to the
    # data, in the case here our data list, passed as the first
    # argument. We choose single selection mode. We may also set this for
    # allowing multiple selection. We set allow_empty_selection to False so
    # that there is always an item selected if at least one is in the list.
    # Setting this to true will make the list useful for display only.
    # Finally, we pass ListItem as the class (cls) to be instantiated by the
    # list adapter for each list item. ListItem is based on Button. When an
    # item is selected, its background color will change to red.
    list_adapter = ListAdapter(data=data,
                               selection_mode='single',
                               allow_empty_selection=False,
                               cls=ListItem)

    # The list view is a simple component. Just give it the list adapter that
    # will provide list item views based on its data.
    list_view = ListView(adapter=list_adapter)

Composite List Item Example
---------------------------

Let's say you would like to make a list view with composite list item views
consisting of a button on the left, a label in the middle, and a second button
on the right. Perhaps the buttons could be made as toggle buttons for two
separate properties pertaining to the label. First, we need to make a custom
list item, which we will base on the required SelectableItem mixin and our
choice of layout, BoxLayout:

    from kivy.adapters.listadapter import ListAdapter
    from kivy.adapters.mixins.selection import SelectableItem
    from kivy.uix.listview import ListItemButton, ListItemLabel, ListView

    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.properties import ObjectProperty, ListProperty


    class CompositeListItem(SelectableItem, BoxLayout):
        # ListItem sublasses Button, which has background_color.
        # For a composite list item, we must add this property.
        background_color = ListProperty([1, 1, 1, 1])

        selected_color = ListProperty([1., 0., 0., 1])
        deselected_color = ListProperty([.33, .33, .33, 1])

        left_button = ObjectProperty(None)
        middle_label = ObjectProperty(None)
        right_button = ObjectProperty(None)

        def __init__(self, **kwargs):
            super(CompositeListItem, self).__init__(**kwargs)

            # For the component list items in our composite list item, we want
            # their individual selection to select the composite. Here we pass
            # an argument for the list_adapter, required by the SelectableItem
            # mixing, and a selection_target argument, setting it to self (to
            # this composite list item).
            kwargs['selection_target'] = self

            kwargs['text']="left-{0}".format(kwargs['text'])
            self.left_button = ListItemButton(**kwargs)

            kwargs['text']="middle-{0}".format(kwargs['text'])
            self.middle_label = ListItemLabel(**kwargs)

            kwargs['text']="right-{0}".format(kwargs['text'])
            self.right_button = ListItemButton(**kwargs)

            self.add_widget(self.left_button)
            self.add_widget(self.middle_label)
            self.add_widget(self.right_button)

        def select(self, *args):
            self.background_color = self.selected_color

        def deselect(self, *args):
            self.background_color = self.deselected_color

        def __repr__(self):
            if self.middle_label is not None:
                return self.middle_label.text
            else:
                return 'empty'


    class MainView(GridLayout):

        def __init__(self, **kwargs):
            kwargs['cols'] = 2
            kwargs['size_hint'] = (1.0, 1.0)
            super(MainView, self).__init__(**kwargs)

            # Here we create a list adapter with some item strings, passing
            # our CompositeListItem as the list item view class, and then we
            # create list view using this adapter:
            data = ["{0}".format(index) for index in xrange(100)]
            list_adapter = ListAdapter(data=data,
                                       selection_mode='single',
                                       allow_empty_selection=False,
                                       cls=CompositeListItem)
            list_view = ListView(adapter=list_adapter)

            self.add_widget(list_view)

Using With kv
-------------

[TODO]

Cascading Selection Between Lists
---------------------------------

[TODO]

'''

__all__ = ('ListView', )

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.adapters.listadapter import ListAdapter
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

        for cls_dict in kwargs['cls_dicts']:
            cls = cls_dict['cls']
            cls_kwargs = cls_dict['kwargs']

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

            # The list_adapter is instantiating this composite list item,
            # which, as a subclass of SelectableItem, gets a kwargs argument
            # for list_adapter. Here, we are acting in the same fashion, in
            # turn, carrying the list_adapter reference down to the component
            # views.
            cls_kwargs['list_adapter'] = kwargs['list_adapter']

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

    _index = NumericProperty(0)
    _sizes = DictProperty({})
    _count = NumericProperty(0)

    _wstart = NumericProperty(0)
    _wend = NumericProperty(None)

    item_strings = ListProperty([])

    def __init__(self, **kwargs):
        # Intercept for the adapter property, which would pass through to
        # AbstractView, to check for its existence. If it doesn't exist, we
        # assume that the data list is to be used with ListAdapter
        # to make a simple list. If it does exist, and data was also
        # provided, raise an exception, because if an adapter is provided, it
        # should be a fully-fledged adapter with its own data.
        if 'adapter' not in kwargs:
            if item_strings is None:
                raise Exception('ListView: input needed, or an adapter')
            list_adapter = ListAdapter(data=item_strings,
                                       selection_mode='single',
                                       allow_empty_selection=False,
                                       cls=ListItemButton)
            kwargs['adapter'] = list_adapter

        super(ListView, self).__init__(**kwargs)

        self._trigger_populate = Clock.create_trigger(self._spopulate, -1)
        # [TODO] Is this "hard" scheme needed -- better way?
        self._trigger_hard_populate = \
                Clock.create_trigger(self._hard_spopulate, -1)
        self.bind(size=self._trigger_populate,
                  pos=self._trigger_populate,
                  adapter=self._trigger_populate)
        self.adapter.bind(data=self._trigger_hard_populate)

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
        self.item_view_instances = {}
        self.populate()

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
