#!/usr/bin/env python
from kivy.clock import Clock
from kivy.uix.gridlayout import GridLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView
from kivy.graphics import Rectangle, Color
from kivy.multistroke import Recognizer

__all__ = ('GestureBrowser', 'GestureItem')

class GestureItem(FloatLayout):
    def __init__(self, name, glist, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (120, 130))
        super(GestureItem, self).__init__(**kwargs)

        self.glist = glist
        self.name = name
        self.rect = None
        
        self.head = Label(text=name, size_hint=(1, None), height=40,
            font_size=14, color=(1, 0, 0, 1))

        tpl_count = 0
        for g in glist:
            tpl_count += len(g.templates)
        txt = "%d gestures\n%d templates" % (len(glist), tpl_count)
        self.stat = Label(text=txt, size_hint=(1, None), height=60)
        
        self.select = ToggleButton(text='select', size_hint=(None, None), 
            size=(120, 30))
        self.select.bind(state = self.toggle_item)

        self._trigger_draw = Clock.create_trigger(self._draw_item, 0)
        self.bind(pos=self._trigger_draw, size=self._trigger_draw)

        self.add_widget(self.head)
        self.add_widget(self.stat)
        self.add_widget(self.select)
        
        self.register_event_type('on_select')
        self.register_event_type('on_deselect')

    def on_select(*l):
        pass
    
    def on_deselect(*l):
        pass
        
    def _draw_rect(self, clear=False, *l):
        col = .2

        if self.select.state == 'down':
            col = 1
        with self.canvas:
            Color(col,0,0,.15)
            if self.rect or clear:
                self.canvas.remove(self.rect)
            self.rect = Rectangle(size=self.size, pos=self.pos)

    def toggle_item(self, btn, state):
        self._draw_rect(clear=True)
        self.dispatch(state == 'down' and 'on_select' or 'on_deselect')
        
    def _draw_item(self, *l):
        self.head.pos = self.pos
        self.head.y += 90
        self.stat.pos = self.pos
        self.stat.y += 40
        self.select.pos = self.pos
        self._draw_rect()


class GestureBrowser(GridLayout):
    def __init__(self, gdb, **kwargs):
        kwargs.setdefault('rows', 1)
        kwargs.setdefault('spacing', 10)
        kwargs.setdefault('padding', 10)
        kwargs.setdefault('cols_minimum', {0:200})
        super(GestureBrowser, self).__init__(**kwargs)

        self._selected = 0
        self.gdb = gdb
        self.menu = self._setup_menu()
    
    def import_gdb(self):
        self.gdict = {}

        for gesture in self.gdb.db:
            if gesture.name not in self.gdict:
                self.gdict[gesture.name] = []
            self.gdict[gesture.name].append(gesture)

        l = StackLayout(spacing=10, padding=10, size_hint=(1, None))
        l.bind(minimum_height=l.setter('height'))
                
        import string
        self.gitems = ScrollView()
        for k in sorted(self.gdict, key=string.lower):
            gitem = GestureItem(k, self.gdict[k])
            gitem.bind(on_select = self.select_item)
            gitem.bind(on_deselect = self.deselect_item)
            self.gitems.bind(scroll_y = gitem._trigger_draw)
            l.add_widget(gitem)
                
        self.itemlayout = l
        self.gitems.add_widget(l)
        self.clear_widgets()
        self.add_widget(self.menu)
        self.add_widget(self.gitems)

    def select_item(self, *l):
        self._selected += 1
        self._update_buttons()

    def deselect_item(self, *l):
        self._selected -= 1
        self._update_buttons()

    def save_selection_to_file(self, filename, *l):
        if not self._selected:
            self.gdb.export_gesture(filename=filename)
        else:
            tmpgdb = Recognizer()
            for i in self.itemlayout.children:
                if i.select.state == 'down':
                    for g in i.glist:
                        tmpgdb.db.append(g)
            tmpgdb.export_gesture(filename=filename)
            
    def _mass_select(self, btn, *l):
        if self._selected:
            for i in self.itemlayout.children:
                if i.select.state == 'down':
                    i.select.state = 'normal'
                i._draw_item()
        else:
            for i in self.itemlayout.children:
                if i.select.state == 'normal':
                    i.select.state = 'down'
                i._draw_item()

    def _load_gestures(self, btn, *l):
        from os import getcwd
        fc = FileChooserListView(size_hint=(None, None), size=(400, 380), 
            filters=['*.kg'], path=getcwd())

        p = Popup(title='', auto_dismiss=True,
            content=fc, size_hint=(None, None), size=(450,400))

        def load_file(fc, files, *l):
            count = len(self.gdb.db)
            for f in files:
                self.gdb.import_gesture(filename=f)
            txt = "Loaded %d gestures.\n" % (len(self.gdb.db) - count)
            txt += "(Click outside the popup to close it)"
            self.import_gdb()
            l = Label(text=txt)
            p.content = l
        
        fc.bind(on_submit = load_file)

        p.open()
        
    def _unload_gestures(self, btn, *l):
        if not self._selected:
            self.gdb.db = []
            self.itemlayout.clear_widgets()
            self._update_buttons()
            self._selected = 0
            return

        for i in self.itemlayout.children[:]:
            for g in i.glist:
                if i.select.state == 'down':
                    if g in self.gdb.db: # not needed, for testing
                        self.gdb.db.remove(g)
                    self._selected -= 1
                    self.itemlayout.remove_widget(i)
        
        self._update_buttons()

    def _export_gestures(self, btn, *l):
        l = GridLayout(cols=1, rows_minimum={0:100}, 
            spacing=10, padding=10)
            
        txt = "The extension .kg is appended automatically.\n"
        txt += "The file is saved to the current working directory, unless\n"
        txt += "you specify an absolute path"
        label = Label(text=txt)
        l.add_widget(label)
        
        filename = TextInput(text='', multiline=False, size_hint=(1, None),
            height=40)
        l.add_widget(filename)
        
        do_save = Button(text='Save it!', size_hint=(1, None), height=45)
        cancel  = Button(text='Cancel', size_hint=(1, None), height=45)
        l.add_widget(do_save)
        l.add_widget(cancel)
        
        p = Popup(title='Specify filename', auto_dismiss=True,
            content=l, size_hint=(None, None), size=(400,400))

        def confirm_export(*largs):
            if filename.text == '':
                label.text = 'You must specify a filename for export'
                return
            else:
                self.save_selection_to_file(filename.text + '.kg')
                l.clear_widgets()
                label.text = 'Gestures exported'
                cancel.text = 'Close'
                l.add_widget(label)
                l.add_widget(cancel)
                
        do_save.bind(on_press = confirm_export)
        cancel.bind(on_press = p.dismiss)
        p.open()
            
    def _setup_menu(self):
        self.select = Button(text='Select all', size_hint_y=None, height=100)
        self.select.bind(on_press = self._mass_select)

        self.save = Button(text='Save all', size_hint_y=None, height=100)
        self.save.bind(on_press = self._export_gestures)
        
        self.nuke = Button(text='Unload all', size_hint_y=None, height=100)
        self.nuke.bind(on_press = self._unload_gestures)

        self.load = Button(text='Load from file', size_hint_y=None, height=100)
        self.load.bind(on_press = self._load_gestures)
        
        l = GridLayout(cols=1, size_hint=(None, 1), width=200, spacing=10, 
            padding=10)

        for w in (self.select, self.save, self.nuke, self.load):
           l.add_widget(w)

        return l

    def _update_buttons(self):
        if not self._selected:
            self.save.text = 'Save all'
            self.nuke.text = 'Unload all'
            self.select.text = 'Select all'
        else:
            self.save.text = 'Save %d gestures' % (self._selected)
            self.nuke.text = 'Unload %d gestures' % (self._selected)
            self.select.text = 'Deselect all'

