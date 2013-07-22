from kivy.base import runTouchApp
from kivy.lang import Builder

runTouchApp(Builder.load_string('''
FloatLayout
    canvas:
        Color:
            rgb: .9, .9, .9
        Rectangle:
            size: self.size
    ActionBar:
        size_hint_y: None
        height: '48dp'
        pos_hint: {'top':1}
        ActionView:
            use_separator: True
            ActionPrevious:
                title: 'Title'
            ActionOverflow:
            ActionButton:
                text: 'A'
                size_hint_x: None
                width: '48dp'
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
                ActionButton:
                    text: 'Btn5'
                ActionButton:
                    text: 'Btn6'
                ActionButton:
                    text: 'Btn7'
'''))

