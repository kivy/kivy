'''
Drop-Down List
==============

.. versionadded:: 1.4.0

A versatile drop-down list that can be used with custom widgets. It allows you
to display a list of widgets under a displayed widget. Unlike other toolkits,
the list of widgets can contain any type of widget: simple buttons,
images etc.

The positioning of the drop-down list is fully automatic: we will always try to
place the dropdown list in a way that the user can select an item in the list.

Basic example
-------------

A button with a dropdown list of 10 possible values. All the buttons within the
dropdown list will trigger the dropdown :meth:`DropDown.select` method. After
being called, the main button text will display the selection of the
dropdown. ::

    from kivy.uix.dropdown import DropDown
    from kivy.uix.button import Button
    from kivy.base import runTouchApp

    # create a dropdown with 10 buttons
    dropdown = DropDown()
    for index in range(10):
        # when adding widgets, we need to specify the height manually (disabling
        # the size_hint_y) so the dropdown can calculate the area it needs.
        btn = Button(text='Value %d' % index, size_hint_y=None, height=44)

        # for each button, attach a callback that will call the select() method
        # on the dropdown. We'll pass the text of the button as the data of the
        # selection.
        btn.bind(on_release=lambda btn: dropdown.select(btn.text))

        # then add the button inside the dropdown
        dropdown.add_widget(btn)

    # create a big main button
    mainbutton = Button(text='Hello', size_hint=(None, None))

    # show the dropdown menu when the main button is released
    # note: all the bind() calls pass the instance of the caller (here, the
    # mainbutton instance) as the first argument of the callback (here,
    # dropdown.open.).
    mainbutton.bind(on_release=dropdown.open)

    # one last thing, listen for the selection in the dropdown list and
    # assign the data to the button text.
    dropdown.bind(on_select=lambda instance, x: setattr(mainbutton, 'text', x))

    runTouchApp(mainbutton)

Extending dropdown in Kv
------------------------

You could create a dropdown directly from your kv::

    #:kivy 1.4.0
    <CustomDropDown>:
        Button:
            text: 'My first Item'
            size_hint_y: None
            height: 44
            on_release: root.select('item1')
        Label:
            text: 'Unselectable item'
            size_hint_y: None
            height: 44
        Button:
            text: 'My second Item'
            size_hint_y: None
            height: 44
            on_release: root.select('item2')

And then, create the associated python class and use it::

    class CustomDropDown(DropDown):
        pass

    dropdown = CustomDropDown()
    mainbutton = Button(text='Hello', size_hint=(None, None))
    mainbutton.bind(on_release=dropdown.open)
    dropdown.bind(on_select=lambda instance, x: setattr(mainbutton, 'text', x))
'''

__all__ = ('DropDown', )

from kivy.uix.scrollview import ScrollView
from kivy.properties import ObjectProperty, NumericProperty, BooleanProperty
from kivy.core.window import Window
from kivy.lang import Builder

Builder.load_string('''
<DropDown>:
    container: container
    do_scroll_x: False
    size_hint: None, None

    GridLayout:
        id: container
        size_hint_y: None
        height: self.minimum_size[1]
        cols: 1
''')


class DropDownException(Exception):
    '''DropDownException class.
    '''
    pass


class DropDown(ScrollView):
    '''DropDown class. See module documentation for more information.

    :Events:
        `on_select`: data
            Fired when a selection is done. The data of the selection is passed
            in as the first argument and is what you pass in the :meth:`select`
            method as the first argument.
        `on_dismiss`:
            .. versionadded:: 1.8.0

            Fired when the DropDown is dismissed, either on selection or on
            touching outside the widget.
    '''

    auto_width = BooleanProperty(True)
    '''By default, the width of the dropdown will be the same as the width of
    the attached widget. Set to False if you want to provide your own width.
    '''

    max_height = NumericProperty(None, allownone=True)
    '''Indicate the maximum height that the dropdown can take. If None, it will
    take the maximum height available until the top or bottom of the screen
    is reached.

    :attr:`max_height` is a :class:`~kivy.properties.NumericProperty` and
    defaults to None.
    '''

    dismiss_on_select = BooleanProperty(True)
    '''By default, the dropdown will be automatically dismissed when a
    selection has been done. Set to False to prevent the dismiss.

    :attr:`dismiss_on_select` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to True.
    '''

    auto_dismiss = BooleanProperty(True)
    '''By default, the dropdown will be automatically dismissed when a
    touch happens outside of it, this option allow to disable this
    feature

    :attr:`auto_dismiss` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to True.

    .. versionadded:: 1.8.0
    '''

    attach_to = ObjectProperty(allownone=True)
    '''(internal) Property that will be set to the widget to which the
    drop down list is attached.

    The :meth:`open` method will automatically set this property whilst
    :meth:`dismiss` will set it back to None.
    '''

    container = ObjectProperty()
    '''(internal) Property that will be set to the container of the dropdown
    list. It is a :class:`~kivy.uix.gridlayout.GridLayout` by default.
    '''

    __events__ = ('on_select', 'on_dismiss')

    def __init__(self, **kwargs):
        self._win = None
        super(DropDown, self).__init__(**kwargs)
        Window.bind(on_key_down=self.on_key_down)
        self.bind(size=self._reposition)

    def on_key_down(self, instance, key, scancode, codepoint, modifiers):
        if key == 27 and self.get_parent_window():
            self.dismiss()
            return True

    def on_container(self, instance, value):
        self.container.bind(minimum_size=self._container_minimum_size)

    def open(self, widget):
        '''Open the dropdown list and attach it to a specific widget.
        Depending on the position of the widget within the window and
        the height of the dropdown, the dropdown might be above or below
        that widget.
        '''
        # ensure we are not already attached
        if self.attach_to is not None:
            self.dismiss()

        # we will attach ourself to the main window, so ensure the
        # widget we are looking for have a window
        self._win = widget.get_parent_window()
        if self._win is None:
            raise DropDownException(
                'Cannot open a dropdown list on a hidden widget')

        self.attach_to = widget
        widget.bind(pos=self._reposition, size=self._reposition)
        self._reposition()

        # attach ourself to the main window
        self._win.add_widget(self)

    def dismiss(self, *largs):
        '''Remove the dropdown widget from the window and detach it from
        the attached widget.
        '''
        if self.parent:
            self.parent.remove_widget(self)
        if self.attach_to:
            self.attach_to.unbind(pos=self._reposition, size=self._reposition)
            self.attach_to = None
        self.dispatch('on_dismiss')

    def on_dismiss(self):
        pass

    def select(self, data):
        '''Call this method to trigger the `on_select` event with the `data`
        selection. The `data` can be anything you want.
        '''
        self.dispatch('on_select', data)
        if self.dismiss_on_select:
            self.dismiss()

    def on_select(self, data):
        pass

    def _container_minimum_size(self, instance, size):
        if self.max_height:
            self.height = min(size[1], self.max_height)
            self.do_scroll_y = size[1] > self.max_height
        else:
            self.height = size[1]
            self.do_scroll_y = True

    def add_widget(self, *largs):
        if self.container:
            return self.container.add_widget(*largs)
        return super(DropDown, self).add_widget(*largs)

    def remove_widget(self, *largs):
        if self.container:
            return self.container.remove_widget(*largs)
        return super(DropDown, self).remove_widget(*largs)

    def clear_widgets(self):
        if self.container:
            return self.container.clear_widgets()
        return super(DropDown, self).clear_widgets()

    def on_touch_down(self, touch):
        if super(DropDown, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos):
            return True
        if self.auto_dismiss:
            self.dismiss()

    def on_touch_up(self, touch):
        if super(DropDown, self).on_touch_up(touch):
            return True
        if 'button' in touch.profile and touch.button.startswith('scroll'):
            return
        if self.auto_dismiss:
            self.dismiss()

    def _reposition(self, *largs):
        # calculate the coordinate of the attached widget in the window
        # coordinate system
        win = self._win
        widget = self.attach_to
        if not widget or not win:
            return
        wx, wy = widget.to_window(*widget.pos)
        wright, wtop = widget.to_window(widget.right, widget.top)

        # set width and x
        if self.auto_width:
            self.width = wright - wx

        # ensure the dropdown list doesn't get out on the X axis, with a
        # preference to 0 in case the list is too wide.
        x = wx
        if x + self.width > win.width:
            x = win.width - self.width
        if x < 0:
            x = 0
        self.x = x

        # determine if we display the dropdown upper or lower to the widget
        h_bottom = wy - self.height
        h_top = win.height - (wtop + self.height)
        if h_bottom > 0:
            self.top = wy
        elif h_top > 0:
            self.y = wtop
        else:
            # none of both top/bottom have enough place to display the
            # widget at the current size. Take the best side, and fit to
            # it.
            height = max(h_bottom, h_top)
            if height == h_bottom:
                self.top = wy
                self.height = wy
            else:
                self.y = wtop
                self.height = win.height - wtop


if __name__ == '__main__':
    from kivy.uix.button import Button
    from kivy.base import runTouchApp

    def show_dropdown(button, *largs):
        dp = DropDown()
        dp.bind(on_select=lambda instance, x: setattr(button, 'text', x))
        for i in range(10):
            item = Button(text='hello %d' % i, size_hint_y=None, height=44)
            item.bind(on_release=lambda btn: dp.select(btn.text))
            dp.add_widget(item)
        dp.open(button)

    def touch_move(instance, touch):
        instance.center = touch.pos

    btn = Button(text='SHOW', size_hint=(None, None), pos=(300, 200))
    btn.bind(on_release=show_dropdown, on_touch_move=touch_move)

    runTouchApp(btn)
