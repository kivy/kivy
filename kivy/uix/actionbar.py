'''
ActionBar
=========

..versionadded:: 1.8.0

.. image:: images/actionbar.jpg
    :align: right

ActionBar widget is like Andriod's ActionBar, where items are stacked
horizontally.

The :class:`ActionBar` will contain one :class:`ActionView` and many
:class:`ContextualActionView`.
:class:`ActionView` will contain :class:`ActionPrevious` having title,
app_icon and previous_icon properties. :class:`ActionView` will contain
subclasses of :class:`ActionItem`. Some of predefined are :class:`ActionButton`,
:class:`ActionToggleButton`, :class:`ActionCheck`, :class:`ActionSeparator`
and :class:`ActionGroup`.
:class:`ActionGroup` is used to display :class:`ActionItem` in a Group.
:class:`ActionView` will always display :class:`ActionGroup` after other
:class:`ActionItem`s.
:class:`ActionView` will contain :class:`ActionOverflow`.
:class:`ContextualActionView` is a subclass of :class:`ActionView`.
'''

__all__ = ('ActionBarException', 'ActionItem', 'ActionButton',
           'ActionToggleButton', 'ActionCheck', 'ActionSeparator',
           'ActionDropDown', 'ActionGroup', 'ActionOverflow',
           'ActionView', 'ContextualActionView', 'ActionBar')

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.properties import ObjectProperty, NumericProperty, \
    BooleanProperty, StringProperty, ListProperty, OptionProperty
from kivy.uix.spinner import Spinner
from kivy.graphics import Canvas
from kivy.core.image import Image
from functools import partial
from kivy.config import Config


class ActionBarException(Exception):
    '''ActionBarException class
    '''
    pass


class ActionItem(Widget):
    '''ActionItem class, an abstract class for all ActionVar widgets. To create
       a custom widget for ActionBar, custom widget should inherit from this
       class. See module documentation for more information
    '''

    minimum_width = NumericProperty('90sp')
    '''Minimum Width required by an ActionItem.

       :data:`minimum_width` is a :class:`~kivy.properties.NumericProperty`
       default to '90sp'.
    '''

    important = BooleanProperty(False)
    '''Determines if ActionItem is important or not.

       :data:`important` is a :class:`~kivy.properties.BooleanProperty`
       default to False.
    '''

    inside_group = BooleanProperty(False)
    '''(internal) Determines, if ActionItem is displayed inside
       ActionGroup or not

       :data:`inside_group` is a :class:`~kivy.properties.BooleanProperty`
       default to False.
    '''

    background_normal = StringProperty(
        'atlas://data/images/defaulttheme/action_item')
    '''Background image of the ActionItem used for default graphical
       representation, when ActionItem is not pressed.

       :data:`background_normal` is a :class:`~kivy.properties.StringProperty`,
       default to 'atlas://data/images/defaulttheme/action_item'.
    '''

    background_down = StringProperty(
        'atlas://data/images/defaulttheme/action_item_down')
    '''Background image of the ActionItem used for default graphical
       representation, when ActionItem is pressed.

       :data:`background_down` is a :class:`~kivy.properties.StringProperty`,
       default to 'atlas://data/images/defaulttheme/action_item_down'.
    '''


class ActionButton(ActionItem, Button):
    '''ActionButton class, see module documentation for more information.
    '''
    pass


class ActionPrevious(ActionButton):
    '''ActionPrevious class, see module documentation for more information.
    '''

    app_icon = StringProperty(
        Config.get('kivy', 'window_icon'))
    '''Application icon for the ActionView.

       :data:`app_icon` is a :class:`~kivy.properties.StringProperty`,
       default to window icon if set otherwise 'data/logo/kivy-icon-32'.
    '''

    previous_image = StringProperty(
        'atlas://data/images/defaulttheme/previous_normal')
    '''Image for 'previous' ActionButton for default graphical representation.

       :data:`previous_image` is a :class:`~kivy.properties.StringProperty`,
       default to 'previous_normal'.
    '''

    title = StringProperty('')
    '''Title for ActionView.

       :data:`title` is a :class:`~kivy.properties.StringProperty`,
       default to ''.
    '''

    def __init__(self, **kwargs):
        super(ActionPrevious, self).__init__(**kwargs)
        if not self.app_icon:
            self.app_icon = 'data/logo/kivy-icon-32'


class ActionToggleButton(ActionItem, ToggleButton):
    '''ActionToggleButton class, see module documentation for more information.
    '''
    pass


class ActionCheck(ActionItem, CheckBox):
    '''ActionCheck class, see module documentation for more information.
    '''
    pass


class ActionSeparator(ActionItem):
    '''ActionSeparator class, see module documentation for more information.
    '''

    background_image = StringProperty(
        'atlas://data/images/defaulttheme/separator')
    '''Background image of separator for default graphical representation.

       :data:`background_image` is a :class:`~kivy.properties.StringProperty`,
       default to 'separator'.
    '''


class ActionDropDown(DropDown):
    '''ActionDropDown class, see module documentation for more information.
    '''
    pass


class ActionGroup(Spinner, ActionItem):
    '''ActionGroup class, , see module documentation for more information.
    '''

    use_separator = BooleanProperty(False)
    '''Whether to use separator after before this group or not.

       :data:`use_separator` is a :class:`~kivy.properties.BooleanProperty`,
       default to False.
    '''

    separator_image = StringProperty(
        'atlas://data/images/defaulttheme/separator')
    '''Background Image for ActionSeparator in ActionView.

       :data:`separator_image` is a :class:`~kivy.properties.StringProperty`,
       default to 'separator'.
    '''

    separator_width = NumericProperty(1)
    '''Width of ActionSeparator in ActionView.

       :data:`separator_width` is a :class:`~kivy.properties.NumericProperty`,
       default to 1.
    '''

    mode = OptionProperty('normal', options=('normal', 'spinner'))
    '''Sets current mode of ActionGroup. If mode is 'normal' then ActionGroup
       children will be displayed normally when there is enough space. If mode
       is 'spinner', then AcionGroup will be displayed even if there is enough
       space.

       :data:`mode` is a :class:`~kivy.properties.OptionProperty`,
       default to 'normal'.
    '''

    def __init__(self, **kwargs):
        self.list_action_item = []
        super(ActionGroup, self).__init__(**kwargs)
        self.dropdown_cls = ActionDropDown

    def add_widget(self, item):
        if isinstance(item, ActionSeparator):
            super(ActionGroup, self).add_widget(item)
            return

        if not isinstance(item, ActionItem):
            raise ActionBarException('ActionGroup only accepts ActionItem')

        self.list_action_item.append(item)

    def show_group(self):
        self.clear_widgets()
        for item in self.list_action_item:
            item.inside_group = True
            self._dropdown.add_widget(item)

    def _build_dropdown(self, *largs):
        if self._dropdown:
            self._dropdown.dismiss()
            self._dropdown = None
        self._dropdown = self.dropdown_cls()

    def _update_dropdown(self, *largs):
        pass

    def _toggle_dropdown(self, *largs):
        self.is_open = not self.is_open
        self._dropdown.size_hint_x = None
        self._dropdown.width = max([self.width,
                                    self.list_action_item[0].minimum_width])
        for item in self.list_action_item:
            item.size_hint_y = None
            item.height = max([self.height, '48sp'])

    def clear_widgets(self):
        self._dropdown.clear_widgets()


class ActionOverflow(ActionGroup):
    '''ActionOverflow class, see module documentation for more information.
    '''

    overflow_image = StringProperty(
        'atlas://data/images/defaulttheme/overflow')
    '''Image to be used as Overflow Image.

      :data:`overflow_image` is an :class:`~kivy.properties.ObjectProperty`,
       default to 'overflow'.
    '''

    pass


class ActionView(BoxLayout):
    '''ActionView class, see module documentation for more information.
    '''

    action_previous = ObjectProperty(None)
    '''Previous button for ActionView.

       :data:`action_previous` is an :class:`~kivy.properties.ObjectProperty`,
       default to an instance of ActionPrevious.
    '''

    background_color = ListProperty([1, 1, 1, 1])
    '''Background color, in the format (r, g, b, a).

       :data:`background_color` is a :class:`~kivy.properties.ListProperty`,
        default to [1, 1, 1, 1].
    '''

    background_image = StringProperty(
        'atlas://data/images/defaulttheme/action_view')
    '''Background image of ActionView for default graphical represenation.

      :data:`background_image` is an :class:`~kivy.properties.StringProperty`,
      default to 'action_view'
    '''

    use_separator = BooleanProperty(False)
    '''Whether to use separator before every ActionGroup or not.

       :data:`use_separator` is an :class:`~kivy.properties.OptionProperty`,
       default to False.
    '''

    overflow_group = ObjectProperty(None)
    '''Widget to be used for overflow.

       :data:`action_previous` is an :class:`~kivy.properties.ObjectProperty`,
       default to an instance of ActionOverflow.
    '''

    def __init__(self, **kwargs):
        self._list_action_items = []
        self._list_action_group = []
        super(ActionView, self).__init__(**kwargs)
        self._state = ''
        self.overflow_group = ActionOverflow(use_separator=self.use_separator)

    def on_action_previous(self, instance, value):
        self._list_action_items.insert(0, value)

    def add_widget(self, action_item, index=0):
        if not isinstance(action_item, ActionItem):
            raise ActionBarException('ActionView only accepts ActionItem')

        elif isinstance(action_item, ActionOverflow):
            #action_item is an ActionOverflow
            self.overflow_group = action_item
            action_item.use_separator = self.use_separator

        elif isinstance(action_item, ActionGroup):
            #action_item is an ActionGroup
            self._list_action_group.append(action_item)
            action_item.use_separator = self.use_separator

        elif isinstance(action_item, ActionPrevious):
            #action_item is ActionPrevious
            self.action_previous = action_item

        else:
            #otherwise its an ActionItem only
            super(ActionView, self).add_widget(action_item, index)
            if index == 0:
                index = len(self._list_action_items)
            self._list_action_items.insert(index, action_item)

    def on_use_separator(self, instance, value):
        for group in self._list_action_group:
            group.use_separator = value
        self.overflow_group.use_separator = value

    def _clear_all(self):
        self.clear_widgets()
        for group in self._list_action_group:
            group.clear_widgets()

        self.overflow_group.clear_widgets()
        self.overflow_group.list_action_item = []

    def on_width(self, width, *args):
        total_width = 0
        super_add = super(ActionView, self).add_widget

        for child in self._list_action_items:
            total_width += child.minimum_width

        for group in self._list_action_group:
            for child in group.list_action_item:
                total_width += child.minimum_width

        #First check if ActionView could display all ActionItems
        if total_width <= self.width:
            if self._state == 'all':
                return

            self._state = 'all'
            self._clear_all()
            #If yes, then display them
            super_add(self.action_previous)
            if len(self._list_action_items) > 1:
                for child in self._list_action_items[1:]:
                    child.size_hint_y = 1
                    child.inside_group = False
                    super_add(child)

            for group in self._list_action_group:
                if group.mode == 'spinner':
                    super_add(group)
                    group.show_group()
                else:
                    if group.list_action_item != []:
                        super_add(ActionSeparator())
                    for child in group.list_action_item:
                        child.inside_group = False
                        child.size_hint = 1, 1
                        super_add(child)

        else:
            #If no, then check if all ActionItems could be displayed
            #using ActionGroup
            total_width = 0
            for child in self._list_action_items:
                total_width += child.minimum_width
            for group in self._list_action_group:
                total_width += group.minimum_width

            if total_width < self.width:
                if self._state == 'group':
                    return

                self._state = 'group'
                self._clear_all()
                #If yes, then display them using ActionGroup
                super_add(self.action_previous)
                if len(self._list_action_items) > 1:
                    for child in self._list_action_items[1:]:
                        child.size_hint = 1, 1
                        super_add(child)
                        child.inside_group = False

                for group in self._list_action_group:
                    super_add(group)
                    group.show_group()

            else:
                #If no, then display as many ActionItem having 'important'
                #set to true
                self._state = 'random'
                self._clear_all()
                hidden_items = []
                hidden_groups = []
                total_width = 0
                super_add(self.action_previous)

                width = self.width - self.overflow_group.minimum_width -\
                        self.action_previous.minimum_width

                if len(self._list_action_items) >= 1:
                    for child in self._list_action_items[1:]:
                        if child.important is True:
                            if child.minimum_width + total_width < width:
                                child.size_hint = 1, 1
                                super_add(child)
                                child.inside_group = False
                                total_width += child.minimum_width
                            else:
                                hidden_items.append(child)
                        else:
                            hidden_items.append(child)

                #If space is left then display ActionItem inside
                #their ActionGroup
                if total_width < self.width:
                    for group in self._list_action_group:
                        if group.minimum_width + total_width +\
                           group.separator_width < width:
                            super_add(group)
                            group.show_group()
                            total_width += group.minimum_width +\
                                           group.separator_width

                        else:
                            hidden_groups.append(group)

                #If space is left then display other ActionItems
                if total_width < self.width:
                    for child in hidden_items[:]:
                        if child.minimum_width + total_width < width:
                            child.size_hint = 1, 1
                            super_add(child, 1)
                            total_width += child.minimum_width
                            child.inside_group = False
                            hidden_items.remove(child)

                #For all the remaining ActionItems and ActionItems
                #with in ActionGroups, Display them inside overflow_group
                for group in hidden_groups:
                    hidden_items.extend(group.list_action_item)

                if hidden_items != []:
                    for child in hidden_items:
                        child.size_hint_x = 1
                        self.overflow_group.add_widget(child)

                    self.overflow_group.show_group()
                    super_add(self.overflow_group)


class ContextualActionView(ActionView):
    '''ContextualActionView class, see module documentation
       for more information.
    '''
    pass


class ActionBar(BoxLayout):
    '''ActionBar, see module documentation for more information.

    :Events:
        `on_previous`
            Fired when action_previous of action_view is pressed.
    '''

    action_view = ObjectProperty(None)
    '''action_view of ActionBar.

       :data:`action_view` is an :class:`~kivy.properties.ObjectProperty`,
       default to an instance of ActionView.
    '''

    background_color = ListProperty([1, 1, 1, 1])
    '''Background color, in the format (r, g, b, a).

       :data:`background_color` is a :class:`~kivy.properties.ListProperty`,
        default to [1, 1, 1, 1].
    '''

    background_image = StringProperty(
        'atlas://data/images/defaulttheme/action_bar')

    '''Background image of ActionBar for default graphical represenation.

      :data:`background_image` is an :class:`~kivy.properties.StringProperty`,
      default to 'action_bar'
    '''

    __events__ = ('on_previous',)

    def __init__(self, **kwargs):
        super(ActionBar, self).__init__(**kwargs)
        self._stack_cont_action_view = []
        self._emit_previous = partial(self.dispatch, 'on_previous')

    def add_widget(self, view):
        if isinstance(view, ContextualActionView):
            self._stack_cont_action_view.append(view)
            view.action_view.unbind(on_release=self._emit_previous)
            view.action_view.bind(on_release=self._emit_previous)
            self.clear_widgets()
            super(ActionBar, self).add_widget(view)

        elif isinstance(view, ActionView):
            self.action_view = view
            super(ActionBar, self).add_widget(view)

        else:
            raise ActionBarException(
                'ActionBar can only add ContextualActionView or ActionView')

    def on_previous(self, *args):
        self._pop_contextual_action_view()

    def _pop_contextual_action_view(self):
        '''Remove the current ContextualActionView and display either the
           previous one or the ActionView
        '''
        self._stack_cont_action_view.pop()
        self.clear_widgets()
        if self._stack_cont_action_view == []:
            super(ActionBar, self).add_widget(self.action_view)
        else:
            super(ActionBar, self).add_widget(self._stack_cont_action_view[-1])


if __name__ == "__main__":
    from kivy.base import runTouchApp
    from kivy.uix.floatlayout import FloatLayout
    from kivy.clock import Clock
    from kivy.lang import Builder

    Builder.load_string('''
<MainWindow>:
    ActionBar:
        size_hint: 1,0.1
        pos_hint: {'top':1}
        ActionView:
            use_separator: True
            ActionPrevious:
                title: 'Title'
            ActionOverflow:
            ActionButton:
                text: 'Btn0'
            ActionButton:
                text: 'Btn1'
            ActionButton:
                text: 'Btn2'
            ActionButton:
                text: 'Btn3'
            ActionButton:
                text: 'Btn4'
            ActionGroup:
                text: 'Group1'
                ActionButton:
                    text: 'Btn5'
                ActionButton:
                    text: 'Btn6'
                ActionButton:
                    text: 'Btn7'
''')

    class MainWindow(FloatLayout):
        pass

    float_layout = MainWindow()
    runTouchApp(float_layout)
