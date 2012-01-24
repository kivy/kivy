'''
TabbedPannel
============

.. versionadded:: 1.0.1?

.. image:: images/tabbed_pannel.jpg
    :align: right

The `TabbedPannel` widget is exactly what it sounds like, a Tabbed Pannel.

The :class:`TabbedPannel` contains one tabbed pannel by default pointing towards
the direction you choose.

Simple example
--------------

.. include:: ../../examples/widgets/tabbedpannel_test.py
    :literal:

Customize the Pannel
-----------------------

You can choose the direction the tabbs point towards::

    tab_pos = 'top_mid'

The widgets added to Pannel are orderd by default horizintally like in a
Boxlayout. You can change that by::

    orientation = 'vertical'

Add Tabs/Headings::

    tp = TabbedPannel()
    th = Tabbed_Heading(text='Tab2')
    tp.add_widget(th)

Change the text of default Tab::

    tp.default_tab_text = 'tab head'

Add Items to the Pannel/content area::

    tp.add_widget(your_widget_instance)

Note: There is only one content area shared by all the tabs. Each tab heading
is itself responsible for clearing that content area and adding the widgets it
needs to display to the content area.

Change pannel contents depending on which tab is pressed::

    tab_heading_instance.bind(on_release = my_callback)
    in my_callback
    tabbed_pannel_instance.clear_widgets()
    tabbed_pannel_instance.add_widgets(...)...

Since the default tab exists by default, a `on_default_tab` event is provided
to facilitate changing pannel contents on default tab selection::

    tp.bind(on_default_tab = my_default_tab_callback)

Remove Items::

    tp.remove_widget(Widget/Tab_Heading)
    or
    tp.clear_widgets()# to clear all the widgets in the content area
    or
    tp.clear_tabs()# to remove the Tab_Headings

Access children list, **Warning** This is important! use content.children to
access the children list::

    tp.content.children

Change Appearance of the TabbedPannel::

    background_color = (1, 0, 0, .5) #50% translucent red
    border = [0, 0, 0, 0]
    background_image = 'path/to/background/image'
    tab_image = 'path/to/tab/image'

Change the appearance of the Tab Head::

    tab_heading_instance.background_normal = 'path/to/tab_head/img'
    tab_heading_instance.background_down = 'path/to/tab_head/img_pressed'

Change The Background of the tab strip override the canvas of Tab_Strip
in your kv language::

    <Tab_Strip>
        canvas:
            Color:
                rgba: (0, 1, 0, 1) # green
            Rectangle:
                size: self.size
                pos: self.pos

by default The tab strip takes it's background image, color from the
TabbedPannel's background_image and background_color respectively.

'''
#TODO: overall percentage done[====-]%
# animation
#change added version[====-]%
# move load_string to style.kv

__all__ = ('TabbedPannel', 'Tab_Content', 'Tab_Heading', 'Tab_Strip')

from kivy.event import EventDispatcher
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.properties import ObjectProperty, StringProperty, OptionProperty, \
        ListProperty, NumericProperty


class Tab_Heading(ToggleButton):
    '''A button intented to be used as a Heading/Tab for TabbedPannel widget.

    You can use this Tab_Heading widget to add a new tab  inside TabbedPannel
    '''
    pass


class Tab_Strip(GridLayout):
    '''A strip intented to be used as background for Heading/Tab.
    see module documentation for details.
    '''
    tabbed_pannel = ObjectProperty(None)
    pass


class Tab_Content(GridLayout):
    pass


class TabbedPannel(GridLayout):
    '''Pannel class, see module documentation for more information.
    '''

    background_color = ListProperty([1, 1, 1, 1])
    '''Background color, in the format (r, g, b, a).

    :data:`background_color` is a :class:`~kivy.properties.ListProperty`,
    default to [1, 1, 1, 1].
    '''

    border = ListProperty([16, 16, 16, 16])
    '''Border used for :class:`~kivy.graphics.vertex_instructions.BorderImage`
    graphics instruction, used itself for :data:`background_image`.
    Can be used when using custom background.

    It must be a list of 4 value: (top, right, bottom, left). Read the
    BorderImage instruction for more information about how to play with it.

    :data:`border` is a :class:`~kivy.properties.ListProperty`,
    default to (16, 16, 16, 16)
    '''

    background_image =\
        StringProperty('atlas://data/images/defaulttheme/bubble')
    '''Background image of the Tab content

    :data:`background_image` is a :class:`~kivy.properties.StringProperty`,
    default to 'atlas://data/images/defaulttheme/bubble'.
    '''

    tab_pos = OptionProperty('bottom_mid',
            options=('left_top', 'left_mid', 'left_bottom', 'top_left',
                'top_mid', 'top_right', 'right_top', 'right_mid',
                'right_bottom', 'bottom_left', 'bottom_mid', 'bottom_right'))
    '''Specifies the position of the tabs relative to the content.
    Can be one of: left_top, left_mid, left_bottom top_left, top_mid, top_right
    right_top, right_mid, right_bottom bottom_left, bottom_mid, bottom_right.

    :data:`tab_pos` is a :class:`~kivy.properties.OptionProperty`,
    default to 'bottom_mid'.
    '''

    tab_height = NumericProperty(20)
    '''Specifies the height of the Tab Heading

    :data:`tab_height` is a :class:`~kivy.properties.NumericProperty`,
    default to '20'.
    '''

    tab_width = NumericProperty(30)
    '''Specifies the width of the Tab Heading

    :data:`tab_width` is a :class:`~kivy.properties.NumericProperty`,
    default to '30'.
    '''

    default_tab_text = StringProperty('default tab')
    '''Specifies the Text displayed on the default Tab Heading

    :data:`default_tab_text` is a :class:`~kivy.properties.StringProperty`,
    default to 'default tab'.
    '''

    background_texture = ObjectProperty(None)
    '''Specifies the background texture of the Tabs contents and the Tab Heading

    :data:`background_texture` is a :class:`~kivy.properties.ObjectProperty`,
    default to 'None'.
    '''

    content = ObjectProperty(None)
    '''This is the object where the main content of the current tab is held

    :data:`content` is a :class:`~kivy.properties.ObjectProperty`,
    default to 'None'.
    '''

    orientation = OptionProperty('horizontal',
            options=('horizontal', 'vertical'))
    '''This specifies the manner in which the children inside pannel content
    are arranged. can be one of 'vertical', 'horizontal'

    :data:`orientation` is a :class:`~kivy.properties.OptionProperty`,
    default to 'horizontal'.
    '''

    def __init__(self, **kwargs):
        self._tab_layout = GridLayout(rows=1)
        self._bk_img = Image(
            source=self.background_image, allow_stretch = True,
            keep_ratio = False, color = self.background_color)
        self.background_texture = self._bk_img.texture
        self._tabs = _tabs= Tab_Strip(tabbed_pannel = self,
            rows = 1, cols = 99, size_hint = (None, None),\
            height = self.tab_height, width = self.tab_width)
        self.default_tab = default_tab = \
            Tab_Heading(text = self.default_tab_text,
                height = self.tab_height,
                width = self.tab_width)
        _tabs.add_widget(default_tab)
        default_tab.bind(on_release = self.on_default_tab)

        self.content = content = Tab_Content()
        super(TabbedPannel, self).__init__(**kwargs)
        self.add_widget(content)
        self._bk_img.bind(on_texture=self._on_texture)
        self.on_tab_pos()

    def on_default_tab(self, *l):
        '''This event is fired when the default tab is selected.

        .. versionadded:: 1.0.1?
        '''

    def on_default_tab_text(self, *l):
        self.default_tab.text = self.default_tab_text

    def add_widget(self, *l):
        content = self.content
        if content is None:
            return
        if l[0] == content or l[0] == self._tab_layout:
            super(TabbedPannel, self).add_widget(*l)
        elif isinstance(l[0], Tab_Heading):
            self_tabs = self._tabs
            self_tabs.add_widget(l[0])
            self_tabs.width += l[0].width
        else:
            content.add_widget(l[0])

    def remove_widget(self, *l):
        content = self.content
        if content is None:
            return
        if l[0] == content or l[0] == self._tab_layout:
            super(TabbedPannel, self).remove_widget(*l)
        elif isinstance(l[0], Tab_Heading) and l[0]!= self.default_tab:
            self_tabs = self._tabs
            self_tabs.remove_widget(l[0])
            self_tabs.width -= l[0].width
        else:
            content.remove_widget(l[0])

    def clear_widgets(self, **kwargs):
        content = self.content
        if content is None:
            return
        if kwargs.get('do_super', False):
            super(TabbedPannel, self).clear_widgets()
        else:
            content.clear_widgets()

    def clear_tabs(self, *l):
        self_tabs = self._tabs
        self_tabs.clear_widgets()
        self_tabs.add_widget(self.default_tab)

    def _on_texture(self, *l):
        self.background_texture = self._bk_img.texture

    def on_background_image(self, *l):
        self._bk_img.source = self.background_image

    def on_background_color(self, *l):
        if self.content is None:
            return
        self._bk_img.color = self.background_color

    def on_orientation(self, *l):
        content = self.content
        if not content:
            return
        if self.orientation[0] == 'v':
            content.cols = 1
            content.rows = 99
        else:
            content.cols = 99
            content.rows = 1

    def on_tab_width(self, *l):
        self._tabs.width = self.tab_width*len(self._tabs.children)

    def on_tab_height(self, *l):
        self._tabs.height = self.tab_height

    def on_tab_pos(self, *l):
        self_content = self.content
        if not self_content:
            return
        self_tab_pos = self.tab_pos
        self_tab_layout = self._tab_layout
        self_tab_layout.clear_widgets()
        scrl_v = ScrollView(size_hint= (None, 1))
        self_tabs = self._tabs
        self_tabs_width = self_tabs.width
        scrl_v.add_widget(self_tabs)
        scrl_v.pos = (0, 0)

        self.clear_widgets(do_super=True)
        self_tab_height = self.tab_height

        widget_list = []
        tab_list = []
        if self_tab_pos[0] == 'b' or self_tab_pos[0] == 't':
            self.cols = 1
            self.rows = 2
            self_tab_layout.rows = 1
            self_tab_layout.cols = 3
            self_tab_layout.size_hint = (1, None)
            self_tab_layout.height = self_tab_height
            scrl_v.width = min(self.width, self_tabs_width)

            if self_tab_pos[0] == 'b':
                if self_tab_pos == 'bottom_mid':
                    tab_list = (Widget(), scrl_v, Widget())
                    widget_list = (self_content, self_tab_layout)
                else:
                    if self_tab_pos == 'bottom_left':
                        tab_list = (scrl_v, Widget(), Widget())
                    elif self_tab_pos == 'bottom_right':
                        #add two dummy widgets
                        tab_list = (Widget(), Widget(), scrl_v)
                    widget_list = (self_content, self_tab_layout)
            else:
                if self_tab_pos == 'top_mid':
                    #add two dummy widgets
                    tab_list = (Widget(), scrl_v, Widget())
                elif self_tab_pos == 'top_left':
                    tab_list = (scrl_v, Widget(), Widget())
                elif self_tab_pos == 'top_right':
                    tab_list = (Widget(), Widget(), scrl_v)
                widget_list = (self_tab_layout, self_content)
        elif self_tab_pos[0] == 'l' or self_tab_pos[0] == 'r':
            self.cols = 2
            self.rows = 1
            #self_tab_layout = FloatLayout
            self_tab_layout.rows = 3
            self_tab_layout.cols = 1
            self_tab_layout.size_hint = (None, 1)
            self_tab_layout.width = self_tab_height
            scrl_v.height = self_tab_height
            self_height = self.height
            scrl_v.width = min(self_height, self_tabs_width)

            rotation = 90 if self_tab_pos[0] == 'l' else -90
            sctr = Scatter(do_translation = False,
                               rotation = rotation,
                               do_rotation = False,
                               do_scale = False,
                               size_hint = (None, None),
                               auto_bring_to_front = False,
                               size=scrl_v.size)
            sctr.add_widget(scrl_v)

            lentab_pos = len(self_tab_pos)
            from kivy.clock import Clock
            from functools import partial
            if self_tab_pos[lentab_pos-4:] == '_top':
                sctr.bind(top = Clock.schedule_once(
                    partial(self.update_top, sctr, self.top), -1))
                tab_list = (sctr, )
            elif self_tab_pos[lentab_pos-4:] == '_mid':
                sctr.bind(top = Clock.schedule_once(
                    partial(self.update_top, sctr,
                        self.top - (self.height - scrl_v.width)/2), -1))
                tab_list = (Widget(), sctr, Widget())
            elif self_tab_pos[lentab_pos-7:] == '_bottom':
                tab_list = (Widget(), Widget(), sctr)

            if self_tab_pos[0] =='l':
                widget_list = (self_tab_layout, self_content)
            else:
                widget_list = (self_content, self_tab_layout)

        # add widgets to tab_layout
        add = self_tab_layout.add_widget
        for widg in tab_list:
            add(widg)

        # add widgets to self
        add = self.add_widget
        for widg in widget_list:
            add(widg)

    def update_top(self, sctr, top, dt):
        sctr.top = top
