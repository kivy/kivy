#!/usr/bin/env python

from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.graphics import Color, Line, Rectangle
from kivy.multistroke import GPoint

__all__ = ('HistoryBrowser', 'HistoryItem', 'AddTemplateForm')

class HistoryBrowser(GridLayout):
    def __init__(self, analyzer, **kwargs):
        kwargs.setdefault('rows', 1)
        kwargs.setdefault('cols_minimum', {0:50, 1:150, 2:400})
        super(HistoryBrowser, self).__init__(**kwargs)
        self.analyzer = analyzer

        # Holds the items we pop from analyzer._history, with an extra 
        # HistoryItem attached, so we can access all the original data/scores
        self._gestures = []

        # Is an item selected in the scrollview? None or GestureItem
        self.selected_item = None
        
        # GridLayout to hold HistoryItems in a vertical row, oldest on top
        history = GridLayout(cols=1, size_hint=(None, None), 
            padding=10, spacing=10, width=150)
        history.bind(minimum_height=history.setter('height'))
        self.history = history
        
        # Slider that is linked with the ScrollView to provide instant jump
        scrollbar = Slider(size_hint=(None, 1), width=50, min=0, max=1,
            orientation='vertical')
        scrollbar.value = 0
        scrollbar.bind(value = self.update_scrollview)
        self.scrollbar = scrollbar
        
        # Finally, scrollview to fit the 'history' widget
        scrollv = ScrollView(size_hint=(None, .93), width=150)
        scrollv.add_widget(history)
        scrollv.bind(scroll_y = self.update_slider)
        self.scrollv = scrollv
        
        # Set the scrollbar and clear button on top of each other
        gl = GridLayout(cols=1, rows_minimum={0:50}, size_hint_x=None,
            width=150, size_hint_y=.93)
        clear = Button(text='Clear History', size_hint=(None, None), 
            size=(150, 50))
        clear.bind(on_press = self.erase_history)
        gl.add_widget(clear)
        gl.add_widget(scrollv)
        
        self.add_widget(scrollbar)
        self.add_widget(gl)
        
        self.details = AddTemplateForm(self.analyzer.gdb)

        txt =  "Select a sample on the left to add it as a gesture template.\n"
        txt += "If you don't see any samples, select 'Sample' and draw!\n"
        self.hint = Label(text=txt)
        self.add_widget(self.hint)

    def erase_history(self, btn):
        if self.selected_item:
            self.item_deselect()
        self.history.clear_widgets()
        self._gestures = []
     
    def item_select(self, item):
        if self.selected_item is not None:
            self.selected_item.selected = False
            self.selected_item._trigger_draw()
        else:
            self.remove_widget(self.hint)
            self.add_widget(self.details)

        self.details.load(item)
        self.selected_item = item

    def item_deselect(self, item=None):
        self.selected_item = None
        self.remove_widget(self.details)
        self.add_widget(self.hint)

    def _load_history(self, analyzer=None):
        if analyzer is None:
            analyzer = self.analyzer
        
        while len(analyzer._history):
            g = analyzer._history.popleft()
            g.history_item = HistoryItem(g, size_hint=(None, None), size=(150, 
150))
            g.history_item.bind(on_select = self.item_select)
            g.history_item.bind(on_deselect = self.item_deselect)
            self.history.add_widget(g.history_item)
            self._gestures.append(g)
        
        self._trigger_layout()
        self.scrollv.update_from_scroll()

    # FIXME: is this right?
    def update_scrollview(self, sb, dt):
        self.scrollv.scroll_y = sb.value

    def update_slider(self, sv, dt):
        self.scrollbar.value = sv.scroll_y



class HistoryItem(Widget):
    def __init__(self, g, **kwargs):
        super(HistoryItem, self).__init__(**kwargs)
        self.g = g
        self.selected = False
        self.rect = None
        self._trigger_draw = Clock.create_trigger(self._draw_item, 0)
        self.bind(pos = self._trigger_draw, size=self._trigger_draw)
        self.register_event_type('on_select')
        self.register_event_type('on_deselect')
        
    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return
        self.selected = not self.selected
        self.dispatch(self.selected and 'on_select' or 'on_deselect')
        self._draw_rect(True)

    def _draw_rect(self, clear=False):
        color = self.selected and 1 or self.g.color
        alpha = self.selected and .2 or .045
        if clear and self.rect:
            self.canvas.remove(self.rect)
        with self.canvas:
            Color(color, self.selected and 0 or 1, 1, alpha, mode='hsv')
            self.rect = Rectangle(pos=self.pos, size=self.size)
    
    def on_select(self, *l):
        pass

    def on_deselect(self, *l):
        pass
    
    # FIXME this seems stupid I'm sure there is a much better way
    # (beats me though I suck at these things)
    def _draw_item(self, dt):
        self.canvas.clear()
        g = self.g
        if g.height > g.width:
            to_self = (self.height*0.85) / g.height
        else:
            to_self = (self.width*0.85) / g.width

        for tuid, stroke in g.strokes.items():
            out = []
            for x, y in zip(stroke.points[::2], stroke.points[1::2]):
                x = (x - g.bbox['minx']) * to_self
                w = (g.bbox['maxx'] - g.bbox['minx']) * to_self
                out.append(x + self.pos[0] + (self.width-w)*.85/2)

                y = (y - g.bbox['miny']) * to_self
                h = (g.bbox['maxy'] - g.bbox['miny']) * to_self
                out.append(y + self.pos[1] + (self.height-h)*.85/2)

            with self.canvas:
                Color(g.color,1,1, mode='hsv')
                self.line = Line(points=out, group='historyitem')
        self._draw_rect()

class AddTemplateForm(GridLayout):
    def __init__(self, gdb, hi=None, **kwargs):
        kwargs.setdefault('cols', 1)
        
        super(AddTemplateForm, self).__init__(**kwargs)
        self.gdb = gdb
        self.hi = None
        self.load(hi)
    
    def load(self, hi):
        if hi is None:
            return
        self.hi = hi
        self.clear_widgets()
        self.add_widget(self._settings())

    def _group(self, lbltxt, btntxt=None, r=None):
        if r is None:
            r = ToggleButton(text=btntxt, size_hint=(None, 1), width=150)
        b = BoxLayout(orientation='horizontal', padding=10, spacing=10,
            size_hint_x=None, width=400)
        b.add_widget(Label(text=lbltxt, size_hint=(None,.7), width=400))
        b.add_widget(r)
        return (b, r)
                
    def _settings(self):
        s = BoxLayout(orientation='vertical', padding=10, spacing=10,
            size_hint=(None, None), size=(400, 500))

        best = self.hi.g.recognize_result.best
        if best['name'] is not None:
            txt = "Name: %s (%d strokes)\nScore: %f\nDistance: %f" % (
                best['name'], len(self.hi.g.strokes), best['score'], 
                best['dist'])
        else:
            txt = 'No match (%d strokes)' % (len(self.hi.g.strokes))
        s.add_widget(Label(text=txt, halign='left', size_hint=(1, None)))

        txt = "Use full rotation invariance?\n"
        txt += "In many cases you will have better results with this off\n"
        bl, self.use_bri = self._group(txt, 'Full invariance')
        s.add_widget(bl)

        txt = "Require same number of strokes?\n"
        txt += "This optimization is important to use if suitable.\n"
        txt += "It prevents unneccessary comparison to the template."
        bl, self.use_len = self._group(txt, 'Stroke dependant')
        self.use_len.state = 'down'
        s.add_widget(bl)
        
        txt = "Use the $N algorithm?\n"
        txt += "This will generate permutations of your input, so it is\n"
        txt += "more likely to match different input stroke orders"
        bl, self.use_nd = self._group(txt, 'Use $N')
        self.use_nd.state = 'down'
        s.add_widget(bl)

        txt = "Specify a name for the new gesture"
        bl, self.new_name = self._group(txt, r=TextInput(text='', 
            multiline=False, size_hint=(None, None), width=150, height=30))
        s.add_widget(bl)

        if not hasattr(self.hi.g, 'tpl_added'):
            txt = "Click to add as a new gesture\n"
            b = BoxLayout(orientation='horizontal', padding=10, spacing=10,
                size_hint_x=None, width=400)
            add_btn = Button(text='Add as a Gesture', size_hint=(None, 1), 
                width=400)
            add_btn.bind(on_press = self.add_gesture)
            b.add_widget(add_btn)
            s.add_widget(b)
        else:
            s.add_widget(Label(text='The sample has been added'))

        return s

    def add_gesture(self, *l):
        if not len(self.new_name.text):
            l = GridLayout(cols=1)
            p = Popup(title='Must specify gesture name',
                content=l,
                size_hint=(None, None), size=(400,200), auto_dismiss=True)
            btn = Button(text="Close", size_hint=(1, None), height=40)
            btn.bind(on_press = p.dismiss)
            l.add_widget(Label(text='Please type a gesture name'))
            l.add_widget(btn)
            p.open()

        else:
            cand = []
            for tuid, line in self.hi.g.strokes.items():
                cand.append([ GPoint(*pts) for pts in \
                    zip(line.points[::2], line.points[1::2]) ])

            r_inv = self.use_bri.state   == 'down' and True or False
            use_len = self.use_len.state == 'down' and True or False                                            
            permute = self.use_nd.state  == 'down' and True or False

            self.gdb.add_gesture(self.new_name.text, cand, 
                use_strokelen=use_len,
                rotation_invariant=r_inv,
                permute=permute)
            
            if not permute:
                from kivy.multistroke import Template
                self.gdb.db[-1].templates = [ Template(self.new_name.text,
                    points=[ i for sub in cand for i in sub ], 
                    rotation_invariant=r_inv) ]
            self.hi.g.tpl_added = True
            self.load(self.hi)
        
