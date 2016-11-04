'''
Accordion
=========

.. versionadded:: 1.0.8


.. image:: images/accordion.jpg
    :align: right

The Accordion widget is a form of menu where the options are stacked either
vertically or horizontally and the item in focus (when touched) opens up to
display its content.

The :class:`Accordion` should contain one or many :class:`AccordionItem`
instances, each of which should contain one root content widget. You'll end up
with a Tree something like this:

- Accordion

  - AccordionItem

    - YourContent

  - AccordionItem

    - BoxLayout

      - Another user content 1

      - Another user content 2

  - AccordionItem

    - Another user content


The current implementation divides the :class:`AccordionItem` into two parts:

#. One container for the title bar
#. One container for the content

The title bar is made from a Kv template. We'll see how to create a new
template to customize the design of the title bar.

.. warning::

    If you see message like::

        [WARNING] [Accordion] not have enough space for displaying all children
        [WARNING] [Accordion] need 440px, got 100px
        [WARNING] [Accordion] layout aborted.

    That means you have too many children and there is no more space to
    display the content. This is "normal" and nothing will be done. Try to
    increase the space for the accordion or reduce the number of children. You
    can also reduce the :attr:`Accordion.min_space`.

Simple example
--------------

.. include:: ../../examples/widgets/accordion_1.py
    :literal:

Customize the accordion
-----------------------

You can increase the default size of the title bar::

    root = Accordion(min_space=60)

Or change the orientation to vertical::

    root = Accordion(orientation='vertical')

The AccordionItem is more configurable and you can set your own title
background when the item is collapsed or opened::

    item = AccordionItem(background_normal='image_when_collapsed.png',
        background_selected='image_when_selected.png')

'''

__all__ = ('Accordion', 'AccordionItem', 'AccordionException')

from kivy.animation import Animation
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import (ObjectProperty, StringProperty,
                             BooleanProperty, NumericProperty,
                             ListProperty, OptionProperty, DictProperty)
from kivy.uix.widget import Widget
from kivy.logger import Logger


class AccordionException(Exception):
    '''AccordionException class.
    '''
    pass


class AccordionItem(FloatLayout):
    '''AccordionItem class that must be used in conjunction with the
    :class:`Accordion` class. See the module documentation for more
    information.
    '''

    title = StringProperty('')
    '''Title string of the item. The title might be used in conjunction with the
    `AccordionItemTitle` template. If you are using a custom template, you can
    use that property as a text entry, or not. By default, it's used for the
    title text. See title_template and the example below.

    :attr:`title` is a :class:`~kivy.properties.StringProperty` and defaults
    to ''.
    '''

    title_template = StringProperty('AccordionItemTitle')
    '''Template to use for creating the title part of the accordion item. The
    default template is a simple Label, not customizable (except the text) that
    supports vertical and horizontal orientation and different backgrounds for
    collapse and selected mode.

    It's better to create and use your own template if the default template
    does not suffice.

    :attr:`title` is a :class:`~kivy.properties.StringProperty` and defaults to
    'AccordionItemTitle'. The current default template lives in the
    `kivy/data/style.kv` file.

    Here is the code if you want to build your own template::

        [AccordionItemTitle@Label]:
            text: ctx.title
            canvas.before:
                Color:
                    rgb: 1, 1, 1
                BorderImage:
                    source:
                        ctx.item.background_normal \
                        if ctx.item.collapse \
                        else ctx.item.background_selected
                    pos: self.pos
                    size: self.size
                PushMatrix
                Translate:
                    xy: self.center_x, self.center_y
                Rotate:
                    angle: 90 if ctx.item.orientation == 'horizontal' else 0
                    axis: 0, 0, 1
                Translate:
                    xy: -self.center_x, -self.center_y
            canvas.after:
                PopMatrix


    '''

    title_args = DictProperty({})
    '''Default arguments that will be passed to the
    :meth:`kivy.lang.Builder.template` method.

    :attr:`title_args` is a :class:`~kivy.properties.DictProperty` and defaults
    to {}.
    '''

    collapse = BooleanProperty(True)
    '''Boolean to indicate if the current item is collapsed or not.

    :attr:`collapse` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    collapse_alpha = NumericProperty(1.)
    '''Value between 0 and 1 to indicate how much the item is collapsed (1) or
    whether it is selected (0). It's mostly used for animation.

    :attr:`collapse_alpha` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 1.
    '''

    accordion = ObjectProperty(None)
    '''Instance of the :class:`Accordion` that the item belongs to.

    :attr:`accordion` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    background_normal = StringProperty(
        'atlas://data/images/defaulttheme/button')
    '''Background image of the accordion item used for the default graphical
    representation when the item is collapsed.

    :attr:`background_normal` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/button'.
    '''

    background_disabled_normal = StringProperty(
        'atlas://data/images/defaulttheme/button_disabled')
    '''Background image of the accordion item used for the default graphical
    representation when the item is collapsed and disabled.

    .. versionadded:: 1.8.0

    :attr:`background__disabled_normal` is a
    :class:`~kivy.properties.StringProperty` and defaults to
    'atlas://data/images/defaulttheme/button_disabled'.
    '''

    background_selected = StringProperty(
        'atlas://data/images/defaulttheme/button_pressed')
    '''Background image of the accordion item used for the default graphical
    representation when the item is selected (not collapsed).

    :attr:`background_normal` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/button_pressed'.
    '''

    background_disabled_selected = StringProperty(
        'atlas://data/images/defaulttheme/button_disabled_pressed')
    '''Background image of the accordion item used for the default graphical
    representation when the item is selected (not collapsed) and disabled.

    .. versionadded:: 1.8.0

    :attr:`background_disabled_selected` is a
    :class:`~kivy.properties.StringProperty` and defaults to
    'atlas://data/images/defaulttheme/button_disabled_pressed'.
    '''

    orientation = OptionProperty('vertical', options=(
        'horizontal', 'vertical'))
    '''Link to the :attr:`Accordion.orientation` property.
    '''

    min_space = NumericProperty('44dp')
    '''Link to the :attr:`Accordion.min_space` property.
    '''

    content_size = ListProperty([100, 100])
    '''(internal) Set by the :class:`Accordion` to the size allocated for the
    content.
    '''

    container = ObjectProperty(None)
    '''(internal) Property that will be set to the container of children inside
    the AccordionItem representation.
    '''

    container_title = ObjectProperty(None)
    '''(internal) Property that will be set to the container of title inside
    the AccordionItem representation.
    '''

    def __init__(self, **kwargs):
        self._trigger_title = Clock.create_trigger(self._update_title, -1)
        self._anim_collapse = None
        super(AccordionItem, self).__init__(**kwargs)
        trigger_title = self._trigger_title
        fbind = self.fbind
        fbind('title', trigger_title)
        fbind('title_template', trigger_title)
        fbind('title_args', trigger_title)
        trigger_title()

    def add_widget(self, widget):
        if self.container is None:
            return super(AccordionItem, self).add_widget(widget)
        return self.container.add_widget(widget)

    def remove_widget(self, widget):
        if self.container:
            self.container.remove_widget(widget)
        super(AccordionItem, self).remove_widget(widget)

    def on_collapse(self, instance, value):
        accordion = self.accordion
        if accordion is None:
            return
        if not value:
            self.accordion.select(self)
        collapse_alpha = float(value)
        if self._anim_collapse:
            self._anim_collapse.stop()
            self._anim_collapse = None
        if self.collapse_alpha != collapse_alpha:
            self._anim_collapse = Animation(
                collapse_alpha=collapse_alpha,
                t=accordion.anim_func,
                d=accordion.anim_duration).start(self)

    def on_collapse_alpha(self, instance, value):
        self.accordion._trigger_layout()

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return
        if self.disabled:
            return True
        if self.collapse:
            self.collapse = False
            return True
        else:
            return super(AccordionItem, self).on_touch_down(touch)

    def _update_title(self, dt):
        if not self.container_title:
            self._trigger_title()
            return
        c = self.container_title
        c.clear_widgets()
        instance = Builder.template(self.title_template,
                                    title=self.title,
                                    item=self,
                                    **self.title_args)
        c.add_widget(instance)


class Accordion(Widget):
    '''Accordion class. See module documentation for more information.
    '''

    orientation = OptionProperty('horizontal', options=(
        'horizontal', 'vertical'))
    '''Orientation of the layout.

    :attr:`orientation` is an :class:`~kivy.properties.OptionProperty`
    and defaults to 'horizontal'. Can take a value of 'vertical' or
    'horizontal'.

    '''

    anim_duration = NumericProperty(.25)
    '''Duration of the animation in seconds when a new accordion item is
    selected.

    :attr:`anim_duration` is a :class:`~kivy.properties.NumericProperty` and
    defaults to .25 (250ms).
    '''

    anim_func = ObjectProperty('out_expo')
    '''Easing function to use for the animation. Check
    :class:`kivy.animation.AnimationTransition` for more information about
    available animation functions.

    :attr:`anim_func` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to 'out_expo'. You can set a string or a function to use as an
    easing function.
    '''

    min_space = NumericProperty('44dp')
    '''Minimum space to use for the title of each item. This value is
    automatically set for each child every time the layout event occurs.

    :attr:`min_space` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 44 (px).
    '''

    def __init__(self, **kwargs):
        super(Accordion, self).__init__(**kwargs)
        update = self._trigger_layout = \
            Clock.create_trigger(self._do_layout, -1)
        fbind = self.fbind
        fbind('orientation', update)
        fbind('children', update)
        fbind('size', update)
        fbind('pos', update)
        fbind('min_space', update)

    def add_widget(self, widget, *largs):
        if not isinstance(widget, AccordionItem):
            raise AccordionException('Accordion accept only AccordionItem')

        widget.accordion = self
        ret = super(Accordion, self).add_widget(widget, *largs)
        return ret

    def select(self, instance):
        if instance not in self.children:
            raise AccordionException(
                'Accordion: instance not found in children')
        for widget in self.children:
            widget.collapse = widget is not instance
        self._trigger_layout()

    def _do_layout(self, dt):
        children = self.children
        if children:
            all_collapsed = all(x.collapse for x in children)
        else:
            all_collapsed = False

        if all_collapsed:
            children[0].collapse = False

        orientation = self.orientation
        min_space = self.min_space
        min_space_total = len(children) * self.min_space
        w, h = self.size
        x, y = self.pos
        if orientation == 'horizontal':
            display_space = self.width - min_space_total
        else:
            display_space = self.height - min_space_total

        if display_space <= 0:
            Logger.warning('Accordion: not enough space '
                           'for displaying all children')
            Logger.warning('Accordion: need %dpx, got %dpx' % (
                min_space_total, min_space_total + display_space))
            Logger.warning('Accordion: layout aborted.')
            return

        if orientation == 'horizontal':
            children = reversed(children)

        for child in children:
            child_space = min_space
            child_space += display_space * (1 - child.collapse_alpha)
            child._min_space = min_space
            child.x = x
            child.y = y
            child.orientation = self.orientation
            if orientation == 'horizontal':
                child.content_size = display_space, h
                child.width = child_space
                child.height = h
                x += child_space
            else:
                child.content_size = w, display_space
                child.width = w
                child.height = child_space
                y += child_space

if __name__ == '__main__':
    from kivy.base import runTouchApp
    from kivy.uix.button import Button
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label

    acc = Accordion()
    for x in range(10):
        item = AccordionItem(title='Title %d' % x)
        if x == 0:
            item.add_widget(Button(text='Content %d' % x))
        elif x == 1:
            l = BoxLayout(orientation='vertical')
            l.add_widget(Button(text=str(x), size_hint_y=None, height=35))
            l.add_widget(Label(text='Content %d' % x))
            item.add_widget(l)
        else:
            item.add_widget(Label(text='This is a big content\n' * 20))
        acc.add_widget(item)

    def toggle_layout(*l):
        o = acc.orientation
        acc.orientation = 'vertical' if o == 'horizontal' else 'horizontal'
    btn = Button(text='Toggle layout')
    btn.bind(on_release=toggle_layout)

    def select_2nd_item(*l):
        acc.select(acc.children[-2])
    btn2 = Button(text='Select 2nd item')
    btn2.bind(on_release=select_2nd_item)

    from kivy.uix.slider import Slider
    slider = Slider()

    def update_min_space(instance, value):
        acc.min_space = value

    slider.bind(value=update_min_space)

    root = BoxLayout(spacing=20, padding=20)
    controls = BoxLayout(orientation='vertical', size_hint_x=.3)
    controls.add_widget(btn)
    controls.add_widget(btn2)
    controls.add_widget(slider)
    root.add_widget(controls)
    root.add_widget(acc)
    runTouchApp(root)
