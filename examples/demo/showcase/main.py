import kivy
kivy.require('1.1.3')

import random

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import Metrics
from kivy.properties import NumericProperty
from kivy.properties import StringProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scatter import Scatter
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.uix.widget import Widget


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
        self.text_size = self.size
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

        btn = Button(text=self.txt, halign='center', valign='middle')
        btn.bind(size=btn.setter('text_size'))
        self.blayout.add_widget(btn)
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
        self.flayout.add_widget(Button(text='no restrictions\n what so ever',
            size_hint=(None, None), size=(150, 40),
            pos_hint={'x': random.random(), 'y': random.random()}))
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
        if self.buttons > 10:
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
        self.glayout.add_widget(Button(text=self.txt))
        Clock.schedule_once(self.add_button, 1)


class StackLayoutShowcase(FloatLayout):

    def __init__(self, **kwargs):
        super(StackLayoutShowcase, self).__init__(**kwargs)
        self.buttons = 0
        self.orientationit = 0
        self.txt = 'lr-tb'
        Clock.schedule_once(self.add_button, 1)

    def add_button(self, *l):
        orientations = ('lr-tb', 'tb-lr',
                        'rl-tb', 'tb-rl',
                        'lr-bt', 'bt-lr',
                        'rl-bt', 'bt-rl')
        self.buttons += 1
        if self.buttons > 11:
            self.buttons = 0
            self.slayout.clear_widgets()
            self.orientationit = (self.orientationit + 1) % len(orientations)
            self.slayout.orientation = orientations[self.orientationit]
            self.txt = self.slayout.orientation
        self.slayout.add_widget(Button(
            text=("%s %d" % (self.txt, self.buttons)),
            size_hint=(.1 + self.buttons * 0.02, .1 + self.buttons * 0.01)))
        Clock.schedule_once(self.add_button, .5)


class RelativeLayoutShowcase(FloatLayout):
    pass



class StandardWidgets(FloatLayout):

    value = NumericProperty(0)

    def __init__(self, **kwargs):
        super(StandardWidgets, self).__init__(**kwargs)
        Clock.schedule_interval(self.increment_value, 1 / 30.)

    def increment_value(self, dt):
        self.value += dt


class ComplexWidgets(FloatLayout):
    pass


class ComplexWidgets2(FloatLayout):
    pass


class TreeViewWidgets(FloatLayout):
    pass


class FontSizesWidgets(BoxLayout):
    pass


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
        n = create_tree('Widgets')
        attach_node('Standard widgets', n)
        attach_node('Complex widgets 1', n)
        attach_node('Complex widgets 2', n)
        attach_node('Scatters', n)
        attach_node('Treeviews', n)
        attach_node('Font Sizes', n)
        attach_node('Popup', n)
        n = create_tree('Layouts')
        attach_node('Anchor Layout', n)
        attach_node('Box Layout', n)
        attach_node('Float Layout', n)
        attach_node('Grid Layout', n)
        attach_node('Stack Layout', n)
        attach_node('Relative Layout', n)


        root.add_widget(tree)
        self.content = content = BoxLayout()
        root.add_widget(content)
        sc = Showcase()
        sc.content.add_widget(root)
        self.content.add_widget(StandardWidgets())
        return sc

    def show_standard_widgets(self):
        return StandardWidgets()

    def show_complex_widgets_1(self):
        return ComplexWidgets()

    def show_complex_widgets_2(self):
        return ComplexWidgets2()

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

    def show_relative_layout(self):
        return RelativeLayoutShowcase()

    def show_scatters(self):
        col = Widget()
        center = self.content.center_x - 150, self.content.center_y
        s = KivyImageScatter(center=center)
        col.add_widget(s)
        center = self.content.center_x + 150, self.content.center_y
        s = ButtonsScatter(size=(300, 200))
        s.center = center
        col.add_widget(s)
        return col

    def show_popup(self):
        btnclose = Button(text='Close this popup', size_hint_y=None, height='50sp')
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text='Hello world'))
        content.add_widget(btnclose)
        popup = Popup(content=content, title='Modal popup example',
                      size_hint=(None, None), size=('300dp', '300dp'))
        btnclose.bind(on_release=popup.dismiss)
        button = Button(text='Open popup', size_hint=(None, None),
                        size=('150sp', '70dp'),
                        on_release=popup.open)
        popup.open()
        col = AnchorLayout()
        col.add_widget(button)
        return col

    def show_treeviews(self):
        tv = TreeViewWidgets()
        self.populate_treeview(tv.treeview1)
        self.populate_treeview(tv.treeview2)
        return tv

    def show_font_sizes(self):
        font_sizes = FontSizesWidgets()
        metrics_values = {
            'dpi': str(Metrics.dpi),
            'dpi_rounded': str(Metrics.dpi_rounded),
            'density': str(Metrics.density),
            'fontscale': str(Metrics.fontscale),
        }
        label = font_sizes.children[1]
        label.text = ('DPI: {dpi} | '
                      'DPI Rounded: {dpi_rounded} | '
                      'Density: {density} | '
                      'Font Scale: {fontscale} ').format(**metrics_values)
        return font_sizes

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

if __name__ == '__main__':
    ShowcaseApp().run()
