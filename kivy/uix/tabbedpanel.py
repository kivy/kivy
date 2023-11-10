'''
TabbedPanel
===========

.. image:: images/tabbed_panel.jpg
    :align: right

.. versionadded:: 1.3.0


The `TabbedPanel` widget manages different widgets in tabs, with a header area
for the actual tab buttons and a content area for showing the current tab
content.

The :class:`TabbedPanel` provides one default tab.

Simple example
--------------

.. include:: ../../examples/widgets/tabbedpanel.py
    :literal:

.. note::

    A new class :class:`TabbedPanelItem` has been introduced in 1.5.0 for
    convenience. So now one can simply add a :class:`TabbedPanelItem` to a
    :class:`TabbedPanel` and `content` to the :class:`TabbedPanelItem`
    as in the example provided above.

Customize the Tabbed Panel
--------------------------

You can choose the position in which the tabs are displayed::

    tab_pos = 'top_mid'

An individual tab is called a TabbedPanelHeader. It is a special button
containing a `content` property. You add the TabbedPanelHeader first, and set
its `content` property separately::

    tp = TabbedPanel()
    th = TabbedPanelHeader(text='Tab2')
    tp.add_widget(th)

An individual tab, represented by a TabbedPanelHeader, needs its content set.
This content can be any widget. It could be a layout with a deep
hierarchy of widgets, or it could be an individual widget, such as a label or a
button::

    th.content = your_content_instance

There is one "shared" main content area active at any given time, for all
the tabs. Your app is responsible for adding the content of individual tabs
and for managing them, but it's not responsible for content switching. The
tabbed panel handles switching of the main content object as per user action.

There is a default tab added when the tabbed panel is instantiated.
Tabs that you add individually as above, are added in addition to the default
tab. Thus, depending on your needs and design, you will want to customize the
default tab::

    tp.default_tab_text = 'Something Specific To Your Use'


The default tab machinery requires special consideration and management.
Accordingly, an `on_default_tab` event is provided for associating a callback::

    tp.bind(default_tab = my_default_tab_callback)

It's important to note that by default, :attr:`default_tab_cls` is of type
:class:`TabbedPanelHeader` and thus has the same properties as other tabs.

Since 1.5.0, it is now possible to disable the creation of the
:attr:`default_tab` by setting :attr:`do_default_tab` to False.

Tabs and content can be removed in several ways::

    tp.remove_widget(widget/tabbed_panel_header)
    or
    tp.clear_widgets() # to clear all the widgets in the content area
    or
    tp.clear_tabs() # to remove the TabbedPanelHeaders

To access the children of the tabbed panel, use content.children::

    tp.content.children

To access the list of tabs::

    tp.tab_list

To change the appearance of the main tabbed panel content::

    background_color = (1, 0, 0, .5) #50% translucent red
    border = [0, 0, 0, 0]
    background_image = 'path/to/background/image'

To change the background of a individual tab, use these two properties::

    tab_header_instance.background_normal = 'path/to/tab_head/img'
    tab_header_instance.background_down = 'path/to/tab_head/img_pressed'

A TabbedPanelStrip contains the individual tab headers. To change the
appearance of this tab strip, override the canvas of TabbedPanelStrip.
For example, in the kv language:

.. code-block:: kv

    <TabbedPanelStrip>
        canvas:
            Color:
                rgba: (0, 1, 0, 1) # green
            Rectangle:
                size: self.size
                pos: self.pos

By default the tabbed panel strip takes its background image and color from the
tabbed panel's background_image and background_color.

'''

__all__ = ('StripLayout', 'TabbedPanel', 'TabbedPanelContent',
           'TabbedPanelHeader', 'TabbedPanelItem', 'TabbedPanelStrip',
           'TabbedPanelException')

from functools import partial
from kivy.clock import Clock
from kivy.compat import string_types
from kivy.factory import Factory
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty, OptionProperty, \
    ListProperty, NumericProperty, AliasProperty, BooleanProperty, \
    ColorProperty


class TabbedPanelException(Exception):
    '''The TabbedPanelException class.
    '''
    pass


class TabbedPanelHeader(ToggleButton):
    '''A Base for implementing a Tabbed Panel Head. A button intended to be
    used as a Heading/Tab for a TabbedPanel widget.

    You can use this TabbedPanelHeader widget to add a new tab to a
    TabbedPanel.
    '''

    content = ObjectProperty(None, allownone=True)
    '''Content to be loaded when this tab header is selected.

    :attr:`content` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    # only allow selecting the tab if not already selected
    def on_touch_down(self, touch):
        if self.state == 'down':
            # dispatch to children, not to self
            for child in self.children:
                child.dispatch('on_touch_down', touch)
            return
        else:
            super(TabbedPanelHeader, self).on_touch_down(touch)

    def on_release(self, *largs):
        # Tabbed panel header is a child of tab_strib which has a
        # `tabbed_panel` property
        if self.parent:
            self.parent.tabbed_panel.switch_to(self)
        else:
            # tab removed before we could switch to it. Switch back to
            # previous tab
            self.panel.switch_to(self.panel.current_tab)


class TabbedPanelItem(TabbedPanelHeader):
    '''This is a convenience class that provides a header of type
    TabbedPanelHeader and links it with the content automatically. Thus
    facilitating you to simply do the following in kv language:

    .. code-block:: kv

        <TabbedPanel>:
            # ...other settings
            TabbedPanelItem:
                BoxLayout:
                    Label:
                        text: 'Second tab content area'
                    Button:
                        text: 'Button that does nothing'

    .. versionadded:: 1.5.0
    '''

    def add_widget(self, widget, *args, **kwargs):
        self.content = widget
        if not self.parent:
            return
        panel = self.parent.tabbed_panel
        if panel.current_tab == self:
            panel.switch_to(self)

    def remove_widget(self, *args, **kwargs):
        self.content = None
        if not self.parent:
            return
        panel = self.parent.tabbed_panel
        if panel.current_tab == self:
            panel.remove_widget(*args, **kwargs)


class TabbedPanelStrip(GridLayout):
    '''A strip intended to be used as background for Heading/Tab.
    This does not cover the blank areas in case the tabs don't cover
    the entire width/height of the TabbedPanel(use :class:`StripLayout`
    for that).
    '''
    tabbed_panel = ObjectProperty(None)
    '''Link to the panel that the tab strip is a part of.

    :attr:`tabbed_panel` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None .
    '''


class StripLayout(GridLayout):
    ''' The main layout that is used to house the entire tabbedpanel strip
    including the blank areas in case the tabs don't cover the entire
    width/height.

    .. versionadded:: 1.8.0

    '''

    border = ListProperty([4, 4, 4, 4])
    '''Border property for the :attr:`background_image`.

    :attr:`border` is a :class:`~kivy.properties.ListProperty` and defaults
    to [4, 4, 4, 4]
    '''

    background_image = StringProperty(
        'atlas://data/images/defaulttheme/action_view')
    '''Background image to be used for the Strip layout of the TabbedPanel.

    :attr:`background_image` is a :class:`~kivy.properties.StringProperty` and
    defaults to a transparent image.
    '''


class TabbedPanelContent(FloatLayout):
    '''The TabbedPanelContent class.
    '''
    pass


class TabbedPanel(GridLayout):
    '''The TabbedPanel class. See module documentation for more information.
    '''

    background_color = ColorProperty([1, 1, 1, 1])
    '''Background color, in the format (r, g, b, a).

    :attr:`background_color` is a :class:`~kivy.properties.ColorProperty` and
    defaults to [1, 1, 1, 1].

    .. versionchanged:: 2.0.0
        Changed from :class:`~kivy.properties.ListProperty` to
        :class:`~kivy.properties.ColorProperty`.
    '''

    border = ListProperty([16, 16, 16, 16])
    '''Border used for :class:`~kivy.graphics.vertex_instructions.BorderImage`
    graphics instruction, used itself for :attr:`background_image`.
    Can be changed for a custom background.

    It must be a list of four values: (bottom, right, top, left). Read the
    BorderImage instructions for more information.

    :attr:`border` is a :class:`~kivy.properties.ListProperty` and
    defaults to (16, 16, 16, 16)
    '''

    background_image = StringProperty('atlas://data/images/defaulttheme/tab')
    '''Background image of the main shared content object.

    :attr:`background_image` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/tab'.
    '''

    background_disabled_image = StringProperty(
        'atlas://data/images/defaulttheme/tab_disabled')
    '''Background image of the main shared content object when disabled.

    .. versionadded:: 1.8.0

    :attr:`background_disabled_image` is a
    :class:`~kivy.properties.StringProperty` and defaults to
    'atlas://data/images/defaulttheme/tab'.
    '''

    strip_image = StringProperty(
        'atlas://data/images/defaulttheme/action_view')
    '''Background image of the tabbed strip.

    .. versionadded:: 1.8.0

    :attr:`strip_image` is a :class:`~kivy.properties.StringProperty`
    and defaults to a empty image.
    '''

    strip_border = ListProperty([4, 4, 4, 4])
    '''Border to be used on :attr:`strip_image`.

    .. versionadded:: 1.8.0

    :attr:`strip_border` is a :class:`~kivy.properties.ListProperty` and
    defaults to [4, 4, 4, 4].
    '''

    _current_tab = ObjectProperty(None)

    def get_current_tab(self):
        return self._current_tab

    current_tab = AliasProperty(get_current_tab, None, bind=('_current_tab', ))
    '''Links to the currently selected or active tab.

    .. versionadded:: 1.4.0

    :attr:`current_tab` is an :class:`~kivy.AliasProperty`, read-only.
    '''

    tab_pos = OptionProperty(
        'top_left',
        options=('left_top', 'left_mid', 'left_bottom', 'top_left',
                 'top_mid', 'top_right', 'right_top', 'right_mid',
                 'right_bottom', 'bottom_left', 'bottom_mid', 'bottom_right'))
    '''Specifies the position of the tabs relative to the content.
    Can be one of: `left_top`, `left_mid`, `left_bottom`, `top_left`,
    `top_mid`, `top_right`, `right_top`, `right_mid`, `right_bottom`,
    `bottom_left`, `bottom_mid`, `bottom_right`.

    :attr:`tab_pos` is an :class:`~kivy.properties.OptionProperty` and
    defaults to 'top_left'.
    '''

    tab_height = NumericProperty('40dp')
    '''Specifies the height of the tab header.

    :attr:`tab_height` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 40.
    '''

    tab_width = NumericProperty('100dp', allownone=True)
    '''Specifies the width of the tab header.

    :attr:`tab_width` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 100.
    '''

    bar_width = NumericProperty('2dp')
    '''Width of the horizontal scroll bar. The width is interpreted
    as a height for the horizontal bar.

    .. versionadded:: 2.2.0

    :attr:`bar_width` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 2.
    '''

    scroll_type = OptionProperty(['content'], options=(['content'], ['bars'],
                                 ['bars', 'content'], ['content', 'bars']))

    '''Sets the type of scrolling to use for the content of the scrollview.
    Available options are: ['content'], ['bars'], ['bars', 'content'].

    .. versionadded:: 2.2.0

    :attr:`scroll_type` is an :class:`~kivy.properties.OptionProperty` and
    defaults to ['content'].
    '''

    do_default_tab = BooleanProperty(True)
    '''Specifies whether a default_tab head is provided.

    .. versionadded:: 1.5.0

    :attr:`do_default_tab` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to 'True'.
    '''

    default_tab_text = StringProperty('Default tab')
    '''Specifies the text displayed on the default tab header.

    :attr:`default_tab_text` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'default tab'.
    '''

    default_tab_cls = ObjectProperty(TabbedPanelHeader)
    '''Specifies the class to use for the styling of the default tab.

    .. versionadded:: 1.4.0

    .. warning::
        `default_tab_cls` should be subclassed from `TabbedPanelHeader`

    :attr:`default_tab_cls` is an :class:`~kivy.properties.ObjectProperty`
    and defaults to `TabbedPanelHeader`. If you set a string, the
    :class:`~kivy.factory.Factory` will be used to resolve the class.

    .. versionchanged:: 1.8.0
        The :class:`~kivy.factory.Factory` will resolve the class if a string
        is set.
    '''

    def get_tab_list(self):
        if self._tab_strip:
            return self._tab_strip.children
        return 1.

    tab_list = AliasProperty(get_tab_list, None)
    '''List of all the tab headers.

    :attr:`tab_list` is an :class:`~kivy.properties.AliasProperty` and is
    read-only.
    '''

    content = ObjectProperty(None)
    '''This is the object holding (current_tab's content is added to this)
    the content of the current tab. To Listen to the changes in the content
    of the current tab, you should bind to current_tabs `content` property.

    :attr:`content` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to 'None'.
    '''

    _default_tab = ObjectProperty(None, allow_none=True)

    def get_def_tab(self):
        return self._default_tab

    def set_def_tab(self, new_tab):
        if not issubclass(new_tab.__class__, TabbedPanelHeader):
            raise TabbedPanelException('`default_tab_class` should be\
                subclassed from `TabbedPanelHeader`')
        if self._default_tab == new_tab:
            return
        oltab = self._default_tab
        self._default_tab = new_tab
        self.remove_widget(oltab)
        self._original_tab = None
        self.switch_to(new_tab)
        new_tab.state = 'down'

    default_tab = AliasProperty(get_def_tab, set_def_tab,
                                bind=('_default_tab', ))
    '''Holds the default tab.

    .. Note:: For convenience, the automatically provided default tab is
              deleted when you change default_tab to something else.
              As of 1.5.0, this behavior has been extended to every
              `default_tab` for consistency and not just the automatically
              provided one.

    :attr:`default_tab` is an :class:`~kivy.properties.AliasProperty`.
    '''

    def get_def_tab_content(self):
        return self.default_tab.content

    def set_def_tab_content(self, *l):
        self.default_tab.content = l[0]

    default_tab_content = AliasProperty(get_def_tab_content,
                                        set_def_tab_content)
    '''Holds the default tab content.

    :attr:`default_tab_content` is an :class:`~kivy.properties.AliasProperty`.
    '''

    _update_top_ev = _update_tab_ev = _update_tabs_ev = None

    def __init__(self, **kwargs):
        # these variables need to be initialized before the kv lang is
        # processed setup the base layout for the tabbed panel
        self._childrens = []
        self._tab_layout = StripLayout(rows=1)
        self.rows = 1
        self._tab_strip = TabbedPanelStrip(
            tabbed_panel=self,
            rows=1, size_hint=(None, None),
            height=self.tab_height, width=self.tab_width)

        self._partial_update_scrollview = None
        self.content = TabbedPanelContent()
        self._current_tab = self._original_tab \
            = self._default_tab = TabbedPanelHeader()

        super(TabbedPanel, self).__init__(**kwargs)

        self.fbind('size', self._reposition_tabs)
        if not self.do_default_tab:
            Clock.schedule_once(self._switch_to_first_tab)
            return
        self._setup_default_tab()
        self.switch_to(self.default_tab)

    def switch_to(self, header, do_scroll=False):
        '''Switch to a specific panel header.

        .. versionchanged:: 1.10.0

        If used with `do_scroll=True`, it scrolls
        to the header's tab too.

        :meth:`switch_to` cannot be called from within the
        :class:`TabbedPanel` or its subclass' ``__init__`` method.
        If that is required, use the ``Clock`` to schedule it. See `discussion
        <https://github.com/kivy/kivy/issues/3493#issuecomment-121567969>`_
        for full example.
        '''
        header_content = header.content
        self._current_tab.state = 'normal'
        header.state = 'down'
        self._current_tab = header
        self.clear_widgets()
        if header_content is None:
            return
        # if content has a previous parent remove it from that parent
        parent = header_content.parent
        if parent:
            parent.remove_widget(header_content)
        self.add_widget(header_content)

        if do_scroll:
            tabs = self._tab_strip
            tabs.parent.scroll_to(header)

    def clear_tabs(self, *l):
        self_tabs = self._tab_strip
        self_tabs.clear_widgets()
        if self.do_default_tab:
            self_default_tab = self._default_tab
            self_tabs.add_widget(self_default_tab)
            self_tabs.width = self_default_tab.width
        self._reposition_tabs()

    def add_widget(self, widget, *args, **kwargs):
        content = self.content
        if content is None:
            return
        parent = widget.parent
        if parent:
            parent.remove_widget(widget)
        if widget in (content, self._tab_layout):
            super(TabbedPanel, self).add_widget(widget, *args, **kwargs)
        elif isinstance(widget, TabbedPanelHeader):
            self_tabs = self._tab_strip
            self_tabs.add_widget(widget, *args, **kwargs)
            widget.group = '__tab%r__' % self_tabs.uid
            self.on_tab_width()
        else:
            widget.pos_hint = {'x': 0, 'top': 1}
            self._childrens.append(widget)
            content.disabled = self.current_tab.disabled
            content.add_widget(widget, *args, **kwargs)

    def remove_widget(self, widget, *args, **kwargs):
        content = self.content
        if content is None:
            return
        if widget in (content, self._tab_layout):
            super(TabbedPanel, self).remove_widget(widget, *args, **kwargs)
        elif isinstance(widget, TabbedPanelHeader):
            if not (self.do_default_tab and widget is self._default_tab):
                self_tabs = self._tab_strip
                self_tabs.width -= widget.width
                self_tabs.remove_widget(widget)
                if widget.state == 'down' and self.do_default_tab:
                    self._default_tab.on_release()
                self._reposition_tabs()
            else:
                Logger.info('TabbedPanel: default tab! can\'t be removed.\n' +
                            'Change `default_tab` to a different tab.')
        else:
            if widget in self._childrens:
                self._childrens.remove(widget)
            if widget in content.children:
                content.remove_widget(widget, *args, **kwargs)

    def clear_widgets(self, *args, **kwargs):
        if self.content:
            self.content.clear_widgets(*args, **kwargs)

    def on_strip_image(self, instance, value):
        if not self._tab_layout:
            return
        self._tab_layout.background_image = value

    def on_strip_border(self, instance, value):
        if not self._tab_layout:
            return
        self._tab_layout.border = value

    def on_do_default_tab(self, instance, value):
        if not value:
            dft = self.default_tab
            if dft in self.tab_list:
                self.remove_widget(dft)
                self._switch_to_first_tab()
                self._default_tab = self._current_tab
        else:
            self._current_tab.state = 'normal'
            self._setup_default_tab()

    def on_default_tab_text(self, *args):
        self._default_tab.text = self.default_tab_text

    def on_tab_width(self, *l):
        ev = self._update_tab_ev
        if ev is None:
            ev = self._update_tab_ev = Clock.create_trigger(
                self._update_tab_width, 0)
        ev()

    def on_tab_height(self, *l):
        self._tab_layout.height = self._tab_strip.height = self.tab_height
        self._reposition_tabs()

    def on_tab_pos(self, *l):
        # ensure canvas
        self._reposition_tabs()

    def _setup_default_tab(self):
        if self._default_tab in self.tab_list:
            return
        content = self._default_tab.content
        _tabs = self._tab_strip
        cls = self.default_tab_cls

        if isinstance(cls, string_types):
            cls = Factory.get(cls)

        if not issubclass(cls, TabbedPanelHeader):
            raise TabbedPanelException('`default_tab_class` should be\
                subclassed from `TabbedPanelHeader`')

        # no need to instantiate if class is TabbedPanelHeader
        if cls != TabbedPanelHeader:
            self._current_tab = self._original_tab = self._default_tab = cls()

        default_tab = self.default_tab
        if self._original_tab == self.default_tab:
            default_tab.text = self.default_tab_text

        default_tab.height = self.tab_height
        default_tab.group = '__tab%r__' % _tabs.uid
        default_tab.state = 'down'
        default_tab.width = self.tab_width if self.tab_width else 100
        default_tab.content = content

        tl = self.tab_list
        if default_tab not in tl:
            _tabs.add_widget(default_tab, len(tl))

        if default_tab.content:
            self.clear_widgets()
            self.add_widget(self.default_tab.content)
        else:
            Clock.schedule_once(self._load_default_tab_content)
        self._current_tab = default_tab

    def _switch_to_first_tab(self, *l):
        ltl = len(self.tab_list) - 1
        if ltl > -1:
            self._current_tab = dt = self._original_tab \
                = self.tab_list[ltl]
            self.switch_to(dt)

    def _load_default_tab_content(self, dt):
        if self.default_tab:
            self.switch_to(self.default_tab)

    def _reposition_tabs(self, *l):
        ev = self._update_tabs_ev
        if ev is None:
            ev = self._update_tabs_ev = Clock.create_trigger(
                self._update_tabs, 0)
        ev()

    def _update_tabs(self, *l):
        self_content = self.content
        if not self_content:
            return
        # cache variables for faster access
        tab_pos = self.tab_pos
        tab_layout = self._tab_layout
        tab_layout.clear_widgets()
        scrl_v = ScrollView(size_hint=(None, 1), always_overscroll=False,
                            bar_width=self.bar_width,
                            scroll_type=self.scroll_type)
        tabs = self._tab_strip
        parent = tabs.parent
        if parent:
            parent.remove_widget(tabs)
        scrl_v.add_widget(tabs)
        scrl_v.pos = (0, 0)
        self_update_scrollview = self._update_scrollview

        # update scrlv width when tab width changes depends on tab_pos
        if self._partial_update_scrollview is not None:
            tabs.unbind(width=self._partial_update_scrollview)
        self._partial_update_scrollview = partial(
            self_update_scrollview, scrl_v)
        tabs.bind(width=self._partial_update_scrollview)

        # remove all widgets from the tab_strip
        super(TabbedPanel, self).clear_widgets()
        tab_height = self.tab_height

        widget_list = []
        tab_list = []
        pos_letter = tab_pos[0]
        if pos_letter == 'b' or pos_letter == 't':
            # bottom or top positions
            # one col containing the tab_strip and the content
            self.cols = 1
            self.rows = 2
            # tab_layout contains the scrollview containing tabs and two blank
            # dummy widgets for spacing
            tab_layout.rows = 1
            tab_layout.cols = 3
            tab_layout.size_hint = (1, None)
            tab_layout.height = (tab_height + tab_layout.padding[1] +
                                 tab_layout.padding[3] + dp(2))
            self_update_scrollview(scrl_v)

            if pos_letter == 'b':
                # bottom
                if tab_pos == 'bottom_mid':
                    tab_list = (Widget(), scrl_v, Widget())
                    widget_list = (self_content, tab_layout)
                else:
                    if tab_pos == 'bottom_left':
                        tab_list = (scrl_v, Widget(), Widget())
                    elif tab_pos == 'bottom_right':
                        # add two dummy widgets
                        tab_list = (Widget(), Widget(), scrl_v)
                    widget_list = (self_content, tab_layout)
            else:
                # top
                if tab_pos == 'top_mid':
                    tab_list = (Widget(), scrl_v, Widget())
                elif tab_pos == 'top_left':
                    tab_list = (scrl_v, Widget(), Widget())
                elif tab_pos == 'top_right':
                    tab_list = (Widget(), Widget(), scrl_v)
                widget_list = (tab_layout, self_content)
        elif pos_letter == 'l' or pos_letter == 'r':
            # left or right positions
            # one row containing the tab_strip and the content
            self.cols = 2
            self.rows = 1
            # tab_layout contains two blank dummy widgets for spacing
            # "vertically" and the scatter containing scrollview
            # containing tabs
            tab_layout.rows = 3
            tab_layout.cols = 1
            tab_layout.size_hint = (None, 1)
            tab_layout.width = tab_height
            scrl_v.height = tab_height
            self_update_scrollview(scrl_v)

            # rotate the scatter for vertical positions
            rotation = 90 if tab_pos[0] == 'l' else -90
            sctr = Scatter(do_translation=False,
                           rotation=rotation,
                           do_rotation=False,
                           do_scale=False,
                           size_hint=(None, None),
                           auto_bring_to_front=False,
                           size=scrl_v.size)
            sctr.add_widget(scrl_v)

            lentab_pos = len(tab_pos)

            # Update scatter's top when its pos changes.
            # Needed for repositioning scatter to the correct place after its
            # added to the parent. Use clock_schedule_once to ensure top is
            # calculated after the parent's pos on canvas has been calculated.
            # This is needed for when tab_pos changes to correctly position
            # scatter. Without clock.schedule_once the positions would look
            # fine but touch won't translate to the correct position

            if tab_pos[lentab_pos - 4:] == '_top':
                # on positions 'left_top' and 'right_top'
                sctr.bind(pos=partial(self._update_top, sctr, 'top', None))
                tab_list = (sctr, )
            elif tab_pos[lentab_pos - 4:] == '_mid':
                # calculate top of scatter
                sctr.bind(pos=partial(self._update_top, sctr, 'mid',
                                      scrl_v.width))
                tab_list = (Widget(), sctr, Widget())
            elif tab_pos[lentab_pos - 7:] == '_bottom':
                tab_list = (Widget(), Widget(), sctr)

            if pos_letter == 'l':
                widget_list = (tab_layout, self_content)
            else:
                widget_list = (self_content, tab_layout)

        # add widgets to tab_layout
        add = tab_layout.add_widget
        for widg in tab_list:
            add(widg)

        # add widgets to self
        add = self.add_widget
        for widg in widget_list:
            add(widg)

    def _update_tab_width(self, *l):
        if self.tab_width:
            for tab in self.tab_list:
                tab.size_hint_x = 1
            tsw = self.tab_width * len(self._tab_strip.children)
        else:
            # tab_width = None
            tsw = 0
            for tab in self.tab_list:
                if tab.size_hint_x:
                    # size_hint_x: x/.xyz
                    tab.size_hint_x = 1
                    # drop to default tab_width
                    tsw += 100
                else:
                    # size_hint_x: None
                    tsw += tab.width
        self._tab_strip.width = tsw
        self._reposition_tabs()

    def _update_top(self, *args):
        sctr, top, scrl_v_width, x, y = args
        ev = self._update_top_ev
        if ev is not None:
            ev.cancel()

        ev = self._update_top_ev = Clock.schedule_once(
            partial(self._updt_top, sctr, top, scrl_v_width), 0)

    def _updt_top(self, sctr, top, scrl_v_width, *args):
        if top[0] == 't':
            sctr.top = self.top
        else:
            sctr.top = self.top - (self.height - scrl_v_width) / 2

    def _update_scrollview(self, scrl_v, *l):
        self_tab_pos = self.tab_pos
        self_tabs = self._tab_strip
        if self_tab_pos[0] == 'b' or self_tab_pos[0] == 't':
            # bottom or top
            scrl_v.width = min(self.width, self_tabs.width)
            # required for situations when scrl_v's pos is calculated
            # when it has no parent
            scrl_v.top += 1
            scrl_v.top -= 1
        else:
            # left or right
            scrl_v.width = min(self.height, self_tabs.width)
            self_tabs.pos = (0, 0)
