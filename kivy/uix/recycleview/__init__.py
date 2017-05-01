"""
RecycleView
===========

.. versionadded:: 1.10.0

The RecycleView provides a flexible model for viewing selected sections of
large data sets. It aims to prevent the performance degradation that can occur
when generating large numbers of widgets in order to display many data items.

The view is generatad by processing the :attr:`~RecycleView.data`, essentially
a list of dicts, and uses these dicts to generate instances of the
:attr:`~RecycleView.viewclass` as required. Its design is based on the
MVC (`Model-view-controller
<https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller>`_)
pattern.

* Model: The model is formed by :attr:`~RecycleView.data` you pass in via a
  list of dicts.
* View: The View is split across layout and views and implemented by...
* Controller: The controller is implemented by :class:`RecycleViewBehavior`.

These are abstract classes and cannot be used directly. The default concrete
implementation is the
:class:`~kivy.uix.recycleview.datamodel.RecycleDataModel` for the model, the
:class:`~kivy.uix.recyclelayout.RecycleLayout` and ... for view, and the
:class:`RecycleView` for the controller.

When a RecycleView is instantiated, it automatically creates the views and data
classes. However, one must manually create the layout classes and add them to
the RecycleView.

A layout manager is automatically created as a
:attr:`~RecycleViewBehavior.layout_manager` when added as the child of the
RecycleView. Similarly when removed. A requirement is that the layout manager
must be contained as a child somewhere within the RecycleView's widget tree so
the view port can be found.

A minimal example might look something like this::

    from kivy.app import App
    from kivy.lang import Builder
    from kivy.uix.recycleview import RecycleView


    Builder.load_string('''
    <RV>:
        viewclass: 'Label'
        RecycleBoxLayout:
            default_size: None, dp(56)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'
    ''')

    class RV(RecycleView):
        def __init__(self, **kwargs):
            super(RV, self).__init__(**kwargs)
            self.data = [{'text': str(x)} for x in range(100)]


    class TestApp(App):
        def build(self):
            return RV()

    if __name__ == '__main__':
        TestApp().run()

In order to support selection in the view, you can add the required behaviours
as follows::

    from kivy.app import App
    from kivy.lang import Builder
    from kivy.uix.recycleview import RecycleView
    from kivy.uix.recycleview.views import RecycleDataViewBehavior
    from kivy.uix.label import Label
    from kivy.properties import BooleanProperty
    from kivy.uix.recycleboxlayout import RecycleBoxLayout
    from kivy.uix.behaviors import FocusBehavior
    from kivy.uix.recycleview.layout import LayoutSelectionBehavior

    Builder.load_string('''
    <SelectableLabel>:
        # Draw a background to indicate selection
        canvas.before:
            Color:
                rgba: (.0, 0.9, .1, .3) if self.selected else (0, 0, 0, 1)
            Rectangle:
                pos: self.pos
                size: self.size
    <RV>:
        viewclass: 'SelectableLabel'
        SelectableRecycleBoxLayout:
            default_size: None, dp(56)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'
            multiselect: True
            touch_multiselect: True
    ''')


    class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,
                                     RecycleBoxLayout):
        ''' Adds selection and focus behaviour to the view. '''


    class SelectableLabel(RecycleDataViewBehavior, Label):
        ''' Add selection support to the Label '''
        index = None
        selected = BooleanProperty(False)
        selectable = BooleanProperty(True)

        def refresh_view_attrs(self, rv, index, data):
            ''' Catch and handle the view changes '''
            self.index = index
            return super(SelectableLabel, self).refresh_view_attrs(
                rv, index, data)

        def on_touch_down(self, touch):
            ''' Add selection on touch down '''
            if super(SelectableLabel, self).on_touch_down(touch):
                return True
            if self.collide_point(*touch.pos) and self.selectable:
                return self.parent.select_with_touch(self.index, touch)

        def apply_selection(self, rv, index, is_selected):
            ''' Respond to the selection of items in the view. '''
            self.selected = is_selected
            if is_selected:
                print("selection changed to {0}".format(rv.data[index]))
            else:
                print("selection removed for {0}".format(rv.data[index]))


    class RV(RecycleView):
        def __init__(self, **kwargs):
            super(RV, self).__init__(**kwargs)
            self.data = [{'text': str(x)} for x in range(100)]


    class TestApp(App):
        def build(self):
            return RV()

    if __name__ == '__main__':
        TestApp().run()



Please see the `examples/widgets/recycleview/basic_data.py` file for a more
complete example.

TODO:
    - Method to clear cached class instances.
    - Test when views cannot be found (e.g. viewclass is None).
    - Fix selection goto.

.. warning::
    When views are re-used they may not trigger if the data remains the same.
"""

__all__ = ('RecycleViewBehavior', 'RecycleView')

from copy import deepcopy

from kivy.uix.scrollview import ScrollView
from kivy.properties import AliasProperty
from kivy.clock import Clock

from kivy.uix.recycleview.layout import RecycleLayoutManagerBehavior, \
    LayoutChangeException
from kivy.uix.recycleview.views import RecycleDataAdapter
from kivy.uix.recycleview.datamodel import RecycleDataModelBehavior, \
    RecycleDataModel


class RecycleViewBehavior(object):
    """RecycleViewBehavior provides a behavioral model upon which the
    :class:`RecycleView` is built. Together, they offer an extensible and
    flexible way to produce views with limited windows over large data sets.

    See the module documentation for more information.
    """

    # internals
    _view_adapter = None
    _data_model = None
    _layout_manager = None

    _refresh_flags = {'data': [], 'layout': [], 'viewport': False}
    _refresh_trigger = None

    def __init__(self, **kwargs):
        self._refresh_trigger = Clock.create_trigger(self.refresh_views, -1)
        self._refresh_flags = deepcopy(self._refresh_flags)
        super(RecycleViewBehavior, self).__init__(**kwargs)

    def get_viewport(self):
        pass

    def save_viewport(self):
        pass

    def restore_viewport(self):
        pass

    def refresh_views(self, *largs):
        lm = self.layout_manager
        flags = self._refresh_flags
        if lm is None or self.view_adapter is None or self.data_model is None:
            return

        data = self.data
        f = flags['data']
        if f:
            self.save_viewport()
            # lm.clear_layout()
            flags['data'] = []
            flags['layout'] = [{}]
            lm.compute_sizes_from_data(data, f)

        while flags['layout']:
            # if `data` we were re-triggered so finish in the next call.
            # Otherwise go until fully laid out.
            self.save_viewport()
            if flags['data']:
                return
            flags['viewport'] = True
            f = flags['layout']
            flags['layout'] = []

            try:
                lm.compute_layout(data, f)
            except LayoutChangeException:
                flags['layout'].append({})
                continue

        if flags['data']:  # in case that happened meanwhile
            return

        # make sure if we were re-triggered in the loop that we won't be
        # called needlessly later.
        self._refresh_trigger.cancel()

        self.restore_viewport()

        if flags['viewport']:
            # TODO: make this also listen to LayoutChangeException
            flags['viewport'] = False
            viewport = self.get_viewport()
            indices = lm.compute_visible_views(data, viewport)
            lm.set_visible_views(indices, data, viewport)

    def refresh_from_data(self, *largs, **kwargs):
        """
        This should be called when data changes. Data changes typically
        indicate that everything should be recomputed since the source data
        changed.

        This method is automatically bound to the
        :attr:`~RecycleDataModelBehavior.on_data_changed` method of the
        :class:`~RecycleDataModelBehavior` class and
        therefore responds to and accepts the keyword arguments of that event.

        It can be called manually to trigger an update.
        """
        self._refresh_flags['data'].append(kwargs)
        self._refresh_trigger()

    def refresh_from_layout(self, *largs, **kwargs):
        """
        This should be called when the layout changes or needs to change. It is
        typically called when a layout parameter has changed and therefore the
        layout needs to be recomputed.
        """
        self._refresh_flags['layout'].append(kwargs)
        self._refresh_trigger()

    def refresh_from_viewport(self, *largs):
        """
        This should be called when the viewport changes and the displayed data
        must be updated. Neither the data nor the layout will be recomputed.
        """
        self._refresh_flags['viewport'] = True
        self._refresh_trigger()

    def _dispatch_prop_on_source(self, prop_name, *largs):
        # Dispatches the prop of this class when the
        # view_adapter/layout_manager property changes.
        getattr(self.__class__, prop_name).dispatch(self)

    def _get_data_model(self):
        return self._data_model

    def _set_data_model(self, value):
        data_model = self._data_model
        if value is data_model:
            return
        if data_model is not None:
            self._data_model = None
            data_model.detach_recycleview()

        if value is None:
            return True

        if not isinstance(value, RecycleDataModelBehavior):
            raise ValueError(
                'Expected object based on RecycleDataModelBehavior, got {}'.
                format(value.__class__))

        self._data_model = value
        value.attach_recycleview(self)
        self.refresh_from_data()
        return True

    data_model = AliasProperty(_get_data_model, _set_data_model)
    """
    The Data model responsible for maintaining the data set.

    data_model is an :class:`~kivy.properties.AliasProperty` that gets and sets
    the current data model.
    """

    def _get_view_adapter(self):
        return self._view_adapter

    def _set_view_adapter(self, value):
        view_adapter = self._view_adapter
        if value is view_adapter:
            return
        if view_adapter is not None:
            self._view_adapter = None
            view_adapter.detach_recycleview()

        if value is None:
            return True

        if not isinstance(value, RecycleDataAdapter):
            raise ValueError(
                'Expected object based on RecycleAdapter, got {}'.
                format(value.__class__))

        self._view_adapter = value
        value.attach_recycleview(self)
        self.refresh_from_layout()
        return True

    view_adapter = AliasProperty(_get_view_adapter, _set_view_adapter)
    """
    The adapter responsible for providing views that represent items in a data
    set.

    view_adapter is an :class:`~kivy.properties.AliasProperty` that gets and
    sets the current view adapter.
    """

    def _get_layout_manager(self):
        return self._layout_manager

    def _set_layout_manager(self, value):
        lm = self._layout_manager
        if value is lm:
            return

        if lm is not None:
            self._layout_manager = None
            lm.detach_recycleview()

        if value is None:
            return True

        if not isinstance(value, RecycleLayoutManagerBehavior):
            raise ValueError(
                'Expected object based on RecycleLayoutManagerBehavior, '
                'got {}'.format(value.__class__))

        self._layout_manager = value
        value.attach_recycleview(self)
        self.refresh_from_layout()
        return True

    layout_manager = AliasProperty(
        _get_layout_manager, _set_layout_manager)
    """
    The Layout manager responsible for positioning views within the
    :class:`RecycleView`.

    layout_manager is an :class:`~kivy.uix.properties.AliasProperty` that gets
    and sets the layout_manger.
    """


class RecycleView(RecycleViewBehavior, ScrollView):
    """
    RecycleView is a flexible view for providing a limited window
    into a large data set.

    See the module documentation for more information.
    """
    def __init__(self, **kwargs):
        if self.data_model is None:
            kwargs.setdefault('data_model', RecycleDataModel())
        if self.view_adapter is None:
            kwargs.setdefault('view_adapter', RecycleDataAdapter())
        super(RecycleView, self).__init__(**kwargs)

        fbind = self.fbind
        fbind('scroll_x', self.refresh_from_viewport)
        fbind('scroll_y', self.refresh_from_viewport)
        fbind('size', self.refresh_from_viewport)
        self.refresh_from_data()

    def _convert_sv_to_lm(self, x, y):
        lm = self.layout_manager
        tree = [lm]
        parent = lm.parent
        while parent is not None and parent is not self:
            tree.append(parent)
            parent = parent.parent

        if parent is not self:
            raise Exception(
                'The layout manager must be a sub child of the recycleview. '
                'Could not find {} in the parent tree of {}'.format(self, lm))

        for widget in reversed(tree):
            x, y = widget.to_local(x, y)

        return x, y

    def get_viewport(self):
        lm = self.layout_manager
        lm_w, lm_h = lm.size
        w, h = self.size
        scroll_y = min(1, max(self.scroll_y, 0))
        scroll_x = min(1, max(self.scroll_x, 0))

        if lm_h <= h:
            bottom = 0
        else:
            above = (lm_h - h) * scroll_y
            bottom = max(0, lm_h - above - h)

        bottom = max(0, (lm_h - h) * scroll_y)
        left = max(0, (lm_w - w) * scroll_x)
        width = min(w, lm_w)
        height = min(h, lm_h)

        # now convert the sv coordinates into the coordinates of the lm. In
        # case there's a relative layout type widget in the parent tree
        # between the sv and the lm.
        left, bottom = self._convert_sv_to_lm(left, bottom)
        return left, bottom, width, height

    def save_viewport(self):
        pass

    def restore_viewport(self):
        pass

    def add_widget(self, widget, *largs):
        super(RecycleView, self).add_widget(widget, *largs)
        if (isinstance(widget, RecycleLayoutManagerBehavior) and
                not self.layout_manager):
            self.layout_manager = widget

    def remove_widget(self, widget, *largs):
        super(RecycleView, self).remove_widget(widget, *largs)
        if self.layout_manager == widget:
            self.layout_manager = None

    # or easier way to use
    def _get_data(self):
        d = self.data_model
        return d and d.data

    def _set_data(self, value):
        d = self.data_model
        if d is not None:
            d.data = value

    data = AliasProperty(_get_data, _set_data, bind=["data_model"])
    """
    The data used by the current view adapter. This is a list of dicts whose
    keys map to the corresponding property names of the
    :attr:`~RecycleView.viewclass`.

    data is an :class:`~kivy.properties.AliasProperty` that gets and sets the
    data used to generate the views.
    """

    def _get_viewclass(self):
        a = self.layout_manager
        return a and a.viewclass

    def _set_viewclass(self, value):
        a = self.layout_manager
        if a:
            a.viewclass = value

    viewclass = AliasProperty(_get_viewclass, _set_viewclass,
                              bind=["layout_manager"])
    """
    The viewclass used by the current layout_manager.

    viewclass is an :class:`~kivy.properties.AliasProperty` that gets and sets
    the class used to generate the individual items presented in the view.
    """

    def _get_key_viewclass(self):
        a = self.layout_manager
        return a and a.key_viewclass

    def _set_key_viewclass(self, value):
        a = self.layout_manager
        if a:
            a.key_viewclass = value

    key_viewclass = AliasProperty(_get_key_viewclass, _set_key_viewclass,
        bind=["layout_manager"])
    """
    key_viewclass is an :class:`~kivy.properties.AliasProperty` that gets and
    sets the key viewclass for the current
    :attr:`~kivy.uix.recycleview.layout_manager`.
    """
