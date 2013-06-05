from kivy.base import runTouchApp
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.uix import actionbar
from kivy.lang import Builder

Builder.load_string('''
<MainWindow>:
    ActionBar:
        size_hint: 1,0.1
        pos_hint: {'top':1}
        ActionView:
            use_separator: True
            ActionPrevious:
                title: 'Title'
            ActionOverflow:
            ActionButton:
                text: 'Btn0'
            ActionButton:
                text: 'Btn1'
            ActionButton:
                text: 'Btn2'
            ActionButton:
                text: 'Btn3'
            ActionButton:
                text: 'Btn4'
            ActionGroup:
                text: 'Group1'
                #mode: 'spinner'
                ActionButton:
                    text: 'Btn5'
                ActionButton:
                    text: 'Btn6'
                ActionButton:
                    text: 'Btn7'
''')

class MainWindow(FloatLayout):
    pass

runTouchApp(MainWindow())
