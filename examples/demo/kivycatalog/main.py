import kivy
kivy.require('1.4.2')
import os
import sys
from kivy.app import App
from kivy.factory import Factory
from kivy.lang import Builder, Parser
from kivy.properties import ObjectProperty, StringProperty
from kivy.config import Config

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.codeinput import CodeInput
from kivy.uix.togglebutton import ToggleButton
from kivy.animation import Animation

CATALOG_ROOT = os.path.dirname(__file__)

Config.set('graphics', 'width', '1024')
Config.set('graphics', 'height', '768')

'''List of classes that need to be instantiated in the factory from .kv files.
'''
CONTAINER_KVS = os.path.join(CATALOG_ROOT, 'container_kvs')
CONTAINER_CLASSES = [c[:-3] for c in os.listdir(CONTAINER_KVS)
    if c.endswith('.kv')]


class MenuButton(ToggleButton):
    pass


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
        '''Get the name of the kv file, a lowercase version of the class
        name.
        '''
        return os.path.join(CONTAINER_KVS, self.__class__.__name__ + '.kv')


for class_name in CONTAINER_CLASSES:
    globals()[class_name] = type(class_name, (Container,), {})


class KivyRenderTextInput(CodeInput):
    def _keyboard_on_key_down(self, window, keycode, text, modifiers):
        self.catalog.screen_manager.get_screen(self.catalog.current_view
            ).content.children[0].last_render = self.text

        super(KivyRenderTextInput, self)._keyboard_on_key_down(
            window, keycode, text, modifiers)


class Catalog(BoxLayout):
    '''Catalog of widgets. This is the root widget of the app. It contains
    a tabbed pain of widgets that can be displayed and a textbox where .kv
    language files for widgets being demoed can be edited.

    The entire interface for the Catalog is defined in kivycatalog.kv,
    although individual containers are defined in the container_kvs
    directory.

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
    menu_view = ObjectProperty()
    menu_select = ObjectProperty()
    menu_code = ObjectProperty()
    current_view = StringProperty("Welcome")

    def __init__(self, **kwargs):
        super(Catalog, self).__init__(**kwargs)
        self.show_kv()

    def show_kv(self, object=None):
        '''Called when an item is selected from the menu. Render the
        kv file for the item and display it.'''
        # if object is not passed, it's initialization, we just need to load
        # the file
        if object:
            self.screen_manager.current = self.current_view = object.text
            if object.state != "down":
                object.state = "down"

        child = self.screen_manager.get_screen(self.current_view).content.children[0]
        if hasattr(child, 'last_render'):
            self.language_box.text = child.last_render
            self.language_box.reset_undo()
        elif hasattr(child, 'kv_file'):
            with open(child.kv_file) as file:
                self.language_box.text = file.read()
            # reset undo/redo history
            self.language_box.reset_undo()

        if object:  # This is a hack; if it's initialization, we don't want to select the button
            self.menu_view._do_press()

    def change_kv(self, object=None):
        '''Called when the view button is clicked or a new view is selected.
         Needs to update the
        interface for the currently active kv widget, if there is one based
        on the kv file the user entered. If there is an error in their kv
        syntax, show a nice popup.'''

        if object.state != "down":
            object.state = "down"
        screen = self.screen_manager.get_screen(self.current_view)
        kv_container = screen.content.children[0]

        try:
            parser = Parser(content=self.language_box.text.encode('utf8'))
            kv_container.clear_widgets()
            widget = Factory.get(parser.root.name)()
            Builder._apply_rule(widget, parser.root, parser.root)
            kv_container.add_widget(widget)
            self.screen_manager.current = self.current_view
        except Exception as e:
            self.show_error(e)

    def show_error(self, e):
        self.info_label.text = str(e)
        self.anim = Animation(top=190.0, opacity=1, d=2, t='in_back') +\
            Animation(top=190.0, d=3) +\
            Animation(top=0, opacity=0, d=2)
        self.anim.start(self.info_label)


class KivyCatalogApp(App):
    '''The kivy App that runs the main root. All we do is build a catalog
    widget into the root.'''
    def build(self):
        return Catalog()


if __name__ == "__main__":
    KivyCatalogApp().run()
