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
    size_hint: (.54, .45)
    pos_hint: {'center_x': .5, 'y': .55}
    default_tab_text: 'Settings'
    default_tab_content: default_content
    FloatLayout:
        BoxLayout
            id: default_content
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
            id: tab_2_content
            pos:self.parent.pos
            size: self.parent.size
            source: 'data/images/defaulttheme-0.png'
        Image:
            id: tab_3_content
            pos:self.parent.pos
            size: self.parent.size
            source: 'data/images/image-loading.gif'
    TabbedPanelHeader:
        text: 'tab2'
        content: tab_2_content
    TabbedPanelHeader:
        text: 'tab3'
        content: tab_3_content
''')


class Tp(TabbedPanel):
    #override tab switching method to animate on tab switch
    def switch_to(self, header):
        if header.content is None:
            return
        anim = Animation(color=(1, 1, 1, 0), d =.24, t = 'in_out_quad')

        def start_anim(_anim, child, in_complete, *lt):
            if hasattr(child, 'color'):
                _anim.start(child)
            elif not in_complete:
                _on_complete()

        def _on_complete(*lt):
            self.clear_widgets()
            if hasattr(header.content, 'color'):
                header.content.color = (0, 0, 0, 0)
                anim = Animation(color = (1, 1, 1, 1), d =.23, t = 'in_out_quad')
                start_anim(anim, header.content, True)
            self.add_widget(header.content)

        anim.bind(on_complete = _on_complete)
        if self.content != None:
            start_anim(anim, self.content.children[0], False)
        else:
            _on_complete()


class PanelTest(Tp):

    def update_pos(self, sctr, tab, *l):
        sctr.pos = tab.pos

    def update_sctr_rotation(self, sctr, *l):
        sctr.rotation = 90 if self.tab_pos[0] != 'l' else -90

    def economize_tabs(self, *l):
        # switch width and height for long tabs
        self.tab_width, self.tab_height = self.tab_height, self.tab_width

        but_state = l[0].state
        for tab in self.tab_list:
            if but_state == 'normal':
                try:
                    tab.color = tab.old_color
                except AttributeError:
                    pass
                # remove scatter and label
                tab.clear_widgets()
            else:
                # add a scatter with a label rotated to display standing text
                lbl = Label(text = tab.text,
                    size_hint=(None, None), size=tab.size)
                sctr = Scatter(do_translation = False,
                    rotation = 90 if self.tab_pos[0] != 'l' else -90,
                    do_rotation = False,
                    do_scale = False,
                    size_hint = (None, None),
                    auto_bring_to_front = False,
                    size = lbl.size)
                tab.add_widget(sctr)
                sctr.add_widget(lbl)
                # update scatter rotation on tab_pos required only if you need
                # to dynamically change the tab_pos when in long tabs mode and
                # going from 'bottom_right' to 'left_*' tab_pos
                self.bind(tab_pos = partial(self.update_sctr_rotation, sctr))
                tab.old_color = tab.color
                tab.color = (0, 0, 0, 0)

                tab.bind(pos = partial(self.update_pos, sctr, tab))

    def position_close_btn(self, tab, btn, *l):
        btn.pos = (tab.right - btn.width, tab.top - btn.height)

    def close_tab(self, tab, *l):
        self.remove_widget(tab)

    def closable_tabs(self, *l):
        but_state = l[0].state
        for tab in self.tab_list:
            if but_state == 'normal':
                tab.clear_widgets()
            else:
                btn = Button(background_normal =
                    'tools/theming/defaulttheme/close.png',
                    size_hint = (None, None),
                    size = (15, 15),
                    border = (0, 0, 0, 0))
                tab.add_widget(btn)
                btn.bind(on_release = partial(self.close_tab, tab))
                btn.pos = (tab.right - btn.width, tab.top - btn.height)
                tab.bind(pos = partial(self.position_close_btn, tab, btn))

    def image_tabs(self, but):
        but_state = but.state
        if but_state == 'normal':
            self.tab_height = self.old_height
            for tab in self.tab_list:
                try:
                    tab.color = tab.old_color
                    tab.background_down = tab.old_img
                    tab.background_normal = tab.old_img_normal
                except AttributeError:
                    pass
            # all new tabs should also follow style
            Builder.load_string(str('''
<TabbedPanelHeader>:
    background_normal: '%s'
    background_down: '%s'
    color: (%x, %x, %x, %x)
    font_size: 11''') %(tab.old_img_normal, tab.old_img,
        tab.color[0], tab.color[1], tab.color[2], tab.color[3]))
        else:
            self.old_height = self.tab_height
            self.tab_height = 50
            for tab in self.tab_list:
                tab.old_img = tab.background_down
                tab.background_down = 'softboy.png'
                tab.old_img_normal = tab.background_normal
                tab.background_normal = 'sequenced_images/data/images/info.png'
                tab.old_color = tab.color
                tab.color = (0, 0, 0, 0)
            # all new tabs should also follow style
            Builder.load_string('''
<TabbedPanelHeader>:
    background_normal: 'sequenced_images/data/images/info.png'
    background_down: 'softboy.png'
    color: 0,0,0,0
    font_size: 11''')

    def add_heading(self):
        self.add_widget(TabbedPanelHeader(text = 'tabx'))


class TabShowcase(FloatLayout):

    def show_tab(self):
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
