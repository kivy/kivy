__all__ = ('GestureDatabase', 'GestureDatabaseItem')

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty
from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.graphics import Rectangle, Color
from kivy.multistroke import Recognizer

# local libraries
from helpers import InformationPopup


Builder.load_file('gesturedatabase.kv')


class GestureExportPopup(Popup):
    pass


class GestureImportPopup(Popup):
    pass


class GestureDatabaseItem(FloatLayout):
    name = StringProperty('(no name)')
    template_count = NumericProperty(0)
    gesture_list = ListProperty([])

    def __init__(self, **kwargs):
        super(GestureDatabaseItem, self).__init__(**kwargs)
        self.rect = None
        self._draw_trigger = Clock.create_trigger(self.draw_item, 0)
        self.update_template_count()
        self.bind(gesture_list=self.update_template_count)
        self.register_event_type('on_select')
        self.register_event_type('on_deselect')

    def toggle_selected(self, *l):
        self._draw_rect(clear=True)
        if self.ids.select.state == 'down':
            self.dispatch('on_select')
            self.ids.select.text = 'Deselect'
        else:
            self.dispatch('on_deselect')
            self.ids.select.text = 'Select'

    def update_template_count(self, *l):
        tpl_count = 0
        for g in self.gesture_list:
            tpl_count += len(g.templates)
        self.template_count = tpl_count

    def draw_item(self, *l):
        self.ids.namelbl.pos = self.pos
        self.ids.namelbl.y += 90
        self.ids.stats.pos = self.pos
        self.ids.stats.y += 40
        self.ids.select.pos = self.pos
        self._draw_rect()

    def _draw_rect(self, clear=False, *l):
        col = self.ids.select.state == 'down' and 1 or .2
        with self.canvas:
            Color(col, 0, 0, .15)
            if self.rect or clear:
                self.canvas.remove(self.rect)
            self.rect = Rectangle(size=self.size, pos=self.pos)

    def on_select(*l):
        pass

    def on_deselect(*l):
        pass


class GestureDatabase(GridLayout):
    selected_count = NumericProperty(0)
    recognizer = ObjectProperty(None)
    export_popup = ObjectProperty(GestureExportPopup())
    import_popup = ObjectProperty(GestureImportPopup())
    info_popup = ObjectProperty(InformationPopup())

    def __init__(self, **kwargs):
        super(GestureDatabase, self).__init__(**kwargs)
        self.redraw_all = Clock.create_trigger(self._redraw_gesture_list, 0)
        self.export_popup.ids.save_btn.bind(on_press=self.perform_export)
        self.import_popup.ids.filechooser.bind(on_submit=self.perform_import)

    def import_gdb(self):
        self.gdict = {}
        for gesture in self.recognizer.db:
            if gesture.name not in self.gdict:
                self.gdict[gesture.name] = []
            self.gdict[gesture.name].append(gesture)

        self.selected_count = 0
        self.ids.gesture_list.clear_widgets()
        for k in sorted(self.gdict, key=lambda n: n.lower()):
            gitem = GestureDatabaseItem(name=k, gesture_list=self.gdict[k])
            gitem.bind(on_select=self.select_item)
            gitem.bind(on_deselect=self.deselect_item)
            self.ids.gesture_list.add_widget(gitem)

    def select_item(self, *l):
        self.selected_count += 1

    def deselect_item(self, *l):
        self.selected_count -= 1

    def mass_select(self, *l):
        if self.selected_count:
            for i in self.ids.gesture_list.children:
                if i.ids.select.state == 'down':
                    i.ids.select.state = 'normal'
                    i.draw_item()
        else:
            for i in self.ids.gesture_list.children:
                if i.ids.select.state == 'normal':
                    i.ids.select.state = 'down'
                    i.draw_item()

    def unload_gestures(self, *l):
        if not self.selected_count:
            self.recognizer.db = []
            self.ids.gesture_list.clear_widgets()
            self.selected_count = 0
            return

        for i in self.ids.gesture_list.children[:]:
            if i.ids.select.state == 'down':
                self.selected_count -= 1
                for g in i.gesture_list:
#                    if g in self.recognizer.db:  # not needed, for testing
                    self.recognizer.db.remove(g)
                    self.ids.gesture_list.remove_widget(i)

    def perform_export(self, *l):
        path = self.export_popup.ids.filename.text
        if not path:
            self.export_popup.dismiss()
            self.info_popup.text = 'Missing filename'
            self.info_popup.open()
            return
        elif not path.lower().endswith('.kg'):
            path += '.kg'

        self.save_selection_to_file(path)

        self.export_popup.dismiss()
        self.info_popup.text = 'Gestures exported!'
        self.info_popup.open()

    def perform_import(self, filechooser, *l):
        count = len(self.recognizer.db)
        for f in filechooser.selection:
            self.recognizer.import_gesture(filename=f)
        self.import_gdb()
        self.info_popup.text = ("Imported %d gestures.\n" %
                                (len(self.recognizer.db) - count))
        self.import_popup.dismiss()
        self.info_popup.open()

    def save_selection_to_file(self, filename, *l):
        if not self.selected_count:
            self.recognizer.export_gesture(filename=filename)
        else:
            tmpgdb = Recognizer()
            for i in self.ids.gesture_list.children:
                if i.ids.select.state == 'down':
                    for g in i.gesture_list:
                        tmpgdb.db.append(g)
            tmpgdb.export_gesture(filename=filename)

    def _redraw_gesture_list(self, *l):
        for child in self.ids.gesture_list.children:
            child._draw_trigger()
