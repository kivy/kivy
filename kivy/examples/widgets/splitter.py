from kivy.base import runTouchApp
from kivy.lang import Builder

bl = Builder.load_string('''
BoxLayout:
    orientation: 'vertical'
    BoxLayout:
        size_hint_y: None
        height: sp(60)
        Label:
            text: 'keep_within_parent?'
        CheckBox:
            id: in_parent_box
            active: False
        Label:
            text: 'rescale_with_parent?'
        CheckBox:
            id: rescale_box
            active: False
    BoxLayout:
        orientation: 'horizontal'
        Button:
            text: 'left btn'
            size_hint_x: 0.3
        BoxLayout:
            orientation: 'vertical'
            Button:
                text: "Btn0"
            BoxLayout:
                Splitter:
                    sizable_from: 'right'
                    keep_within_parent: in_parent_box.active
                    rescale_with_parent: rescale_box.active
                    Button:
                        text: 'Btn5'
                Button:
                    text: 'Btn6'
            BoxLayout:
                sizable_from: 'top'
                BoxLayout:
                    orientation: 'horizontal'
                    BoxLayout:
                        orientation: 'vertical'
                        Button:
                            text: "Btn1"
                        Splitter:
                            sizable_from: 'top'
                            keep_within_parent: in_parent_box.active
                            rescale_with_parent: rescale_box.active
                            Button:
                                text: "Btn2"
                    Splitter:
                        sizable_from: 'left'
                        keep_within_parent: in_parent_box.active
                        rescale_with_parent: rescale_box.active
                        Button:
                            text: "Btn3"
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.3
            Button:
                text: 'right btn'
            Splitter:
                sizable_from: 'bottom'
                keep_within_parent: in_parent_box.active
                rescale_with_parent: rescale_box.active
                Button:
                    text: 'Btn7'
            Button:
                text: 'right btn'
''')


runTouchApp(bl)
