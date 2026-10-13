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

The title bar is rendered by the :class:`AccordionItemTitle` widget. To
customize the design of the title bar, subclass :class:`AccordionItemTitle`
(or any other widget that exposes ``title`` and ``item`` properties) and
assign your class to :attr:`AccordionItem.title_class`.

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

__all__ = ('Accordion', 'AccordionItem', 'AccordionItemTitle',
           'AccordionException')

from kivy.animation import Animation
from kivy.factory import Factory
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.properties import (ObjectProperty, StringProperty,
                             BooleanProperty, NumericProperty,
                             ListProperty, OptionProperty)
from kivy.uix.widget import Widget
from kivy.logger import Logger


class AccordionException(Exception):
    '''AccordionException class.
    '''
    pass


class AccordionItemTitle(Label):
    '''Default title widget used by :class:`AccordionItem`. Renders the
    ``title`` text and clickable background derived from the owning
    ``item``.

    To use a custom title widget, set :attr:`AccordionItem.title_class` to
    your own class. Your class should expose ``title`` (a string) and
    ``item`` (a reference to the owning :class:`AccordionItem`) properties.

    .. versionadded:: 3.0.0
        Promoted to a regular Python class. Previously this was a deprecated
        Kivy lang template (``[AccordionItemTitle@Label]:``).
    '''

    title = StringProperty('')
    '''Text rendered by this title widget. Populated by the owning
    :class:`AccordionItem` from its :attr:`~AccordionItem.title` property
    each time the title widget is (re)built. Set this when constructing a
    custom title widget; do not set it directly on an existing instance,
    as it will be overwritten on the next rebuild.

    :attr:`title` is a :class:`~kivy.properties.StringProperty` and
    defaults to ''.
    '''

    item = ObjectProperty(None, allownone=True)
    '''Reference to the owning :class:`AccordionItem`. Used by the
    default KV rule to derive backgrounds and rotation.'''


class AccordionItem(FloatLayout):
    '''AccordionItem class that must be used in conjunction with the
    :class:`Accordion` class. See the module documentation for more
    information.
    '''

    title = StringProperty('')
    '''Title string of the item. By default, it's used as the text of the
    title widget (see :attr:`title_class`).

    :attr:`title` is a :class:`~kivy.properties.StringProperty` and defaults
    to ''.
    '''

    title_class = ObjectProperty(AccordionItemTitle)
    '''Class used to instantiate the title widget for this accordion item.
    The class is instantiated with two keyword arguments: ``title`` (the
    text from :attr:`title`) and ``item`` (a reference to this
    :class:`AccordionItem`).

    A string may be supplied; it will be resolved via the
    :class:`~kivy.factory.Factory` to a class. The default is
    :class:`AccordionItemTitle`.

    To use a custom title widget, define a subclass of
    :class:`AccordionItemTitle` (or any widget that accepts ``title``
    and ``item`` kwargs), provide a matching Kv rule, and pass the
    class via this property::

        item = AccordionItem(title='Hello', title_class=MyTitle)

    The default :class:`AccordionItemTitle` is styled by the following
    Kv rule, shipped in ``kivy/data/style.kv``. It can be used as a
    starting point when building your own ``title_class`` rule:

    .. code-block:: kv

        <AccordionItemTitle>:
            text: root.title
            normal_background: (root.item.background_normal if root.item.collapse else root.item.background_selected) if root.item else ''
            disabled_background: (root.item.background_disabled_normal if root.item.collapse else root.item.background_disabled_selected) if root.item else ''
            canvas.before:
                Color:
                    rgba: self.disabled_color if self.disabled else self.color
                BorderImage:
                    source: self.disabled_background if self.disabled else self.normal_background
                    pos: self.pos
                    size: self.size
                PushMatrix
                Translate:
                    xy: self.center_x, self.center_y
                Rotate:
                    angle: 90 if root.item and root.item.orientation == 'horizontal' else 0
                    axis: 0, 0, 1
                Translate:
                    xy: -self.center_x, -self.center_y
            canvas.after:
                PopMatrix

    :attr:`title_class` is an :class:`~kivy.properties.ObjectProperty`
    and defaults to :class:`AccordionItemTitle`.

    .. versionadded:: 3.0.0
        Replaces the deprecated ``title_template`` (string) and
        ``title_args`` (dict) properties, which relied on the now-removed
        Kivy lang templates feature.
    '''  # noqa: E501

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
        fbind('title_class', trigger_title)
        trigger_title()

    def on_title_class(self, instance, value):
        # mirror RecycleView.viewclass: auto-resolve string names through
        # the Factory so users can pass either a string or a class.
        if isinstance(value, str):
            self.title_class = Factory.get(value)

    def add_widget(self, *args, **kwargs):
        if self.container is None:
            super(AccordionItem, self).add_widget(*args, **kwargs)
            return
        self.container.add_widget(*args, **kwargs)

    def remove_widget(self, *args, **kwargs):
        if self.container:
            self.container.remove_widget(*args, **kwargs)
            return
        super(AccordionItem, self).remove_widget(*args, **kwargs)

    def on_collapse(self, instance, value):
        accordion = self.accordion
        if accordion is None:
            return
        if not value:
            self.accordion.select(self)
        collapse_alpha = float(value)
        if self._anim_collapse:
            self._anim_collapse.stop(self)
            self._anim_collapse = None
        if self.collapse_alpha != collapse_alpha:
            self._anim_collapse = Animation(
                collapse_alpha=collapse_alpha,
                t=accordion.anim_func,
                d=accordion.anim_duration)
            self._anim_collapse.start(self)

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
        cls = self.title_class
        if isinstance(cls, str):
            cls = Factory.get(cls)
        c.add_widget(cls(title=self.title, item=self))


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

    def add_widget(self, widget, *args, **kwargs):
        if not isinstance(widget, AccordionItem):
            raise AccordionException('Accordion accept only AccordionItem')
        widget.accordion = self
        super(Accordion, self).add_widget(widget, *args, **kwargs)

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
            z = BoxLayout(orientation='vertical')
            z.add_widget(Button(text=str(x), size_hint_y=None, height=35))
            z.add_widget(Label(text='Content %d' % x))
            item.add_widget(z)
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
