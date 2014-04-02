__all__ = ('SelectableView', 'ListItemButton', 'ListItemLabel',
           'CompositeListItem', 'ListView', )

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.abstractview import AbstractView
from kivy.properties import ObjectProperty, DictProperty, \
        NumericProperty, ListProperty, BooleanProperty, AliasProperty
from kivy.lang import Builder
from math import ceil, floor


class SelectableView(object):
    '''The :class:`~kivy.uix.listview.SelectableView` mixin is used to design
    list item and other classes that are to be instantiated by an adapter to be
    used in a listview.  The :class:`~kivy.adapters.listadapter.ListAdapter`
    and :class:`~kivy.adapters.dictadapter.DictAdapter` adapters are
    selection-enabled. select() and deselect() are to be overridden with
    display code to mark items as selected or not, if desired.
    '''

    index = NumericProperty(-1)
    '''The index into the underlying data list or the data item this view
    represents.

    :attr:`index` is a :class:`~kivy.properties.NumericProperty`, default
    to -1.
    '''

    is_selected = BooleanProperty(False)
    '''A SelectableView instance carries this property, which should be kept
    in sync with the equivalent property in the data item it represents.

    :attr:`is_selected` is a :class:`~kivy.properties.BooleanProperty`, default
    to False.
    '''

    def __init__(self, **kwargs):
        super(SelectableView, self).__init__(**kwargs)
        self.bind(is_selected=self._do_selection)

    def _do_selection(self, *args):
        if self.is_selected:
            self.select()
        else:
            self.deselect()

    def select(self, *args):
        '''The list item is responsible for updating the display for
        being selected, if desired.
        '''
        pass

    def deselect(self, *args):
        '''The list item is responsible for updating the display for
        being unselected, if desired.
        '''
        pass


class ListItemButton(SelectableView, Button):
    ''':class:`~kivy.uix.listview.ListItemButton` mixes
    :class:`~kivy.uix.listview.SelectableView` with
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
    :attr:`selected_color` is a :class:`~kivy.properties.ListProperty` and
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

    def __repr__(self):
        return '<%s text=%s>' % (self.__class__.__name__, self.text)


# [TODO] Why does this mix in SelectableView -- that makes it work like
#        button, which is redundant.

class ListItemLabel(SelectableView, Label):
    ''':class:`~kivy.uix.listview.ListItemLabel` mixes
    :class:`~kivy.uix.listview.SelectableView` with
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

    def __repr__(self):
        return '<%s text=%s>' % (self.__class__.__name__, self.text)


class CompositeListItem(SelectableView, BoxLayout):
    ''':class:`~kivy.uix.listview.CompositeListItem` mixes
    :class:`~kivy.uix.listview.SelectableView` with :class:`BoxLayout` for a
    generic container-style list item, to be used in
    :class:`~kivy.uix.listview.ListView`.
    '''

    background_color = ListProperty([1, 1, 1, 1])
    '''ListItem sublasses Button, which has background_color, but
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
                cls_kwargs['index'] = index
                if 'text' in kwargs:
                    cls_kwargs['text'] = kwargs['text']
                self.add_widget(cls(**cls_kwargs))
        
    def on_parent(self, *args):
        #To avoid blindly binding ANY & ALL `Button` class' children to handle_selection, we explicitly do it here.
        #Yes, there is definitely a better way. Will leave that to geojeff.
        if self.parent:
            handle_selection = self.parent.parent.parent.adapter.handle_selection

            for child in self.children:
                child.bind(on_release=self.handle_selection)

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


class ListView(AbstractView):
    ''':class:`~kivy.uix.listview.ListView` is a primary high-level widget,
    handling the common task of presenting items in a scrolling list.
    Flexibility is afforded by use of a `ListAdapter` to interface with data.
    
    #:class:`~kivy.uix.listview.ListView` also subclasses
    #:class:`EventDispatcher` for scrolling.  The event *on_scroll_complete* is
    #used in refreshing the main view.
    # Why...?

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

    scrolling = BooleanProperty(False)
    '''If the scroll_to() method is called while scrolling operations are
    happening, a call recursion error can occur. scroll_to() checks to see that
    scrolling is False before calling populate(). scroll_to() dispatches a
    scrolling_complete event, which sets scrolling back to False.

    :attr:`scrolling` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''
    
    adapter = ObjectProperty(ListAdapter())
    
    def _get_args_converter(self):
        return self.adapter.args_converter

    def _set_args_converter(self, a_c):
        if a_c is self.adapter.args_converter:
            return False
        else:
            self.adapter.args_converter = a_c
            
    args_converter = AliasProperty(_get_args_converter, _set_args_converter, bind=('adapter',))
    
    def _get_data(self):
        return self.adapter.data
        
    def _set_data(self, data):
        if data is self.adapter.data:
            return False
        else:
            self.adapter.data = data

    data = AliasProperty(_get_data, _set_data, bind=('adapter',))
    
    def _get_list_item(self):
        return self.adapter.cls
        
    def _set_list_item(self, item):
        if item is self.adapter.cls:
            return False
        else:
            self.adapter.cls = item

    list_item = AliasProperty(_get_list_item, _set_list_item, bind=('adapter',))
    
    def _get_selection_mode(self):
        return self.adapter.selection_mode
        
    def _set_selection_mode(self, sm):
        if sm == self.adapter.selection_mode:
            return False
        else:
            self.adapter.selection_mode = sm
            
    selection_mode = AliasProperty(_get_selection_mode, _set_selection_mode, bind=('adapter',))
    
    def _get_propagate_selection_to_data(self):
        return self.adapter.propagate_selection_to_data
    
    def _set_propagate_selection_to_data(self, value):
        if value == self.adapter.propagate_selection_to_data:
            return False
        else:
            self.adapter.propagate_selection_to_data = value
            
    propagate_selection_to_data = AliasProperty(_get_propagate_selection_to_data, _set_propagate_selection_to_data, bind=('adapter',))
            
    def _get_allow_empty_selection(self):
        return self.adapter.allow_empty_selection
        
    def _set_allow_empty_selection(self, value):
        if value == self.adapter.allow_empty_selection:
            return False
        else:
            self.adapter.allow_empty_selection = value
            
    allow_empty_selection = AliasProperty(_get_allow_empty_selection, _set_allow_empty_selection, bind=('adapter',))
    
    def _get_selection_limit(self):
        return self.adapter.selection_limit
        
    def _set_selection_limit(self, value):
        if value == self.adapter.selection_limit
            return False
        else:
            self.adapter.selection_limit = value
            
    selection_limit = AliasProperty(_get_selection_limit, _set_selection_limit, bind=('adapter',))

    _index = NumericProperty(0)
    _sizes = DictProperty({})
    _count = NumericProperty(0)

    _wstart = NumericProperty(0)
    _wend = NumericProperty(None, allownone=True)

    __events__ = ('on_scroll_complete', )

    def __init__(self, **kwargs):
        super(ListView, self).__init__(**kwargs)

        self._trigger_populate = Clock.create_trigger(self._spopulate, -1)
        self._trigger_reset_populate = \
            Clock.create_trigger(self._reset_spopulate, -1)

        self.bind(size=self._trigger_populate,
                  pos=self._trigger_populate,
                  adapter=self._trigger_populate)

        # The bindings setup above sets self._trigger_populate() to fire
        # when the adapter changes, but we also need this binding for when
        # adapter.data and other possible triggers change for view updating.
        # We don't know that these are, so we ask the adapter to set up the
        # bindings back to the view updating function here.
        self.adapter.bind_triggers_to_view(self._trigger_reset_populate)

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
        self._wend = None
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
        if iend is not None:

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
