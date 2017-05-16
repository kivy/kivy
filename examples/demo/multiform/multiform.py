# Python related imports
import random
from functools import partial

# Core imports
from kivy.app import App
from kivy.clock import Clock
from kivy.weakproxy import WeakProxy
from kivy.uix.scatter import Scatter
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty, DictProperty
from kivy.properties import NumericProperty, ListProperty
from kivy.properties import ObjectProperty

# Casual widgets
from kivy.uix.button import Button
from kivy.uix.switch import Switch
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput


def get_parent(name=None, parent=None):
    '''A function to seek a widget in parent-children
    tree from bottom up.
    '''
    if not name:
        return
    if name in str(parent):
        return parent
    else:
        return get_parent(name, parent.parent)


class MsgButton(Button):
    def __init__(self, **kwargs):
        '''Parent variable is available after __init__ is
        completed, therefore we schedule a Clock event to
        postprone working with a parent until a next frame.
        '''
        self.app = App.get_running_app()
        super(MsgButton, self).__init__(**kwargs)
        Clock.schedule_once(self.post_init)

    def post_init(self, *args):
        '''Get an instance of Form the widget is in via
        traversing the parent-children tree, because the order
        of children added to a custom layout is randomized.

        Set up an `on_release` binding. It's important
        to notice passing an object of Form to partial, not
        just a string, because partial freezes everything
        in-place. Making this::

            partial(function, string)

        would leave the string unchanged in partial although
        it might change somewhere else during the app cycle.
        '''
        self.form = get_parent('Form', self.parent)
        part = partial(
            self.send_message,
            self.form, 'Ping from %s' % self
        )
        self.bind(on_release=part)

    def send_message(self, form, msg, *args):
        '''If a target Form is available, change its `bottom`.
        '''
        if form.msg_target:
            form.msg_target.ids.bottom.text = msg


class MsgSpinner(Spinner):
    def __init__(self, **kwargs):
        '''Fetch every previously created Form if available
        in a dictionary stored in Area. If not available,
        create a new item of a current Form through assigning
        to a key. This way even an old reference is overwritten.
        '''
        wp = WeakProxy
        self.app = App.get_running_app()
        super(MsgSpinner, self).__init__(**kwargs)
        self.weak_values = self.app.area.weak_values

        for child in self.app.area.children:
            if 'Form' in str(child):
                self.weak_values[str(child.title)] = wp(child)

        self.values = self.weak_values.keys()
        Clock.schedule_once(self.post_init)

    def post_init(self, *args):
        self.form = get_parent('Form', self.parent)

    def on_text(self, *args):
        '''Update a message target if a selected value
        of Spinner changes.
        '''
        self.form.msg_target = self.weak_values[self.text]


class FormItem(Button):
    '''A taskbar-like item storing a reference to Form
    object. On click/tap restores the Form.
    '''
    def __init__(self, area=None, formobj=None, **kwargs):
        super(FormItem, self).__init__(**kwargs)
        self.area = area
        self.formobj = formobj
        self.bind(on_release=self.restore)

    def restore(self, *args):
        '''Restore a Form by adding it as a widget to Area
        as FormItem already has the instance of Form stored
        in `formobj`. The instance is added unchanged.
        '''
        self.area.add_widget(self.formobj)
        self.parent.remove_widget(self)


class Form(Scatter):
    '''A dragable, scalable window-like widget.
    '''
    msg_target = ObjectProperty()
    old_pos = ListProperty([0, 0])
    old_size = ListProperty([0, 0])
    title = StringProperty('My Form')
    default_bottom = StringProperty('Bottom')

    def __init__(self, title='My Form', content=None,
                 bottom='', area=None, **kwargs):

        if not area or not content:
            raise Exception(
                'A Form has to have both area it'
                ' belongs to and widget content!')

        self.area = area
        self.title = title
        super(Form, self).__init__(**kwargs)
        self.ids.container.add_widget(content)

    def minimize(self):
        '''For minimizing we'll need to hide a widget,
        which is handled with `remove_widget`, however
        such an action discards an instance of our Form,
        therefore we'll need to save it somewhere first.

        FormItem takes a direct reference of our Form
        and as there's still a reference, the instance
        won't be collected by garbage collector.
        '''
        formitem = FormItem(text=self.title, area=self.area,
                            formobj=self)

        self.area.ids.formbar.add_widget(formitem)
        self.area.remove_widget(self)

    def maximize(self):
        '''To maximize a form, we'll set its size to
        an Area it's created in.

        `size`, `pos`, `old_size` and `old_pos` are
        ListProperties, and not just casual Python
        lists. By assigning one to another we get
        directly a value, not only a reference.
        '''
        if self.size != self.area.size:
            self.old_size = self.size
            self.old_pos = self.pos
            self.size = self.area.size
            self.pos = [0, self.area.formbar_height]
        else:
            self.size = self.old_size
            self.pos = self.old_pos

    def close(self):
        '''Close a Form and discard any evidence of it.
        The next created Form after closing will continue
        in the count of `total_children`.

        Example: `My Form 1` is closed, a new Form is
        created. The new form will have a title `My Form 1`.
        '''
        self.area.total_children -= 1
        self.area.remove_widget(self)

    def flush_ping(self, *args):
        '''Flush any other text than the default one
        in the bottom part of a Form.
        '''
        if self.ids.bottom.text != self.default_bottom:
            self.ids.bottom.text = self.default_bottom


class Area(FloatLayout):
    '''A widget for placing Forms. Doesn't need to be
    a FloatLayout, but must not restrict position of its
    children or depend on it in any way.
    '''
    total_children = NumericProperty(0)
    formbar_height = NumericProperty(0.05)
    available = ListProperty(
        [CheckBox, MsgButton, MsgSpinner, Switch, TextInput]
    )
    weak_values = DictProperty()

    def __init__(self, **kwargs):
        super(Area, self).__init__(**kwargs)
        self.app = App.get_running_app()
        self.app.area = self

    def create_form(self, *args):
        '''Create a Form with a title "My Form N", where N
        is a count of Forms in the Area and populate the
        Form content with a layout with randomized children.
        '''
        self.total_children += 1
        title = 'My Form %s' % self.total_children
        bottom = str(random.random())
        form = Form(title=title, content=self.pick_child(),
                    bottom=bottom, area=self)
        self.add_widget(form)

    def pick_child(self):
        '''Return a layout of this shape::
            _____________
            |     |_____|
            |     |_____|
            |_____|__|__|

        populated from shuffled `available` list.
        '''
        avail = self.available
        children = random.sample(avail, len(avail))
        box = BoxLayout()

        left = children[0]()
        right = BoxLayout(orientation='vertical')

        up = children[1]()
        mid = children[2]()
        down = BoxLayout()

        down_left = children[3]()
        down_right = children[4]()

        down.add_widget(down_left)
        down.add_widget(down_right)

        right.add_widget(up)
        right.add_widget(mid)
        right.add_widget(down)

        box.add_widget(left)
        box.add_widget(right)
        return box


class MultiForm(App):
    def build(self):
        return Area()

if __name__ == '__main__':
    MultiForm().run()
