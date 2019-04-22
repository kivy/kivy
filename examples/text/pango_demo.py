# -*- coding: utf-8 -*-

from kivy.base import runTouchApp
from kivy.lang import Builder
from kivy.factory import Factory as F


class DemoBox(F.ButtonBehavior, F.BoxLayout):
    base_direction = F.StringProperty(None, allownone=True)
    font_context = F.StringProperty(None, allownone=True)
    font_size = F.NumericProperty(10)


runTouchApp(Builder.load_string('''
#:import F kivy.factory.Factory
<MenuLabel@Label>:
    bold: True
    size_hint_x: None
    width: '150dp'
    text_size: self.size
    halign: 'right'
    valign: 'middle'
<MyToggleButton@ToggleButton>:
    hacked_state: False
    allow_no_selection: False
    on_state: self.hacked_state = self.state == 'down'
<HalignButton@MyToggleButton>:
    text: 'auto'
    group: 'halign'
    on_hacked_state: for c in root.parent.__boxes.children: \
                c.halign = root.text
<FontButton@MyToggleButton>:
    text: '20'
    group: 'font'
    on_hacked_state: for c in root.parent.__boxes.children: \
                c.font_size = int(root.text)
<ContextButton@MyToggleButton>:
    text: 'system://'
    group: 'context'
    on_hacked_state: for c in root.parent.__boxes.children: \
                c.font_context = root.text
<BaseDirButton@MyToggleButton>:
    text: 'None'
    group: 'basedir'
    on_hacked_state: for c in root.parent.__boxes.children: \
                c.base_direction = root.text
<EditPopup@Popup>:
    size_hint: .8, .8
    text: ''
    BoxLayout:
        orientation: 'vertical'
        TextInput:
            multiline: True
            id: ti
            text: root.text
            cursor_width: 3
        Button:
            size_hint_y: None
            text: 'Close'
            on_press: root.dismiss()
<DemoBox>:
    text: ti.text
    language: ''
    halign: 'auto'
    font_size: '20sp'
    font_context: 'system://'
    base_direction: None
    markup: True
    orientation: 'horizontal'
    padding: '5dp'
    spacing: '5dp'
    size_hint_y: None
    height: lbl.texture_size[1] + 25
    on_text:
        if self.text: ti.text = self.text
    Button:
        text: 'Open'
        size_hint_x: None
        on_press:
            pop = F.EditPopup()
            pop.text = lbl.text
            pop.ids.ti.halign = root.halign
            pop.ids.ti.font_size = root.font_size
            pop.ids.ti.font_context = root.font_context != 'None' \
                                      and root.font_context or None
            pop.ids.ti.base_direction = root.base_direction != 'None' \
                                        and root.base_direction or None
            pop.title = 'Edit: {}'.format(root.language)
            pop.open()
    Label:
        text: root.language
        text_size: self.size
        halign: 'left'
        bold: True
        size_hint_x: None
        width: 150
        halign: 'left'
        valign: 'middle'
        font_size: '15sp'
        color: 1, 1, 0, 1
        canvas.before:
            Color:
                rgba: 1, 1, 1, .5
            Rectangle:
                pos: self.pos
                size: self.size
    Label:
        id: lbl
        halign: root.halign
        text: root.text
        markup: root.markup
        font_context: root.font_context != 'None' and \
                      root.font_context or None
        base_direction: root.base_direction != 'None' and \
                        root.base_direction or None
        font_size: root.font_size
        text_size: self.width, None
        canvas.before:
            Color:
                rgba: 1, 1, 1, .1
            Rectangle:
                pos: self.pos
                size: self.size
    TextInput:
        id: ti
        halign: root.halign
        cursor_width: 3
        font_context: root.font_context != 'None' and root.font_context or None
        base_direction: root.base_direction != 'None' and \
                        root.base_direction or None
        font_size: root.font_size
BoxLayout:
    orientation: 'vertical'
    ScrollView:
        id: sv
        bar_color: [.1, .75, .1, .95]
        bar_inactive_color: [.5, .5, .5, .8]
        bar_width: '20dp'
        BoxLayout:
            id: boxes
            orientation: 'vertical'
            size_hint: None, None
            height: self.minimum_height
            width: sv.width - 25  # don't draw below scrollbar
            DemoBox:
                markup: True
                language: 'Arabic'
                text: 'اَلْحَمْدُ لِلّٰهِ رَبِّ \
                    [color=ff0000]الْعَالَمِينَ\
                    \\nاَلرَّحْ[/color]مٰنِ الرَّحِيمِ'
            DemoBox:
                language: 'Arabic + English'
                text: 'اِيَّاكَ نَعْبُدُ Kivyوَ اِيَّاكَ نَسْتَعِينُ\\nKivy'
            DemoBox:
                language: 'English + Arabic'
                text: 'Kivy\\nاِيَّاكَ نَعْبُدُ وَKivy اِيَّاكَ نَسْتَعِينُ'
            DemoBox:
                language: 'Hebrew'
                text: 'בְּרֵאשִׁ֖ית בָּרָ֣א \
                       \\nאֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃'
            DemoBox:
                language: 'Hebrew + English'
                text: 'בְּרֵאKivyשִׁ֖ית בָּרָ֣א \\nKivy'
            DemoBox:
                language: 'English + Hebrew'
                text: 'Kivy\\nבְּרֵאשִׁ֖יKivyת בָּרָ֣א '
            DemoBox:
                language: 'Chinese'
                text: '你好，这是中文竖排测试。\\n欢迎来到中国北京。'
            DemoBox:
                language: 'Chinese + English'
                text: '你好，这是Kivy中文竖排测试。\\nKivy'
            DemoBox:
                language: 'English + Chinese'
                text: 'Kivy\\n你好，这是中Kivy文竖排测试。'
            DemoBox:
                language: 'Syriac'
                text: 'ܐܬܐܡܘܢ ܥܠܝܡܢ \\nܘܥܠܝܡܬܢ'
            DemoBox:
                language: 'Syriac + English'
                text: 'ܐܬܐܡܘܢ Kivyܥܠܝܡܢ ܘܥܠܝܡܬܢ\\nKivy'
            DemoBox:
                language: 'English + Syriac'
                text: 'Kivyܐܬܐܡܘܢ ܥܠKivyܝܡܢ ܘܥܠܝܡܬܢ\\nKivy'
            DemoBox:
                language: 'Tibetan'
                text: ' འབྲུག་རྒྱལ་ཁབ\\n་འདི་དགའ་ཏོག་ཏོ་ཡོད།'
            DemoBox:
                language: 'Tibetan + English'
                text: ' འ Kivyབྲུག་རྒྱལ་ཁབ\\n་འདི་དགKivyའ་ཏོག་ཏོ་ཡོད།'
            DemoBox:
                language: 'English + Tibetan'
                text: 'Regular letters\\n\
                        འབྲུག་རྒྱལ་ཁབ་འདི་དགའ་Kivyཏོག་ཏོ་ཡོད།'
            DemoBox:
                language: 'Braille (EN)'
                text: '⠊⠀⠉⠁⠝⠀⠑⠁⠞⠀⠛⠇⠁⠎⠎⠀\\n⠁⠝⠙⠀⠊⠞⠀⠙⠕⠑⠎⠝⠞⠀⠓⠥⠗⠞⠀⠍⠑'
            DemoBox:
                language: 'Braille (EN) + English'
                text: '⠊⠀⠉⠁⠝⠀⠑⠁⠞Kivy\\n⠀⠛⠇⠁⠎⠎⠀⠁⠝Kivy⠙⠀⠊⠞⠀⠙⠕⠑⠎⠝⠞⠀⠓⠥⠗⠞⠀⠍⠑'
            DemoBox:
                markup: True
                language: 'Braille (EN) + English'
                text: '⠊⠀⠉⠁⠝⠀⠑⠁⠞Kivy\\n⠀⠛⠇⠁⠎⠎⠀⠁⠝Kivy\
                       ⠙⠀⠊⠞⠀[color=ff0000]⠙⠕⠑⠎⠝⠞⠀⠓⠥⠗⠞⠀⠍⠑[/color]'
    # --------------------------------------- HALIGN
    BoxLayout:
        __boxes: boxes
        orientation: 'horizontal'
        size_hint_y: None
        height: '30dp'
        MenuLabel:
            text: 'set halign ='
        HalignButton:
            text: 'auto'
            state: 'down'
        HalignButton:
            text: 'left'
        HalignButton:
            text: 'center'
        HalignButton:
            text: 'right'
# Not supported by textinput
#        HalignButton:
#            text: 'justify'
    # --------------------------------BASE DIRECTION
    BoxLayout:
        __boxes: boxes
        orientation: 'horizontal'
        size_hint_y: None
        height: '30dp'
        MenuLabel:
            text: 'set base_direction ='
        BaseDirButton:
            text: 'None'
            state: 'down'
        BaseDirButton:
            text: 'ltr'
        BaseDirButton:
            text: 'rtl'
    # --------------------------------- FONT CONTEXT
    BoxLayout:
        __boxes: boxes
        orientation: 'horizontal'
        size_hint_y: None
        height: '30dp'
        MenuLabel:
            text: 'set font_context ='
        ContextButton:
            text: 'None'
        ContextButton:
            text: 'system://'
            state: 'down'
        ContextButton:
            text: 'system://user'
        ContextButton:
            text: 'user'
    # ------------------------------------ FONT SIZE
    BoxLayout:
        __boxes: boxes
        orientation: 'horizontal'
        size_hint_y: None
        height: '30dp'
        MenuLabel:
            text: 'set font_size ='
        FontButton:
            text: '10'
        FontButton:
            text: '20'
            state: 'down'
        FontButton:
            text: '30'
        FontButton:
            text: '40'
        FontButton:
            text: '50'
        FontButton:
            text: '75'
        FontButton:
            text: '100'
#    BoxLayout:
#        orientation: 'horizontal'
#        size_hint_y: None
#        height: '30dp'
#        Button:
#            color: 0, 1, 0, 1
#            text: 'Add font: user'
#        Button:
#            color: 0, 1, 0, 1
#            text: 'Add font: system://user'
#        ToggleButton:
#            text: 'Enable markup'
#            state: 'down'
#            on_state:
#                for c in boxes.children: c.markup = self.state == 'down'
'''))
