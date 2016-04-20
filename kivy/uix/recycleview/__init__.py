"""
RecycleView
===========

A flexible view for providing a limited window into a large data set.

.. warning::
    This module is highly experimental, its API may change in the future and
    the documentation is not complete at this time.


Data accepted: list of dict.

TODO:
    - Method to clear cached class instances.
    - Test when views cannot be found (e.g. viewclass is None).
    - Fix selection goto.


It is made with the MVC pattern. M for model is implemented by ....
V for views is split across layout and views and implemented by...
C for controller is implemented by RecycleViewBehavior.

These are abstract classes and cannot be used directly. The default concrete
implementation is RecycleDataModel for M, RecycleLayout and ... for views,
and RecycleView for C.

When a RecycleView is instantiated it automatically creates the views and data
classes. However, one must manually create the layout classes and add it to
the RecycleView.

A layout manager is automatically added as a layout manager when added as the
child of the RecycleView. Similarly when removed. A requirement is that the
layout manager must be a sub-child of the RecycleView so the view port can be
found.

.. warning::
    When views are re-used they may not trigger if the data remains the same.
"""

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
    """RecycleViewBehavior is a flexible view for providing a limited window into
    a large data set.

    See module documentation for more informations.
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
        '''Should be called when data changes. Data changes typically indicate
        that everything has to be recomputed since the source data changed.

        It is automatically bound to `'on_data_changed'` in
        :class:`~kivy.uix.recycleview.datamodel.RecycleDataModelBehavior` and
        therefore responds to and accept the keyword arguments of that event.

        It can be called manually to trigger an update.
        '''
        self._refresh_flags['data'].append(kwargs)
        self._refresh_trigger()

    def refresh_from_layout(self, *largs, **kwargs):
        '''Should be called when the layout changes or needs to change.
        Typically called when the data has not been changed, but e.g. a layout
        parameter has and therefore the layout needs to be recomputed.
        '''
        self._refresh_flags['layout'].append(kwargs)
        self._refresh_trigger()

    def refresh_from_viewport(self, *largs):
        '''Should be called when the viewport changes and the displayed data
        must be updated. Typically neither the data nor the layout will be
        recomputed.
        '''
        self._refresh_flags['viewport'] = True
        self._refresh_trigger()

    def _dispatch_prop_on_source(self, prop_name, *largs):
        '''Dispatches the prop of this class when the view_adapter/layout_manager
        property changes.
        '''
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
    """Data model responsible for keeping the data set. """

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
    """Adapter responsible for providing views that represent items in a data
    set."""

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
                'Expected object based on RecycleLayoutManagerBehavior, got {}'.
                format(value.__class__))

        self._layout_manager = value
        value.attach_recycleview(self)
        self.refresh_from_layout()
        return True

    layout_manager = AliasProperty(
        _get_layout_manager, _set_layout_manager)
    """Layout manager responsible to position views within the recycleview
    """


class RecycleView(RecycleViewBehavior, ScrollView):

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
    """Set the data on the current view adapter
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
    """Set the viewclass on the current layout_manager
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
    """Set the key viewclass on the current layout_manager
    """
