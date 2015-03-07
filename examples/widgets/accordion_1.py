'''
Accordion Widget Use
====================

This uses of the accordion widget to show a large amount of text. You should
see folds with the word 'Title' along the left and, because the last fold
is selected, the words "Very big content - page 4" along the right. Clicking
on the different folds collapse the current fold and expand the clicked upon
fold.
'''

from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.label import Label
from kivy.app import App


class AccordionApp(App):
    def build(self):
        root = Accordion()
        for x in range(5):
            item = AccordionItem(title='Title %d' % x)
            item.add_widget(Label(
                text='Very big content - page %d\n' % x * 10))
            root.add_widget(item)
        return root

if __name__ == '__main__':
    AccordionApp().run()
