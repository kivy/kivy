'''
TabbedPanel
============

Test of the widget TabbedPanel.
'''

from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.lang import Builder

Builder.load_string("""
<Test>
    size_hint: .5, .5
    default_content: set1_content
    Label:
        id: set1_content
        text: 'this is the first tabs content area'
    BoxLayout:
        id: set2_content
        Label:
            text: 'second tabs content area'
        Button:
            text: 'Button'
    BoxLayout:
        id: set3_content
        BubbleButton:
            text: 'Bubble Button'
    TabbedPanelHeader:
        text: 'set2'
        on_release: root.change_tab_contents(set2_content)
    TabbedPanelHeader:
        text: 'set3'
        on_release: root.change_tab_contents(set3_content)
""")

class Test(TabbedPanel):

    def __init__(self, **kwargs):
        super(Test, self).__init__(**kwargs)
        self.change_tab_contents(self.default_content)

    def on_Default_tab(self, *l):
        self.change_tab_contents(self.default_content)

    def change_tab_contents(self, content, *l):
        self.clear_widgets()
        self.add_widget(content)

class MyApp(App):
    def build(self):
        return Test()

if __name__ == '__main__':
    MyApp().run()