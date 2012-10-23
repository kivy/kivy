import kivy
kivy.require('1.4.2')
import os
import sys
from kivy.app import App
from kivy.factory import Factory
from kivy.lang import Builder, Parser, ParserException
from kivy.properties import ObjectProperty
from kivy.config import Config

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

print Config.get('graphics', 'width')

Config.set('graphics', 'width', '1024')
Config.set('graphics', 'height', '768')

'''List of classes that need to be instantiated in the factory from .kv files.
'''
CONTAINER_CLASSES = [c[:-3] for c in os.listdir('container_kvs')
    if c.endswith('.kv')]


class Container(BoxLayout):
    '''A container is essentially a class that loads its root from a known
    .kv file.

    The name of the .kv file is taken from the Container's class.
    We can't just use kv rules because the class may be edited
    in the interface and reloaded by the user.
    See :meth: change_kv where this happens.
    '''

    def __init__(self, **kwargs):
        super(Container, self).__init__(**kwargs)
        parser = Parser(content=file(self.kv_file).read())
        widget = Factory.get(parser.root.name)()
        Builder._apply_rule(widget, parser.root, parser.root)
        self.add_widget(widget)

    @property
    def kv_file(self):
        '''Get the name of the kv file, a lowercase version of the class name.'''
        return os.path.join('container_kvs',
            self.__class__.__name__ + ".kv")


for class_name in CONTAINER_CLASSES:
    globals()[class_name] = type(class_name, (Container,), {})


class KivyRenderTextInput(TextInput):
    def _keyboard_on_key_down(self, window, keycode, text, modifiers):
        is_osx = sys.platform == 'darwin'
        # Keycodes on OSX:
        ctrl, cmd = 64, 1024
        key, key_str = keycode

        if text and not key in (self.interesting_keys.keys() + [27]):
            # This allows *either* ctrl *or* cmd, but not both.
            if modifiers == ['ctrl'] or (is_osx and modifiers == ['meta']):
                if key == ord('s'):
                    self.parent.parent.parent.change_kv(True)
                    return

        super(KivyRenderTextInput, self)._keyboard_on_key_down(
            window, keycode, text, modifiers)


class Catalog(BoxLayout):
    '''Catalog of widgets. This is the root widget of the app. It contains
    a tabbed pain of widgets that can be displayed and a textbox where .kv
    language files for widgets being demoed can be edited.

    The entire interface for the Catalog is defined in kivycatalog.kv, although
    individual containers are defined in the container_kvs directory.

    To add a container to the catalog,
    first create the .kv file in container_kvs
    The name of the file (sans .kv) will be the name of the widget available
    inside the kivycatalog.kv
    Finally modify kivycatalog.kv to add an AccordionItem
    to hold the new widget.
    Follow the examples in kivycatalog.kv to ensure the item
    has an appropriate id and the class has been referenced.

    You do not need to edit any python code, just .kv language files!
    '''
    language_box = ObjectProperty()
    screen_manager = ObjectProperty()

    def __init__(self, **kwargs):
        super(Catalog, self).__init__(**kwargs)
        self.show_kv(None)

    def show_kv(self, object):
        '''Called when an accordionitem is collapsed or expanded. If it
        was expanded, we need to show the .kv language file associated with
        the newly revealed container.'''

        # if object is not passed, it's initialization, we just need to load
        # the file
        if object:
            # one button must always be pressed, even if user presses it again
            if object.state == "normal":
                object.state = "down"

            self.screen_manager.current = object.text

        with open(self.screen_manager.current_screen.content.children[
                    0].kv_file) as file:
            self.language_box.text = file.read()

    def change_kv(self, button):
        '''Called when the update button is clicked. Needs to update the
        interface for the currently active kv widget, if there is one based
        on the kv file the user entered. If there is an error in their kv
        syntax, show a nice popup.'''
        kv_container = self.screen_manager.current_screen.content.children[0]
        try:
            parser = Parser(content=self.language_box.text.encode('utf8'))
            kv_container.clear_widgets()
            widget = Factory.get(parser.root.name)()
            Builder._apply_rule(widget, parser.root, parser.root)
            kv_container.add_widget(widget)
        except (SyntaxError, ParserException) as e:
            content = Label(text=str(e), text_size=(350, None))
            popup = Popup(title="Parse Error in Kivy Language Markup",
                content=content, text_size=(350, None),
                size_hint=(None, None), size=(400, 400))
            popup.open()
        except:
            import traceback
            traceback.print_exc()
            popup = Popup(title="Boom",
                content=Label(text="Something horrible happened while parsing your Kivy Language", text_size=(350, None)),
                text_size=(350, None),
                size_hint=(None, None), size=(400, 400))
            popup.open()


class KivyCatalogApp(App):
    '''The kivy App that runs the main root. All we do is build a catalog
    widget into the root.'''
    def build(self):
        return Catalog()


if __name__ == "__main__":
    KivyCatalogApp().run()
