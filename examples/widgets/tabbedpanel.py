'''
TabbedPanel
============

Test of the widget TabbedPanel.
'''

from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.lang import Builder

Builder.load_string("""
<Test>:
    size_hint: .5, .5
    pos_hint: {'center_x': .5, 'center_y': .5}
    default_content: set1_content

    Label:
        id: set1_content
        text: 'First tab content area'

    BoxLayout:
        id: set2_content
        Label:
            text: 'Second tab content area'
        Button:
            text: 'Button that does nothing'

    RstDocument:
        id: set3_content
        text: '\\n'.join(("Hello world", "-----------", "You are in the third tab."))

    # now categorize widgets inserted above in a specific header
    TabbedPanelHeader:
        text: 'Tab 2'
        content: set2_content
    TabbedPanelHeader:
        text: 'Tab 3'
        content: set3_content
""")

class Test(TabbedPanel):

    def __init__(self, **kwargs):
        super(Test, self).__init__(**kwargs)
        self.change_tab_contents(self.default_content)

    def on_default_tab(self, *l):
        self.change_tab_contents(self.default_content)

    def change_tab_contents(self, content, *l):
        self.clear_widgets()
        self.add_widget(content)

class MyApp(App):
    def build(self):
        return Test()

if __name__ == '__main__':
    MyApp().run()
