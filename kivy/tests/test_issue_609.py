from kivy.tests.common import GraphicUnitTest


class Issue609(GraphicUnitTest):

    def test_markup_pos(self):
        from kivy.uix.label import Label
        from kivy.uix.gridlayout import GridLayout

        lbl = Label(text="TextToTest")
        lbl.bind(text_size=lbl.setter('size'))
        mrkp = Label(text="TextToTest", markup=True)
        mrkp.bind(text_size=mrkp.setter('size'))

        grid = GridLayout(rows=1, size_hint=(1, 1))
        grid.add_widget(lbl)
        grid.add_widget(mrkp)

        self.render(grid, 2)
