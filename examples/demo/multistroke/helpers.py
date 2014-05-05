__all__ = ('InformationPopup', )

from kivy.uix.popup import Popup
from kivy.properties import StringProperty
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.clock import Clock

Builder.load_string('''
<InformationPopup>:
    auto_dismiss: True
    size_hint: None, None
    size: 400, 200
    on_open: root.dismiss_trigger()
    title: root.title
    Label:
        text: root.text
''')


class InformationPopup(Popup):
    title = StringProperty('Information')
    text = StringProperty('')

    def __init__(self, time=1.5, **kwargs):
        super(InformationPopup, self).__init__(**kwargs)
        self.dismiss_trigger = Clock.create_trigger(self.dismiss, time)


Factory.register('InformationPopup', cls=InformationPopup)
