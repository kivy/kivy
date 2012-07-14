'''
List View
===========

.. versionadded:: 1.4

The :class:`ListView` widget provides a scrollable/pannable viewport that is
clipped at the scrollview's bounding box, which contains a list of
item_view_instances.

[TODO]:

    - Are multiple levels of abstraction needed? Explain why. (Adapter,
      ListAdapter, AbstractView, ListView).
    - Consider an associated "object adapter" (a.k.a., "object controller")
      that is bound to the selection.
    - Also, what about an associated "array adapter/controller" bound to the
      selection? (For a cascade of several listviews).
    - Settle terminology question: adapter or controller?
    - Divider isn't used (yet).
    - Add associated SortableItem mixin, to be used by list item_view classes
      in a manner similar to the SelectableItem mixin.
    - Add a sort_by property for use with sortable item_view_instances. (See
      next item: is the item_keys list set to one property of the list item
      cls?)
    - Review the use of item_keys in association with sortable
      item_view_instances.
      (Presently item_keys is a list of strings -- are these just the
       strings representing the item_view_instances, which are instances of
       the provided item_view_cls input argument?). If so, formalize and
       document.
    - Address question about "pushing" out to registered selection observers,
      vs. using the built-in Kivy event dispatching for an "on_select" event.
      (Will event dispatching work instead of registering/pushing?). Merits?
    - Work on item_view_instances marked [TODO] in the code.

    Examples (in examples/widgets):

    - Improve examples:
        - Add fruit images.
    - Add an example where selection doesn't just change background color
      or font, but animates.

    Other Possibilities:

    - Consider a horizontally scrolling variant.
    - Is it possible to have dynamic item_view height, for use in a
      master-detail list view in this manner?

        http://www.zkoss.org/zkdemo/grid/master_detail

      (Would this be a new widget called MasterDetailListView, or would the
       listview widget having a facility for use in this way?)
    - Make a separate master-detail example that works like an iphone-style
      animated "source list" that has "disclosure" buttons per item_view, on
      the right, that when clicked will expand to fill the entire list view
      area (useful on mobile devices especially). Similar question as above --
       would listview be given expanded functionality or would this become
       another kind of "master-detail" widget?)
'''

__all__ = ('ListView', )

from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, DictProperty, \
                            NumericProperty, ListProperty
from kivy.lang import Builder
from math import ceil, floor
from kivy.uix.mixins.selection import SelectionSupport

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


class Adapter(SelectionSupport, EventDispatcher):
    '''Adapter is a bridge between an AbstractView and the data.
    '''

    # These pertain to item views:
    cls = ObjectProperty(None)
    template = ObjectProperty(None)
    args_converter = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.register_event_type('on_select')
        super(Adapter, self).__init__(**kwargs)
        if self.cls is None and self.template is None:
            raise Exception('A cls or template must be defined')
        if self.cls is not None \
                and self.template is not None:
            raise Exception('Cannot use cls and template at the same time')

    def get_count(self):
        raise NotImplementedError()

    def get_item(self, index):
        raise NotImplementedError()

    def get_item_view_instance(self, index):
        item = self.get_item(index)
        item_args = None
        if item is None:
            return None
        if self.args_converter:
            item_args = self.args_converter(item)
        else:
            item_args = item
        if self.cls:
            print 'CREATE VIEW FOR', index
            instance = self.cls(
                selection_callback=self.handle_selection,
                **item_args)
            return instance
        return Builder.template(self.template, **item_args)

    # This is for the list adapter, if it wants to get selection events.
    def on_select(self, *args):
        pass

    # [TODO] Things to think about:
    #
    # There are other possibilities:
    #
    #         Additional possibilities, to those stubbed out in
    #         methods below.
    #
    #             - a boolean for whether or not editing of item_view_instances
    #               is allowed
    #             - a boolean for whether or not to destroy on removal (if
    #               applicable)
    #             - guards for adding, removing, sorting item_view_instances
    #

    # [TODO]
    def add_item_view(self, item_view):
        pass

    # [TODO]
    def remove_item_view(self, item_view):
        pass

    # [TODO]
    def replace_item_view(self, item_view):
        pass

    # [TODO]
    # This method would have an associated sort_key property.
    def sorted_item_view_instances(self):
        pass


class ListAdapter(Adapter):
    '''Adapter around a simple Python list
    '''
    item_keys = ListProperty([])

    def __init__(self, item_keys, **kwargs):
        if type(item_keys) not in (tuple, list):
            raise Exception('ListAdapter: input must be a tuple or list')
        super(ListAdapter, self).__init__(**kwargs)

        # Reset and update selection, in SelectionSupport, if item_keys
        # gets reset.
        self.bind(item_keys=self.initialize_selection)

        # Do the initial set.
        self.item_keys = item_keys

    def get_count(self):
        return len(self.item_keys)

    def get_item(self, index):
        if index < 0 or index >= len(self.item_keys):
            return None
        return self.item_keys[index]


class AbstractView(FloatLayout):
    '''View using an Adapter as a data provider
    '''

    adapter = ObjectProperty(None)

    item_view_instances = DictProperty({})

    def set_item_view(self, index, item_view):
        pass

    def get_item_view(self, index):
        item_view_instances = self.item_view_instances
        if index in item_view_instances:
            return item_view_instances[index]
        item_view = self.adapter.get_item_view_instance(index)
        if item_view:
            item_view_instances[index] = item_view
        return item_view


class ListView(AbstractView):
    '''Implementation of an Abstract View as a vertical scrollable list.
    '''

    divider = ObjectProperty(None)

    divider_height = NumericProperty(2)

    container = ObjectProperty(None)

    row_height = NumericProperty(None)

    _index = NumericProperty(0)
    _sizes = DictProperty({})
    _count = NumericProperty(0)

    _wstart = NumericProperty(0)
    _wend = NumericProperty(None)

    def __init__(self, **kwargs):
        super(ListView, self).__init__(**kwargs)
        self._trigger_populate = Clock.create_trigger(self._spopulate, -1)
        self.bind(size=self._trigger_populate,
                pos=self._trigger_populate,
                adapter=self._trigger_populate)
        self.populate()

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
        print 'populate', istart, iend
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
