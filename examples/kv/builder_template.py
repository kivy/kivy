from kivy.lang import Builder
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

Builder.load_string('''
[BlehItem@BoxLayout]:
    orientation: 'vertical'
    Label:
        text: str(ctx.idx)
    Button:
        text: ctx.word
''')


class BlehApp(App):

    def build(self):
        root = BoxLayout()
        for idx, word in enumerate(('Hello', 'World')):
            wid = Builder.template('BlehItem', **{
                'idx': idx, 'word': word,
            })
            root.add_widget(wid)
        return root

if __name__ == '__main__':
    BlehApp().run()

