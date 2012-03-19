'''
TabbedPanel
============

Test of the widget TabbedPanel showing all capabilities.
'''

from kivy.app import App
from kivy.animation import Animation
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scatter import Scatter
from functools import partial

from kivy.lang import Builder

Builder.load_string('''
<TabShowcase>
    but: _but
    Button:
        id: _but
        text: 'Press to show Tabbed Panel'
        on_release: root.show_tab()

<PanelTest>
    size_hint: (None, None)
    size: (350, 250)
    pos_hint: {'center_x': .25, 'y': .55}
    tab_pos: 'top_left'
    tab_height: 20
    tab_width: 70
    default_tab_text: 'Settings'
    default_content: cut
    FloatLayout:
        BoxLayout
            id: cut
            pos:self.parent.pos
            size: self.parent.size
            Label:
                text: 'everything is relative!'
            BoxLayout:
                orientation: 'vertical'
                BubbleButton:
                    text:'press to add\\n a tab head'
                    on_release: root.add_heading()
                ToggleButton:
                    group: 'tab_style'
                    text: '  Economic\\n Long Tabs'
                    on_state: root.economize_tabs(self)
                ToggleButton:
                    group: 'tab_style'
                    text: 'Image tabs'
                    on_state: root.image_tabs(self)
                ToggleButton:
                    group: 'tab_style'
                    text: 'Closable tabs'
                    on_state: root.closable_tabs(self)
        Image:
            id: copy
            color: 1, 1, 1, 0
            pos:self.parent.pos
            size: self.parent.size
            source: 'data/images/defaulttheme-0.png'
        Image:
            id: paste
            color: 1, 1, 1, 0
            pos:self.parent.pos
            size: self.parent.size
            source: 'data/images/image-loading.gif'
    TabbedPanelHeader:
        text: 'tab2'
        on_release: root.change_tab_contents(copy)
    TabbedPanelHeader:
        text: 'tab3'
        on_release: root.change_tab_contents(paste)
''')


class PanelTest(TabbedPanel):

    def update_pos(self, sctr, tab, *l):
        sctr.pos = tab.pos

    def economize_tabs(self, *l):
        self.tab_width, self.tab_height = self.tab_height, self.tab_width
        but_state = l[0].state

        for tab in self.tab_list:
            if but_state == 'normal':
                tab._label.text = tab.text
                tab.clear_widgets()
            else:
                lbl = Label(text = tab.text,
                    size_hint = (None, None),
                    size = tab.size)
                sctr = Scatter(do_translation = False,
                    rotation = 90 if self.tab_pos[0] != 'l' else -90,
                    do_rotation = False,
                    do_scale = False,
                    size_hint = (None, None),
                    auto_bring_to_front = False,
                    size = lbl.size)
                tab.add_widget(sctr)
                sctr.add_widget(lbl)
                tab._label.text = ''

                tab.bind(pos = partial(self.update_pos, sctr, tab))

    def position_close_btn(self, tab, btn, *l):
        btn.pos = (tab.x + tab.width - btn.width, tab.y + 0)

    def close_tab(self, tab, *l):
        self.remove_widget(tab)

    def closable_tabs(self, *l):
        but_state = l[0].state
        for tab in self.tab_list:
            if but_state == 'normal':
                tab.clear_widgets()
            else:
                btn = Button(background_normal =
                    'atlas://data/images/defaulttheme/image-missing',
                    size_hint = (None, None),
                    size = (20, 20))
                tab.add_widget(btn)
                btn.bind(on_release = partial(self.close_tab, tab))
                btn.pos = (tab.x + tab.width - btn.width, tab.y + 0)
                tab.bind(pos = partial(self.position_close_btn, tab, btn))

    def image_tabs(self, *l):
        but_state = l[0].state
        if but_state == 'normal':
            self.tab_height = self.old_height
            for tab in self.tab_list:
                tab._label.text = tab.text
                try:
                    tab.background_down = tab.old_img
                    tab.background_normal = tab.old_img_normal
                except AttributeError:
                    pass
        else:
            self.old_height = self.tab_height
            self.tab_height = 50
            for tab in self.tab_list:
                tab.old_img = tab.background_down
                tab.background_down = 'softboy.png'
                tab.old_img_normal = tab.background_normal
                tab.background_normal = 'sequenced_images/data/images/info.png'
                tab._label.text = ''

    def on_default_tab(self, *l):
        self.change_tab_contents(self.default_content)

    def change_tab_contents(self, *l):
        anim = Animation(color=(1, 1, 1, 0), d =.24, t = 'in_out_quad')

        def start_anim(_anim, child, in_complete, *lt):
            if hasattr(child, 'color'):
                _anim.start(child)
            elif not in_complete:
                _on_complete()

        def _on_complete(*lt):
            if l[0].parent:
                l[0].parent.remove_widget(l[0])
            self.clear_widgets()
            self.add_widget(l[0])
            anim = Animation(color = (1, 1, 1, 1), d =.23, t = 'in_out_quad')
            start_anim(anim, l[0], True)

        anim.bind(on_complete = _on_complete)
        start_anim(anim, self.content.children[0], False)

    def add_heading(self, *l):
        self.add_widget(TabbedPanelHeader(text = 'tabx'))


class TabShowcase(FloatLayout):

    def show_tab(self, *l):
        if not hasattr(self, 'tab'):
            self.tab = tab = PanelTest()
            self.add_widget(tab)
        else:
            values = ('left_top', 'left_mid', 'left_bottom', 'top_left',
                'top_mid', 'top_right', 'right_top', 'right_mid',
                'right_bottom', 'bottom_left', 'bottom_mid', 'bottom_right')
            index = values.index(self.tab.tab_pos)
            self.tab.tab_pos = values[(index + 1) % len(values)]
        self.but.text = 'Tabs in\'%s\' position,\n press to change to next pos'\
                %self.tab.tab_pos


class TestTabApp(App):

    def build(self):
        return TabShowcase()

if __name__ in ('__main__', '__android__'):
    TestTabApp().run()
