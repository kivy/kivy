"""
RecycleView
===========

Data accepted: list of dict.

TODO:
    - recycle old widgets based on the class
    - add custom function to get view height
    - add custom function to get view class
    - update view size when created
    - move all internals to adapter
    - selection
"""

from kivy.compat import string_types
from kivy.uix.relativelayout import RelativeLayout
from kivy.lang import Builder
from kivy.properties import NumericProperty, AliasProperty, StringProperty, \
    ObjectProperty
from kivy.factory import Factory

Builder.load_string("""
<RecycleView>:
    ScrollView:
        id: sv
        do_scroll_x: False
        on_scroll_y: root.refresh_from_data()
        RecycleViewLayout:
            id: layout
            size_hint: None, None
            size: root.width, root.computed_height
""")


class RecycleViewLayout(RelativeLayout):
    pass


class RecycleView(RelativeLayout):

    data = ObjectProperty()
    adapter = ObjectProperty()

    default_height = NumericProperty("48dp")
    key_height = StringProperty()
    viewclass = ObjectProperty()
    key_viewclass = StringProperty()

    # internals
    computed_height = NumericProperty(0)
    computed_heights = []
    computed_positions = []
    views = {}
    dirty_views = {}

    def on_viewclass(self, instance, value):
        if isinstance(value, string_types):
            self.viewclass = getattr(Factory, value)

    def do_layout(self, *args):
        super(RecycleView, self).do_layout(*args)
        self.refresh_from_data(True)

    def refresh_from_data(self, force=True):
        """The data has changed, update the RecycleView internals
        """
        if force:
            self.dirty_views.update(self.views)
        self.compute_views_heights()
        self.compute_visible_views()

    def compute_views_heights(self):
        """(internal) Calculate all the views height according to
        default_height, key_height, and then calculate their future positions
        """
        height = 0
        key_height = self.key_height
        default_height = self.default_height
        self.computed_heights = [
            item.get(key_height, default_height)
            for item in self.data
        ]
        self.computed_height = sum(self.computed_heights)
        self.computed_positions = list(
            self._compute_positions(self.computed_heights))

    def _compute_positions(self, heights):
        y = 0
        for height in heights:
            yield y
            y += height

    def compute_visible_views(self):
        """(internal) Determine the views that need to be showed in the current
        scrollview. All the hidden views will be flagged as dirty, and might
        be resued for others views.
        """
        # determine the view to create for the scrollview y / height
        sv = self.ids.sv
        layout = self.ids.layout
        scroll_y = 1 - (min(1, max(sv.scroll_y, 0)))
        px_start = (layout.height - self.height) * scroll_y
        px_end = px_start + self.height

        # now calculate the view indices we must show
        i_start = self.get_view_index_at(px_start)
        i_end = self.get_view_index_at(px_end)

        current_views = self.views
        visible_views = {}
        dirty_views = self.dirty_views

        # iterate though the visible view
        # add them into the layout if not already done
        for index in range(i_start, i_end + 1):
            view = self.get_view(index)
            if not view:
                continue

            visible_views[index] = view
            current_views.pop(index, None)

            # add to the layout if it's not already done
            if view.parent:
                continue
            layout.add_widget(view)

        # put all the hidden view as dirty views
        for index, view in current_views.items():
            layout.remove_widget(view)
            dirty_views[index] = view

        # save the current visible views
        self.views = visible_views

    def get_view(self, index):
        """Return a view instance for the `index`
        """
        if index in self.dirty_views:
            view = self.dirty_views.pop(index)
            self.refresh_view_layout(view, index)
            return view
        if index in self.views:
            return self.views[index]
        self.views[index] = view = self.create_view(index)
        self.refresh_view_layout(view, index)
        return view

    def refresh_view_layout(self, view, index):
        """(internal) Refresh the layout of a view. Size and pos are determine
        by the `RecycleView` according to the view `index` informations
        """
        view.size_hint = None, None
        view.width = self.width
        view.height = h = self.computed_heights[index]
        view.y = self.computed_height - self.computed_positions[index] - h

    def create_view(self, index):
        """Create the view for the `index`
        """
        viewclass = self.get_viewclass(index)
        item = self.data[index]
        return viewclass(**item)

    def get_view_position(self, index):
        """Get the position for the view at `index`
        """
        return self.computed_positions[index]

    def get_view_height(self, index):
        """Get the height for the view at `index`
        """
        return self.computed_heights[index]

    def get_viewclass(self, index):
        """Get the class needed to create the view `index`
        """
        viewclass = None
        if self.key_viewclass:
            viewclass = self.data[index].get(self.key_viewclass)
        if not viewclass:
            viewclass = self.viewclass
        return viewclass

    def get_view_index_at(self, y):
        """Return the view `index` for the `y` position
        """
        for index, pos in enumerate(self.computed_positions):
            if pos > y:
                return index - 1
        return index

    def on_data(self, instance, value):
        # data changed, right now, remove all the widgets.
        self.dirty_views = {}
        self.views = {}
        self.ids.layout.clear_widgets()
        self._trigger_layout()


if __name__ == "__main__":
    from kivy.base import runTouchApp
    from kivy.lang import Builder

    runTouchApp(Builder.load_string("""
RecycleView:
    data: [{"text": "Hello {}".format(x)} for x in range(100000)]
    viewclass: "Label"
    """))

    """
    from kivy.uix.label import Label
    rv = RecycleView()
    rv.viewclass = Label
    rv.key_height = "height"
    rv.data = [{
        "text": "Hello {}".format(x)}
        for x in range(10000)]
    runTouchApp(rv)
    """
