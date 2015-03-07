'''
Using Includes
==============

This demonstrates using include directives within .kv files. You should see
a large button labelled 'Includes!' with a red rectangle in the lower left
corner. The main application is named TestApp, which causes the file
test.kv to load. This sets the root widget to CustomLayout, which it
defines by including the file layout.kv using '#:include'. The file
button.kv is loaded twice, first from layout.kv and, with the
'#:include force' in test.kv, then unloaded and loaded again.
'''

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button


class SpecialButton(Button):
    pass


class CustomLayout(BoxLayout):
    pass


class TestApp(App):
    pass

if __name__ == '__main__':
    TestApp().run()
