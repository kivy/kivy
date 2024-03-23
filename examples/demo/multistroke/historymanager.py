__all__ = ('GestureHistoryManager', 'GestureVisualizer')

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Line
from kivy.properties import ObjectProperty, BooleanProperty

# local libraries
from helpers import InformationPopup
from settings import MultistrokeSettingsContainer

# refuse heap permute for gestures with more strokes than 3
# (you can increase it, but 4 strokes = 384 templates, 5 = 3840)
MAX_PERMUTE_STROKES = 3

Builder.load_file('historymanager.kv')


class GestureHistoryManager(GridLayout):
    selected = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super(GestureHistoryManager, self).__init__(**kwargs)
        self.gesturesettingsform = GestureSettingsForm()
        rr = self.gesturesettingsform.rrdetails
        rr.bind(on_reanalyze_selected=self.reanalyze_selected)
        self.infopopup = InformationPopup()
        self.recognizer = App.get_running_app().recognizer

    def reanalyze_selected(self, *l):
        # recognize() can block the UI with max_gpf=100, show a message
        self.infopopup.text = 'Please wait, analyzing ..'
        self.infopopup.auto_dismiss = False
        self.infopopup.open()

        # Get a reference to the original GestureContainer object
        gesture_obj = self.selected._result_obj._gesture_obj

        # Reanalyze the candidate strokes using current database
        res = self.recognizer.recognize(gesture_obj.get_vectors(),
                                        max_gpf=100)

        # Tag the result with the gesture object (it didn't change)
        res._gesture_obj = gesture_obj

        # Tag the selected item with the updated ProgressTracker
        self.selected._result_obj = res
        res.bind(on_complete=self._reanalyze_complete)

    def _reanalyze_complete(self, *l):
        self.gesturesettingsform.load_visualizer(self.selected)
        self.infopopup.dismiss()

    def add_selected_to_database(self, *l):
        if self.selected is None:
            raise Exception('add_gesture_to_database before load_visualizer?')

        if self.gesturesettingsform.addsettings is None:
            raise Exception('add_gesture_to_database missing addsetings?')

        ids = self.gesturesettingsform.addsettings.ids

        name = ids.name.value.strip()
        if name == '':
            self.infopopup.auto_dismiss = True
            self.infopopup.text = 'You must specify a name for the gesture'
            self.infopopup.open()
            return

        permute = ids.permute.value
        sensitive = ids.orientation_sens.value
        strokelen = ids.stroke_sens.value
        angle_sim = ids.angle_sim.value

        cand = self.selected._result_obj._gesture_obj.get_vectors()

        if permute and len(cand) > MAX_PERMUTE_STROKES:
            t = "Can't heap permute %d-stroke gesture " % (len(cand))
            self.infopopup.text = t
            self.infopopup.auto_dismiss = True
            self.infopopup.open()
            return

        self.recognizer.add_gesture(
            name,
            cand,
            use_strokelen=strokelen,
            orientation_sensitive=sensitive,
            angle_similarity=angle_sim,
            permute=permute)

        self.infopopup.text = 'Gesture added to database'
        self.infopopup.auto_dismiss = True
        self.infopopup.open()

    def clear_history(self, *l):
        if self.selected:
            self.visualizer_deselect()
        self.ids.history.clear_widgets()

    def visualizer_select(self, visualizer, *l):
        if self.selected is not None:
            self.selected.selected = False
        else:
            self.add_widget(self.gesturesettingsform)

        self.gesturesettingsform.load_visualizer(visualizer)
        self.selected = visualizer

    def visualizer_deselect(self, *l):
        self.selected = None
        self.remove_widget(self.gesturesettingsform)

    def add_recognizer_result(self, result, *l):
        '''The result object is a ProgressTracker with additional
        data; in main.py it is tagged with the original GestureContainer
        that was analyzed (._gesture_obj)'''

        # Create a GestureVisualizer that draws the gesture on canvas
        visualizer = GestureVisualizer(result._gesture_obj,
                                       size_hint=(None, None), size=(150, 150))

        # Tag it with the result object so AddGestureForm.load_visualizer
        # has the results to build labels in the scrollview
        visualizer._result_obj = result

        visualizer.bind(on_select=self.visualizer_select)
        visualizer.bind(on_deselect=self.visualizer_deselect)

        # Add the visualizer to the list of gestures in 'history' screen
        self.ids.history.add_widget(visualizer)
        self._trigger_layout()
        self.ids.scrollview.update_from_scroll()


class RecognizerResultLabel(Label):
    '''This Label subclass is used to show a single result from the
    gesture matching process (is a child of GestureHistoryManager)'''
    pass


class RecognizerResultDetails(BoxLayout):
    '''Contains a ScrollView of RecognizerResultLabels, ie the list of
    matched gestures and their score/distance (is a child of
    GestureHistoryManager)'''

    def __init__(self, **kwargs):
        super(RecognizerResultDetails, self).__init__(**kwargs)
        self.register_event_type('on_reanalyze_selected')

    def on_reanalyze_selected(self, *l):
        pass


class AddGestureSettings(MultistrokeSettingsContainer):
    pass


class GestureSettingsForm(BoxLayout):
    '''This is the main content of the GestureHistoryManager, the form for
    adding a new gesture to the recognizer. It is added to the widget tree
    when a GestureVisualizer is selected.'''

    def __init__(self, **kwargs):
        super(GestureSettingsForm, self).__init__(**kwargs)
        self.infopopup = InformationPopup()
        self.rrdetails = RecognizerResultDetails()
        self.addsettings = None
        self.app = App.get_running_app()

    def load_visualizer(self, visualizer):
        if self.addsettings is None:
            self.addsettings = AddGestureSettings()
            self.ids.settings.add_widget(self.addsettings)

        self.visualizer = visualizer
        analysis = self.ids.analysis
        analysis.clear_widgets()
        analysis.add_widget(self.rrdetails)

        scrollv = self.rrdetails.ids.result_scrollview
        resultlist = self.rrdetails.ids.result_list
        resultlist.clear_widgets()

        r = visualizer._result_obj.results

        if not len(r):
            lbl = RecognizerResultLabel(text='[b]No match[/b]')
            resultlist.add_widget(lbl)
            scrollv.scroll_y = 1
            return

        for one in sorted(r.items(), key=lambda x: x[1]['score'],
                          reverse=True):
            data = one[1]
            lbl = RecognizerResultLabel(
                text='Name: [b]' + data['name'] + '[/b]' +
                     '\n      Score: ' + str(data['score']) +
                     '\n      Distance: ' + str(data['dist']))
            resultlist.add_widget(lbl)

        # Make sure the top is visible
        scrollv.scroll_y = 1


class GestureVisualizer(Widget):
    selected = BooleanProperty(False)

    def __init__(self, gesturecontainer, **kwargs):
        super(GestureVisualizer, self).__init__(**kwargs)

        self._gesture_container = gesturecontainer

        self._trigger_draw = Clock.create_trigger(self._draw_item, 0)
        self.bind(pos=self._trigger_draw, size=self._trigger_draw)
        self._trigger_draw()

        self.register_event_type('on_select')
        self.register_event_type('on_deselect')

    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return
        self.selected = not self.selected
        self.dispatch(self.selected and 'on_select' or 'on_deselect')

    # FIXME: This seems inefficient, is there a better way??
    def _draw_item(self, dt):
        g = self._gesture_container
        bb = g.bbox
        minx, miny, maxx, maxy = bb['minx'], bb['miny'], bb['maxx'], bb['maxy']
        width, height = self.size
        xpos, ypos = self.pos

        if g.height > g.width:
            to_self = (height * 0.85) / g.height
        else:
            to_self = (width * 0.85) / g.width

        self.canvas.remove_group('gesture')

        cand = g.get_vectors()
        col = g.color
        for stroke in cand:
            out = []
            append = out.append
            for vec in stroke:
                x, y = vec
                x = (x - minx) * to_self
                w = (maxx - minx) * to_self
                append(x + xpos + (width - w) * .85 / 2)

                y = (y - miny) * to_self
                h = (maxy - miny) * to_self
                append(y + ypos + (height - h) * .85 / 2)

            with self.canvas:
                Color(col[0], col[1], col[2], mode='rgb')
                Line(points=out, group='gesture', width=2)

    def on_select(self, *l):
        pass

    def on_deselect(self, *l):
        pass
