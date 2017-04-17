from kivy.base import runTouchApp
from kivy.lang import Builder

runTouchApp(Builder.load_string('''
ActionBar:
    pos_hint: {'top':1}
    ActionView:
        use_separator: True
        ActionPrevious:
            title: 'Action Bar'
            with_previous: False
        ActionOverflow:
        ActionButton:
            text: 'Btn0'
            icon: 'atlas://data/images/defaulttheme/audio-volume-high'
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
