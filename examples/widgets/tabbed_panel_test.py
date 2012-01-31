'''
TabbedPannel
============

Test of the widget TabbedPannel.
'''

from kivy.app import App
from kivy.animation import Animation
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.tabbedpannel import TabbedPannel, Tab_Heading

from kivy.lang import Builder
Builder.load_string('''
<TabShowcase>
    but: _but
    Button:
        id: _but
        text: 'Press to show Tabbed Pannel'
        on_release: root.show_tab()

<cut_copy_paste>
    size_hint: (None, None)
    size: (350, 250)
    pos_hint: {'center_x': .25, 'y': .55}
    tab_pos: 'top_left'
    tab_height: 20
    tab_width: 70
    default_tab_text: 'tab1'
    default_content: cut
    FloatLayout:
        BoxLayout
            id: cut
            pos:self.parent.pos
            size: self.parent.size
            padding: 3
            TextInput:
                text: 'everything is relative!'
            BubbleButton:
                text:'press to add\\n a tab head'
                on_release: root.add_heading()
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
    Tab_Heading:
        text: 'tab2'
        on_release: root.change_tab_contents(copy)
    Tab_Heading:
        text: 'tab3'
        on_release: root.change_tab_contents(paste)
''')


class cut_copy_paste(TabbedPannel):

    def on_default_tab(self, *l):
        self.change_tab_contents(self.default_content)

    def change_tab_contents(self, *l):
        anim = Animation(color=(1, 1, 1, 0), d =.24, t = 'in_back')

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
            anim = Animation(color = (1, 1, 1, 1), d =.23, t = 'in_quad')
            start_anim(anim, l[0], True)

        anim.bind(on_complete = _on_complete)
        start_anim(anim, self.content.children[0], False)

    def add_heading(self, *l):
        self.add_widget(Tab_Heading(text = 'tabx'))


class TabShowcase(FloatLayout):

    def show_tab(self, *l):
        if not hasattr(self, 'tab'):
            self.tab = tab = cut_copy_paste()
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
