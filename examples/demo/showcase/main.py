import kivy
kivy.require('1.0.6')

from weakref import ref
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.textinput import TextInput
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.uix.switch import Switch
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.filechooser import FileChooserIconView, FileChooserListView
from kivy.properties import StringProperty
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from functools import partial
import random

class Showcase(FloatLayout):
    pass


class KivyImageScatter(Scatter):
    pass


class ButtonsScatter(Scatter):
    pass


class AnchorLayoutShowcase(FloatLayout):

    anchor_x = StringProperty('left')
    anchor_y = StringProperty('top')

    def __init__(self, **kwargs):
        super(AnchorLayoutShowcase, self).__init__(**kwargs)
        Clock.schedule_once(self.change_anchor, 1)

    def change_anchor(self, *l):
        if self.anchor_x == 'left':
            self.anchor_x = 'center'
        elif self.anchor_x == 'center':
            self.anchor_x = 'right'
        else:
            self.anchor_x = 'left'
            if self.anchor_y == 'top':
                self.anchor_y = 'center'
            elif self.anchor_y == 'center':
                self.anchor_y = 'bottom'
            else:
                self.anchor_y = 'top'

        Clock.schedule_once(self.change_anchor, 1)


class BoxLayoutShowcase(FloatLayout):

    def __init__(self, **kwargs):
        super(BoxLayoutShowcase, self).__init__(**kwargs)
        self.buttons = 0
        self.txt = 'horizontal'
        Clock.schedule_once(self.add_button, 1)

    def add_button(self, *l):
        self.buttons += 1
        if self.buttons > 5:
            self.buttons = 0
            self.blayout.clear_widgets()
            if self.txt == "vertical":
                self.txt = self.blayout.orientation = 'horizontal'
            else:
                self.txt = self.blayout.orientation = 'vertical'
        self.blayout.add_widget(Button(text = self.txt))
        Clock.schedule_once(self.add_button, 1)


class FloatLayoutShowcase(FloatLayout):

    def __init__(self, **kwargs):
        super(FloatLayoutShowcase, self).__init__(**kwargs)
        self.buttons = 0
        Clock.schedule_once(self.add_button, 1)

    def add_button(self, *l):
        self.buttons += 1
        if self.buttons > 5:
            self.buttons = 0
            self.flayout.clear_widgets()
        self.flayout.add_widget(Button(text = 'no restrictions\n what so ever',
            size_hint = (None, None), size = (150, 40),
            pos_hint = {'x':random.random(), 'y': random.random()}))
        Clock.schedule_once(self.add_button, 1)


class GridLayoutShowcase(FloatLayout):

    def __init__(self, **kwargs):
        super(GridLayoutShowcase, self).__init__(**kwargs)
        self.buttons = 0
        self.cols_default = self.glayout.cols
        self.rows_default = self.glayout.rows
        self.glayout.rows = 3
        self.txt = "rows = 3"
        Clock.schedule_once(self.add_button, 1)

    def add_button(self, *l):
        self.buttons += 1
        if self.buttons > 20:
            self.buttons = 0
            self.glayout.clear_widgets()
            if self.txt == "rows = 3":
                self.glayout.cols = 3
                self.glayout.rows = 7
                self.txt = "cols = 3"
            else:
                self.glayout.rows = 3
                self.glayout.cols = 7
                self.txt = "rows = 3"
        self.glayout.add_widget(Button(text = self.txt))
        Clock.schedule_once(self.add_button, 1)


class StackLayoutShowcase(FloatLayout):

    def __init__(self, **kwargs):
        super(StackLayoutShowcase, self).__init__(**kwargs)
        self.buttons = 0
        self.txt = 'lr-tb'
        Clock.schedule_once(self.add_button, 1)

    def add_button(self, *l):
        self.buttons += 1
        if self.buttons > 5:
            self.buttons = 0
            self.slayout.clear_widgets()
            if self.txt == "tb-lr":
                self.txt = self.slayout.orientation = 'lr-tb'
            else:
                self.txt = self.slayout.orientation = 'tb-lr'
        self.slayout.add_widget(Button(text = self.txt))
        Clock.schedule_once(self.add_button, 1)


class ShowcaseApp(App):

    def on_select_node(self, instance, value):
        # ensure that any keybaord is released
        self.content.get_parent_window().release_keyboard()

        self.content.clear_widgets()
        try:
            w = getattr(self, 'show_%s' %
                        value.text.lower().replace(' ', '_'))()
            self.content.add_widget(w)
        except Exception, e:
            print e

    def on_pause(self):
        return True

    def build(self):
        root = BoxLayout(orientation='horizontal', padding=20, spacing=20)
        tree = TreeView(
            size_hint=(None, 1), width=200, hide_root=True, indent_level=0)

        def create_tree(text):
            return tree.add_node(TreeViewLabel(
                text=text, is_open=True, no_selection=True))

        def attach_node(text, n):
            tree.add_node(TreeViewLabel(text=text), n)

        tree.bind(selected_node=self.on_select_node)
        n = create_tree('Buttons')
        attach_node('Standard buttons', n)
        attach_node('Options buttons', n)
        attach_node('Horizontal sliders', n)
        attach_node('Vertical sliders', n)
        attach_node('Scatter with image', n)
        attach_node('Scatter with buttons', n)
        attach_node('Monoline textinput', n)
        attach_node('Multiline textinput', n)
        attach_node('Standard treeview', n)
        attach_node('Treeview without root', n)
        attach_node('Accordion', n)
        attach_node('Popup', n)
        attach_node('Switch', n)
        attach_node('ProgressBar', n)
        n = create_tree('Layouts')
        attach_node('Anchor Layout', n)
        attach_node('Box Layout', n)
        attach_node('Float Layout', n)
        attach_node('Grid Layout', n)
        attach_node('Stack Layout', n)
        n = create_tree('Experimentals')
        attach_node('Filechooser icon', n)
        attach_node('Filechooser list', n)
        root.add_widget(tree)
        self.content = content = BoxLayout()
        root.add_widget(content)
        sc = Showcase()
        sc.content.add_widget(root)
        return sc

    def show_anchor_layout(self):
        return AnchorLayoutShowcase()

    def show_box_layout(self):
        return BoxLayoutShowcase()

    def show_float_layout(self):
        return FloatLayoutShowcase()

    def show_grid_layout(self):
        return GridLayoutShowcase()

    def show_stack_layout(self):
        return StackLayoutShowcase()

    def show_scatter_with_image(self):
        s = KivyImageScatter(center=self.content.center)
        col = Widget()
        col.add_widget(s)
        return col

    def show_scatter_with_buttons(self):
        s = ButtonsScatter(size=(300, 200))
        s.center = self.content.center
        col = Widget()
        col.add_widget(s)
        return col

    def show_standard_buttons(self):
        col = BoxLayout(spacing=10)
        col.add_widget(Button(text='Hello world'))
        col.add_widget(Button(text='Hello world', state='down'))
        return col

    def show_options_buttons(self):
        col = BoxLayout(spacing=10)
        col.add_widget(ToggleButton(text='Option 1', group='t1'))
        col.add_widget(ToggleButton(text='Option 2', group='t1'))
        col.add_widget(ToggleButton(text='Option 3', group='t1'))
        return col

    def show_horizontal_sliders(self):
        col = BoxLayout(orientation='vertical', spacing=10)
        col.add_widget(Slider())
        col.add_widget(Slider(value=50))
        return col

    def show_vertical_sliders(self):
        col = BoxLayout(spacing=10)
        col.add_widget(Slider(orientation='vertical'))
        col.add_widget(Slider(orientation='vertical', value=50))
        return col

    def show_multiline_textinput(self):
        col = AnchorLayout()
        col.add_widget(TextInput(size_hint=(None, None), size=(200, 100)))
        return col

    def show_monoline_textinput(self):
        col = AnchorLayout()
        col.add_widget(TextInput(size_hint=(None, None), size=(200, 32),
                                 multiline=False))
        return col

    def show_switch(self):
        col = AnchorLayout()
        col.add_widget(Switch(active=True))
        return col

    def show_popup(self):
        btnclose = Button(text='Close this popup', size_hint_y=None, height=50)
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text='Hello world'))
        content.add_widget(btnclose)
        popup = Popup(content=content, title='Modal popup example',
                      size_hint=(None, None), size=(300, 300),
                      auto_dismiss=False)
        btnclose.bind(on_release=popup.dismiss)
        button = Button(text='Open popup', size_hint=(None, None),
                        size=(150, 70))
        button.bind(on_release=popup.open)
        popup.open()
        col = AnchorLayout()
        col.add_widget(button)
        return col

    def show_standard_treeview(self):
        return self.populate_treeview(TreeView())

    def show_treeview_without_root(self):
        # test with removing a node
        col = BoxLayout(orientation='vertical')
        tv = self.populate_treeview(TreeView(hide_root=True))
        col.add_widget(tv)
        btn = Button(text='Remove one node', size_hint_y=None, height=50)
        def remove_node(*l):
            if not tv.root.is_leaf:
                tv.remove_node(tv.root.nodes[0])
        btn.bind(on_release=remove_node)
        col.add_widget(btn)
        return col

    def populate_treeview(self, tv):
        n = tv.add_node(TreeViewLabel(text='Item 1'))
        for x in xrange(3):
            tv.add_node(TreeViewLabel(text='Subitem %d' % x), n)
        n = tv.add_node(TreeViewLabel(text='Item 2', is_open=True))
        for x in xrange(3):
            tv.add_node(TreeViewLabel(text='Subitem %d' % x), n)
        n = tv.add_node(TreeViewLabel(text='Item 3'))
        for x in xrange(3):
            tv.add_node(TreeViewLabel(text='Subitem %d' % x), n)
        return tv

    def show_accordion(self):
        root = Accordion()
        for x in xrange(5):
            item = AccordionItem(title='Title %d' % x)
            item.add_widget(Label(text='Very big content\n' * 10))
            root.add_widget(item)
        col = AnchorLayout()
        col.add_widget(root)
        return col

    def show_filechooser_icon(self):
        return FileChooserIconView()

    def show_filechooser_list(self):
        return FileChooserListView()

    def show_progressbar(self):
        pb = ProgressBar()
        Clock.schedule_interval(partial(self.update_pb, ref(pb)), 0)
        return pb

    def update_pb(self, pb, dt):
        if not pb():
            return False
        pb().value = (pb().value + dt * 10) % (1 + pb().max)

if __name__ in ('__main__', '__android__'):
    ShowcaseApp().run()
