#!/usr/bin/kivy
'''
Kivy Catalog
============

The Kivy Catalog viewer showcases demonstrations of widgets available in Kivy
and allows interactive editing of kivy language code to get immediate
feedback. You should see a two panel screen with controls across the top.
The left pane contains kivy (.kv) code, and the right pane is that code
rendered. When you edit the left pane, the 'Render Now' button will turn
red until you pause for a moment and then the edited .kv code will be
rendered in the right pane. Across the top, the spinner on
the left jumps through categories of items while the spinner on the right
lists each individual item. The catalog contains dozens of .kv examples
controlling different widgets and layouts.

The catalog's interface is set in the file kivycatalog.kv, while the
interfaces for each menu option are set in containers_kvs directory. To
add a new .kv file to the Kivy Catalog, add a .kv file into the container_kvs
directory. If you want the .kv file in a particular category, name it
'MyCategoryName__MyMenuName.kv'.

'''
import kivy
kivy.require('1.4.2')
import os
import sys
from kivy.app import App
from kivy.factory import Factory
from kivy.lang import Builder, Parser, ParserException
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.config import Config
from kivy.compat import PY2

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.codeinput import CodeInput
from kivy.animation import Animation
from kivy.clock import Clock
from glob import glob
import re

#Config.set('graphics', 'width', '1024')
#Config.set('graphics', 'height', '768')


class KivyRenderTextInput(CodeInput):
    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        ''' Handle ctrl-s (or Meta for OS/X) to re-render '''
        is_osx = sys.platform == 'darwin'
        # Keycodes on OSX:
        ctrl, cmd = 64, 1024
        key, key_str = keycode

        if text and not key in (list(self.interesting_keys.keys()) + [27]):
            # This allows *either* ctrl *or* cmd, but not both.
            if modifiers == ['ctrl'] or (is_osx and modifiers == ['meta']):
                if key == ord('s'):
                    self.catalog.change_kv(True)
                    return

        return super(KivyRenderTextInput, self).keyboard_on_key_down(
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
    current_render = ObjectProperty()
    need_reload = BooleanProperty()  # render synced with language
    category_spinner = ObjectProperty()
    name_spinner = ObjectProperty()

    def __init__(self, infos, **kwargs):
        self.infos = infos
        self.categories = Info.get_categories(infos)
        self.category_list = sorted(set(self.categories.values()))
        self.previous_text = ''
        self.previous_index = 0

        super(Catalog, self).__init__(**kwargs)
        # for info in infos:
        #    c = Container(kv_file=info.fullname, name=info.name)
        #    self.screen_manager.add_widget(c)
        self.show_kv()

    def guess_index(self, name, default=None):
        ''' return index into infos array of the name. If there
        are two copies of the name in the index, pick one. If the name
        isn't in the infos array, return default.
        '''
        info = [index for index, inf in enumerate(self.infos)
                if inf.name.lower() == name.lower()]
        if info:
            return info[0]   # TODO: keep track of last index to guess better
            # guessing only needed for two or more identically named items.
        else:
            return default

    def show_kv(self, name=None, category=None, prev=None, next=None):
        ''' Called when a different kv file is selected. When selected,
        the .kv file is loaded from disk.

        One or zero of the parameters will specify which kv file is
        selected.
        '''

        if name is not None:
            index = self.guess_index(name, default=0)
        elif category is not None:
            index = min([i for i, info in enumerate(self.infos)
                         if info.category == category])
        elif prev is not None:
            index = (self.previous_index - 1) % len(self.infos)
        elif next is not None:
            index = (self.previous_index + 1) % len(self.infos)
        else:
            index = 0

        info = self.infos[index]
        self.previous_index = index
        self.category_spinner.text = info.category
        self.name_spinner.text = info.name

        with open(info.fullname, 'rb') as f:
            self.language_box.text = f.read().decode('utf8')
        Clock.unschedule(self.change_kv)
        self.change_kv()
        self.language_box.reset_undo()

    def schedule_reload(self):
        ''' if the language_box text changed since last called, note a
        reload is needed and schedule one for a couple seconds from now.
        '''

        txt = self.language_box.text
        if txt == self.previous_text:
            return
        self.need_reload = True
        if self.auto_reload:
            self.previous_text = txt
            Clock.unschedule(self.change_kv)
            Clock.schedule_once(self.change_kv, 2)

    def change_kv(self, *_):
        ''' Called to rerender the widget, e.g., when the update button
        is clicked, the update timer clicks, or the user selects a new
        screen. It rerenders the widget from the language_box text.
        If there is an error in the kv
        syntax, show a nice popup.'''

        txt = self.language_box.text
        kv_container = self.current_render
        try:
            parser = Parser(content=txt)
            kv_container.clear_widgets()
            widget = Factory.get(parser.root.name)()
            Builder._apply_rule(widget, parser.root, parser.root)
            kv_container.add_widget(widget)
            self.need_reload = False
        except (SyntaxError, ParserException) as e:
            self.show_error(e)
            self.need_reload = True
        except Exception as e:
            self.show_error(e)
            self.need_reload = True

    def show_error(self, e):
        self.info_label.text = str(e)
        self.anim = Animation(top=190.0, opacity=1, d=2, t='in_back') +\
            Animation(top=190.0, d=3) +\
            Animation(top=0, opacity=0, d=2)
        self.anim.start(self.info_label)


class Info():
    ''' info on one named screen and its associated .kv file '''

    def __init__(self, filename):
        self.fullname = filename
        self.base = os.path.basename(filename)
        pat = r"(?:(.+)__)?(.*)\.kv"
        m = re.match(pat, self.base)
        assert m is not None, "File name must end in .kv"
        g = m.groups()
        self.demo_name = g[1]
        self.category = g[0] if g[0] is not None else "Other"
        self.name = self.demo_name
        self.name = re.sub('_', ' ', self.name)
        # add space between camel case words)
        self.name = re.sub(r'([^ ])([A-Z][a-z])', r'\1 \2', self.name)
        print "name is ", self.name

    @classmethod
    def yield_kv_filenames(cls, globs):
        ''' yield each filename named by the globs given or by directories
        named in those globs. '''
        for g in globs:
            glob_list = glob(g)
            for fn in glob_list:
                if os.path.isdir(fn):
                    for filename in os.listdir(fn):
                        fullname = os.path.join(fn, filename)
                        if (os.path.isfile(fullname) and
                                filename.endswith('.kv')):
                            yield fullname
                elif os.path.isfile(fn) and fn.endswith('.kv'):
                    yield fn

    @classmethod
    def get_infos(cls, *globs):
        ''' takes filenames, directory names, and names with wildcards (globs)
        and returns an array of info[] with an item for each filename passed.
        '''
        infos = []
        for filename in cls.yield_kv_filenames(globs):
            if filename in [i.fullname for i in infos]:
                continue  # exact filename was specified more than once
            info = cls(filename)
            infos.append(info)
            print "Found ", filename
        return sorted(infos, key=lambda x: x.base)

    @classmethod
    def get_default_infos(cls):
        kvdir = os.path.join(os.path.dirname(__name__), 'container_kvs')
        infos = cls.get_infos(kvdir)
        return infos

    @classmethod
    def get_categories(cls, infos):
        ''' returns a dict of [fullname] = category name for infos given. '''
        categories = {}
        for info in infos:
            categories[info.fullname] = info.category
        return categories


class KivyCatalogApp(App):
    '''The kivy App that runs the main root. All we do is build a catalog
    widget into the root.'''

    def build(self):
        infos = Info.get_default_infos()
        return Catalog(infos)

    def on_pause(self):
        return True

if __name__ == "__main__":

    Info.get_infos('container_kvs', 'container_kvs/TextContainer.kv')
    KivyCatalogApp().run()
