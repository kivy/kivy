# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.core.text import Label as CoreLabel
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.lang import Builder
from kivy import Config
__author__ = 'vahid'

CoreLabel.register(
    'FreeFarsi',
    'fonts/FreeFarsi.ttf',
    fn_bold='fonts/FreeFarsiBold.ttf'
)
#
# CoreLabel.register('Tahoma',
#                'fonts/tahoma.ttf',
#                fn_bold='fonts/tahoma-bold.ttf')


Config.set('graphics', 'width', '2096')
Config.set('graphics', 'height', '1424')


LOREM_EN = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras hendrerit purus ac ante suscipit, sit amet condimentum ex dapibus. In aliquam suscipit erat eget sodales. Phasellus sit amet nibh in neque viverra consectetur eget nec neque. Phasellus ut sem quis erat dictum pretium. Morbi ullamcorper leo nulla, et ultricies elit dictum nec. Proin eleifend ligula eget felis tempor efficitur. Duis ornare velit ante, sed tristique ipsum faucibus eu. Curabitur gravida ex pulvinar massa blandit fringilla. Nam eget sem aliquet, dictum urna quis, volutpat nibh. Morbi lobortis dolor viverra velit facilisis, eget tincidunt purus fermentum. Aliquam accumsan velit dui, a congue orci imperdiet non. Curabitur vehicula nisl nec fringilla tempus. Pellentesque ut faucibus risus. Suspendisse rutrum vel nunc ut commodo."

LOREM_FA = "لورم ایپسوم متن ساختگی با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از طراحان گرافیک است. چاپگرها و متون بلکه روزنامه و مجله در ستون و سطرآنچنان که لازم است و برای شرایط فعلی تکنولوژی مورد نیاز و کاربردهای متنوع با هدف بهبود ابزارهای کاربردی می باشد. کتابهای زیادی در شصت و سه درصد گذشته، حال و آینده شناخت فراوان جامعه و متخصصان را می طلبد تا با نرم افزارها شناخت بیشتری را برای طراحان رایانه ای علی الخصوص طراحان خلاقی و فرهنگ پیشرو در زبان فارسی ایجاد کرد. در این صورت می توان امید داشت که تمام و دشواری موجود در ارائه راهکارها و شرایط سخت تایپ به پایان رسد وزمان مورد نیاز شامل حروفچینی دستاوردهای اصلی و جوابگوی سوالات پیوسته اهل دنیای موجود طراحی اساسا مورد استفاده قرار گیرد."


class RTLTextApp(App):

    def build(self):

        Builder.load_string("""
<Label>:
    font_name: 'FreeFarsi'
    font_size: 40
    on_size:
        self.text_size = self.size

<TextInput>:
    font_name: 'FreeFarsi'
    font_size: 40
    on_size:
        self.text_size = self.size
""")

        root = BoxLayout(orientation='horizontal')

        left = BoxLayout(orientation='vertical', size_hint=(.8, 1))
        root.add_widget(left)

        right = BoxLayout(orientation='vertical', size_hint=(.2, 1))
        root.add_widget(right)

        label = Label(text=LOREM_FA, rtl=True, halign='justify')
        left.add_widget(label)

        label_eng = Label(text=LOREM_EN, rtl=False)
        left.add_widget(label_eng)

        inp = TextInput(text=LOREM_FA, rtl=True, halign='right')
        left.add_widget(inp)

        inp2 = TextInput(text=LOREM_EN)
        left.add_widget(inp2)

        # label2 = Label(text=test_text_fa, rtl=True, halign='right')
        # left.add_widget(label2)


        #
        # inp = TextInput(text=test_text_en, rtl=True)
        # left.add_widget(inp)
        #
        # inp2 = TextInput(text=test_text_fa, rtl=True, halign='right')
        # left.add_widget(inp2)
        #
        # inp2 = TextInput(text=test_text_en, rtl=True, halign='right')
        # left.add_widget(inp2)
        #
        # inp3 = TextInput(text=test_text_fa, rtl=True, halign='center')
        # left.add_widget(inp3)
        #
        # inp3 = TextInput(text=test_text_en, rtl=True, halign='center')
        # left.add_widget(inp3)

        # RIGHT

        # label = Label(text=test_text_fa, rtl=True)
        # right.add_widget(label)
        #
        # label2 = Label(text=test_text_fa, rtl=True, halign='right')
        # right.add_widget(label2)
        #
        # inp = TextInput(text=test_text_fa, rtl=True)
        # right.add_widget(inp)
        #
        # inp = TextInput(text=test_text_en, rtl=True)
        # right.add_widget(inp)
        #
        # inp2 = TextInput(text=test_text_fa, rtl=True, halign='right')
        # right.add_widget(inp2)
        #
        # inp2 = TextInput(text=test_text_en, rtl=True, halign='right')
        # right.add_widget(inp2)
        #
        # inp3 = TextInput(text=test_text_fa, rtl=True, halign='center')
        # right.add_widget(inp3)
        #
        # inp3 = TextInput(text=test_text_en, rtl=True, halign='center')
        # right.add_widget(inp3)

        return root


if __name__ == '__main__':
    RTLTextApp().run()
