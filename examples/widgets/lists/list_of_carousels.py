from kivy.base import runTouchApp
from kivy.binding import DataBinding
from kivy.controllers.listcontroller import ListController
from kivy.lang import Builder
from kivy.models import SelectableDataItem
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.carousel import Carousel
from kivy.uix.label import Label
from kivy.uix.listview import SelectableView
from kivy.uix.listview import ListView

Builder.load_string('''
''')


class OrganismGroupListItem(SelectableView, BoxLayout):

    carousel = ObjectProperty(None)

    def __init__(self, **kw):
        super(OrganismGroupListItem, self).__init__(**kw)

        self.add_widget(Label(text=kw['text']))

        self.carousel = Carousel()

        for organism in kw['organisms']:
            self.carousel.add_widget(CarouselItem(list_item=self, text=organism))

        self.add_widget(self.carousel)

    def on_touch_up(self, touch):
        self.carousel.on_touch_up(touch)
        return super(OrganismGroupListItem, self).on_touch_up(touch)

    def carousel_item_touched(self, touch):
        super(OrganismGroupListItem, self).dispatch('on_release')


class CarouselItem(Button):

    list_item = ObjectProperty(None)

    def on_touch_up(self, touch):
        self.list_item.carousel_item_touched(touch)


class CarouselDataItem(SelectableDataItem):

    def __init__(self, **kw):
        super(CarouselDataItem, self).__init__(**kw)
        self.text = kw['text']
        self.organisms = kw['organisms']


data = [CarouselDataItem(
            text='Mammals:',
            organisms=['cat', 'dog', 'chimpanzee', 'giraffe', 'mouse']),
        CarouselDataItem(
            text='Reptiles:',
            organisms=['chameleon', 'monitor', 'dinosaur', 'snake', 'turtle']),
        CarouselDataItem(
            text='Fish:',
            organisms=['barracuda', 'tuna', 'perch', 'piranha', 'bass']),
        CarouselDataItem(
            text='Mollusks:',
            organisms=['clam', 'snail', 'chiton', 'oyster', 'scallop']),
        CarouselDataItem(
            text='Dinosaurs:',
            organisms=['carnosaur', 'dromeosaur', 'ceratopsian', 'bird', 'hadrosaur']),
        CarouselDataItem(
            text='Angiosperms:',
            organisms=['oak', 'rose', 'corn', 'lilac', 'petunia'])]

converter = lambda x, d: dict(text=d.text,
                              size_hint_y=None,
                              height=75,
                              organisms=d.organisms)

controller = ListController(data=data,
                            selection_mode='single')


def selection_changed(*args):
    print 'selection changed', args

list_view = ListView(data_binding=DataBinding(source=controller),
                     args_converter=converter,
                     list_item_class=OrganismGroupListItem,)

if __name__ == '__main__':
    runTouchApp(list_view)
