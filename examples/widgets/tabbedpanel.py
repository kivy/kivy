'''
TabbedPanel
============

Test of the widget TabbedPanel.
'''

from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder

Builder.load_string("""

<Test>:
    size_hint: .5, .5
    pos_hint: {'center_x': .5, 'center_y': .5}
    default_tab_content: set1_content

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
    pass

class TabbedPanelApp(App):
    def build(self):
        return Test()

if __name__ == '__main__':
    TabbedPanelApp().run()
