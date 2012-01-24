'''
TabbedPannel
======

Test of the widget TabbedPannel.
'''

from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.tabbedpannel import TabbedPannel
from kivy.properties import ObjectProperty

from kivy.lang import Builder
Builder.load_string('''
<cut_copy_paste>
    size_hint: (None, None)
    size: (350, 250)
    pos_hint: {'center_x': .25, 'y': .55}
    tab_pos: 'top_left'
    tab_height: 20
    tab_width: 70
    default_tab_text: 'tab1'
    default_content: cut
    BubbleButton:
        id: cut
        text: 'Cut'
    BubbleButton:
        id: copy
        text: 'Copy'
    BubbleButton:
        id: paste
        text: 'Paste'
    Tab_Heading:
        text: 'tab2'
        on_release: root.change_tab_contents(copy)
    Tab_Heading:
        text: 'tab3'
        on_release: root.change_tab_contents(paste)
    #Tab_Heading:
    #    text: 'tab4'
    #    on_release: root.clear_widgets()
    #Tab_Heading:
    #    text: 'tab5'
    #    on_release: root.clear_widgets()
''')


class cut_copy_paste(TabbedPannel):

    default_content = ObjectProperty(None)

    def on_default_tab(self, *l):
        self.change_tab_contents(self.default_content)

    def change_tab_contents(self, *l):
        anim = Animation( color=(1, 1, 1, 0), d =.27, t = 'in_back')

        def start_anim(*l):
            anim.start(self.content.children[0])

        start_anim()
        self.clear_widgets()
        self.add_widget(l[0])
        anim = Animation( color = (1, 1, 1, 1), d =.27, t = 'in_quad')
        start_anim()


class TabShowcase(FloatLayout):

    def __init__(self, **kwargs):
        super(TabShowcase, self).__init__(**kwargs)
        self.but = Button(text='Press to show Tabbed Pannel')
        self.but.bind(on_release=self.show_tab)
        self.add_widget(self.but)

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
        self.but.text='Tabs in \'%s\' position,\n press to change to next pos'\
                %self.tab.tab_pos


class TestTabApp(App):

    def build(self):
        return TabShowcase()

if __name__ in ('__main__', '__android__'):
    TestTabApp().run()
