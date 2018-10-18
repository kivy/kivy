"""
Drag and Drop
==============

This adds a drag and drop functionality to layouts and widgets. There are 2
primary and one internal component used to have drag and drop:

* The :class:`DragableObjectBehavior`. Each widget that can be dragged needs
  to inherit from this. It has :attr:`DragableObjectBehavior.drag_cls`, which
  is a string that indicates the :class:`DragableLayoutBehavior` instance
  into which the widget can potentially be dropped.
* The :class:`DragableLayoutBehavior`, which any layout that wants to accept
  drop behavior must inherit from. It has a
  :attr:`DragableLayoutBehavior.drag_classes`, which determines the
  dragging widgets it accepts - their :attr:`DragableObjectBehavior.drag_cls`
  must be listed in :attr:`DragableLayoutBehavior.drag_classes`.
* Finally, :class:`DragableController`which manages the drag and drop
  coordination. This is created automatically for each
  :class:`DragableObjectBehavior.drag_controller` upon first drag, or it
  can be set by the user to a global controller to save memory.

Layout
-------

To use :class:`DragableLayoutBehavior` with a layout,
:meth:`DragableLayoutBehavior.compare_pos_to_widget` must be implement for each
layout. This determines where in the layout the widget is being previewed and
ultimitely dropped. But, it can be further customized for any type of layout
by overwriting the default
:meth:`DragableLayoutBehavior.get_drop_insertion_index_move` and
:meth:`DragableLayoutBehavior.get_drop_insertion_index_up`.

Similarly, :meth:`.handle_drag_release` should be implemented. It handles the
actual final drop into the layout. A good default implementation is::

    def handle_drag_release(self, index, drag_widget):
        self.add_widget(drag_widget, index)

Dragging Widget
-----------------

To use :class:`DragableObjectBehavior`, one should implement
:meth:`DragableObjectBehavior.initiate_drag` and/or
:meth:`DragableObjectBehavior.complete_drag`. Typically, you would want to
remove the widget from it's current layout as it starts to be dragged, with
e.g. ::

    def initiate_drag(self):
        self.parent.remove_widget(self)

Describing Which Widgets can be Dropped Into Which Layout
-------------------------------------------------------------

Given some :class:`DragableObjectBehavior` and
some :class:`DragableLayoutBehavior` instances. We can control which widget can
be dragged into which layout using their
:attr:`DragableObjectBehavior.drag_cls` and
:attr:`DragableLayoutBehavior.drag_classes`.
:attr:`DragableObjectBehavior.drag_cls` must be listed in
:attr:`DragableLayoutBehavior.drag_classes` for the widget to be draggable into
the layout.

Example
--------

Following is an example with :class:`kivy.uix.boxlayout.BoxLayout`::

    from kivy.uix.label import Label
    from kivy.uix.boxlayout import BoxLayout

    class DragableBoxLayout(DragableLayoutBehavior, BoxLayout):

        def compare_pos_to_widget(self, widget, pos):
            if self.orientation == 'vertical':
                return 'before' if pos[1] >= widget.center_y else 'after'
            return 'before' if pos[0] < widget.center_x else 'after'

        def handle_drag_release(self, index, drag_widget):
            self.add_widget(drag_widget, index)

    class DragLabel(DragableObjectBehavior, Label):

        def initiate_drag(self):
            # during a drag, we remove the widget from the original location
            self.parent.remove_widget(self)

And then in kv::

    BoxLayout:
        DragableBoxLayout:
            drag_classes: ['label']
            orientation: 'vertical'
            Label:
                text: 'A'
            Label:
                text: 'A'
            Label:
                text: 'A'
        DragableBoxLayout:
            drag_classes: ['label']
            orientation: 'vertical'
            DragLabel:
                text: 'A*'
                drag_cls: 'label'
            DragLabel:
                text: 'A*'
                drag_cls: 'label'
"""
from kivy.properties import ObjectProperty, NumericProperty, \
    StringProperty, ListProperty, DictProperty, BooleanProperty
from kivy.factory import Factory
from kivy.event import EventDispatcher
from kivy.uix.widget import Widget
from kivy.graphics import Fbo, ClearBuffers, ClearColor, Scale, Translate
from kivy.graphics.texture import Texture
from kivy.lang.builder import Builder
from kivy.core.window import Window
from kivy.config import Config

__all__ = (
    'DragableObjectBehavior', 'DragableLayoutBehavior', 'DragableController',
    'PreviewWidget', 'SpacerWidget')

_drag_distance = 0
if Config:
    _drag_distance = '{}sp'.format(Config.getint('widgets', 'scroll_distance'))


def collide_parent_tree(widget, x, y):
    """Returns whether (x, y) collide with the widget and all its parents.
    """
    if not widget.collide_point(x, y):
        return False

    parent = widget.parent
    while parent and hasattr(parent, 'to_parent'):
        x, y = parent.to_parent(x, y)  # transform to parent's parent's
        if not parent.collide_point(x, y):
            return False

        parent = parent.parent
    return True


class DragableObjectBehavior(object):
    """A widget that inherits from this class can participate in a drag by
    someone dragging it with the mouse.
    """

    drag_controller = ObjectProperty(None)
    """A (potentially global) :class:`DragableController` instance that manages
    the (potential) drag. If `None` during the first potential drag, a
    :class:`DragableController` instance will be created and set.
    """

    drag_widget = ObjectProperty(None)
    """The widget, whose texture will be copied and previewed as the object is
    dragged. If `None`, it's this widget.
    """

    drag_cls = StringProperty('')
    """A name to determine where we can potentially drop the dragged widget.
    For each :class:`DragableLayoutBehavior` that we hover over, if
    :attr:`drag_cls` is in that :attr:`DragableLayoutBehavior.drag_classes`, we
    will preview and allow the widget to be dropped there.
    """

    _drag_touch = None

    def initiate_drag(self):
        """Called by the :class:`DragableController`, when a drag is initiated
        on the widget (i.e. thw widget is actually being dragged once it
        exceeds the minimum drag distance).
        """
        pass

    def complete_drag(self):
        """Called by the :class:`DragableController`, when a drag is completed.
        """
        pass

    def _touch_uid(self):
        return '{}.{}'.format(self.__class__.__name__, self.uid)

    def on_touch_down(self, touch):
        uid = self._touch_uid()
        if uid in touch.ud:
            return touch.ud[uid]

        if super(DragableObjectBehavior, self).on_touch_down(touch):
            touch.ud[uid] = False
            return True

        x, y = touch.pos
        if not self.collide_point(x, y):
            touch.ud[uid] = False
            return False

        if self._drag_touch or ('button' in touch.profile and
                                touch.button.startswith('scroll')):
            touch.ud[uid] = False
            return False

        self._drag_touch = touch
        touch.grab(self)
        touch.ud[uid] = True

        if not self.drag_controller:
            self.drag_controller = DragableController()

        return self.drag_controller.drag_down(self, touch)

    def on_touch_move(self, touch):
        uid = self._touch_uid()
        if uid not in touch.ud:
            touch.ud[uid] = False
            return super(DragableObjectBehavior, self).on_touch_move(touch)

        if not touch.ud[uid]:
            return super(DragableObjectBehavior, self).on_touch_move(touch)

        if touch.grab_current is not self:
            return False

        if not self.drag_controller:
            self.drag_controller = DragableController()

        return self.drag_controller.drag_move(self, touch)

    def on_touch_up(self, touch):
        uid = self._touch_uid()
        if uid not in touch.ud:
            touch.ud[uid] = False
            return super(DragableObjectBehavior, self).on_touch_up(touch)

        if not touch.ud[uid]:
            return super(DragableObjectBehavior, self).on_touch_up(touch)

        if touch.grab_current is not self:
            return False

        touch.ungrab(self)
        self._drag_touch = None

        if not self.drag_controller:
            self.drag_controller = DragableController()

        return self.drag_controller.drag_up(self, touch)


class PreviewWidget(Widget):
    """The widget that is used to preview the widget being dragged, during a
    drag. Used internally.
    """

    preview_texture = ObjectProperty(None)


class SpacerWidget(Widget):
    """Widget inserted at the location where the dragged widget may be
    dropped to show where it'll be dropped.
    """
    pass


Builder.load_string('''
<PreviewWidget>:
    canvas:
        Color:
            rgba: .2, .2, .2, 1
        Rectangle:
            size: self.size
            pos: self.pos
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            size: self.size
            pos: self.pos
            texture: self.preview_texture

<SpacerWidget>:
    canvas:
        Color:
            rgba: .2, .2, .2, 1
        Rectangle:
            size: self.size
            pos: self.pos
''')


class DragableController(EventDispatcher):
    """The controller that manages the dragging process.
    """

    drag_distance = NumericProperty(_drag_distance)
    """Minimum amount of pixel distance a widget needs to be dragged before
    we start going into drag mode.
    """

    preview_widget = None
    """The widget shown as preview during a drag, which follows the current
    mouse position. Defaults to a :class:`PreviewWidget`.
    that f"""

    preview_pixels = None

    widget_dragged = None
    """The :class:`DragableObjectBehavior` widget currently being dragged by
    the controller.
    """

    touch_dx = 0

    touch_dy = 0

    dragging = False

    start_widget_pos = 0, 0

    def __init__(self, **kwargs):
        super(DragableController, self).__init__(**kwargs)
        self.preview_widget = PreviewWidget(size_hint=(None, None))

    def _reload_texture(self, texture):
        if self.preview_pixels:
            texture.blit_buffer(
                self.preview_pixels, colorfmt='rgba', bufferfmt='ubyte')
        else:
            texture.remove_reload_observer(self._reload_texture)

    def prepare_preview_widget(self, source_widget):
        size = source_widget.size
        widget = self.preview_widget

        # get the pixels from the source widget
        if source_widget.parent is not None:
            canvas_parent_index = source_widget.parent.canvas.indexof(
                source_widget.canvas)
            if canvas_parent_index > -1:
                source_widget.parent.canvas.remove(source_widget.canvas)

        fbo = Fbo(size=size, with_stencilbuffer=False)

        with fbo:
            ClearColor(0, 0, 0, 1)
            ClearBuffers()
            Scale(1, -1, 1)
            Translate(
                -source_widget.x, -source_widget.y - source_widget.height, 0)

        fbo.add(source_widget.canvas)
        fbo.draw()
        self.preview_pixels = fbo.texture.pixels
        fbo.remove(source_widget.canvas)

        if source_widget.parent is not None and canvas_parent_index > -1:
            source_widget.parent.canvas.insert(
                canvas_parent_index, source_widget.canvas)

        widget.size = size
        texture = widget.preview_texture = Texture.create(
            size=size, colorfmt='RGBA', bufferfmt='ubyte')
        texture.flip_vertical()
        texture.add_reload_observer(self._reload_texture)
        self._reload_texture(texture)

    def clean_dragging(self):
        """Removes the drag widget preview.
        """
        if not self.preview_pixels:
            return

        self.preview_pixels = None
        widget = self.preview_widget
        if widget.parent:
            widget.parent.remove_widget(widget)

    def drag_down(self, source, touch):
        """Called by :class:`DragableObjectBehavior` when it got a touch down.
        """
        self.clean_dragging()
        self.widget_dragged = source
        self.prepare_preview_widget(source.drag_widget or source)
        self.touch_dx = self.touch_dy = 0
        self.dragging = False
        self.preview_widget.canvas.opacity = 0
        Window.add_widget(self.preview_widget)
        self.start_widget_pos = self.preview_widget.pos = \
            source.to_window(*source.pos)
        return False

    def drag_move(self, source, touch):
        """Called by :class:`DragableObjectBehavior` when it got a touch move.
        """
        if not self.dragging:
            self.touch_dx += abs(touch.dx)
            self.touch_dy += abs(touch.dy)
            if (self.touch_dx ** 2 + self.touch_dy ** 2) ** .5 \
                    > self.drag_distance:
                self.dragging = True
                self.preview_widget.canvas.opacity = .4
                touch.ud['drag_cls'] = source.drag_cls
                touch.ud['drag_widget'] = source
                source.initiate_drag()
            else:
                return False

        x, y = self.start_widget_pos
        x += touch.x - touch.ox
        y += touch.y - touch.oy
        self.preview_widget.pos = x, y
        return False

    def drag_up(self, source, touch):
        """Called by :class:`DragableObjectBehavior` when it got a touch up.
        """
        self.clean_dragging()
        if not self.dragging:
            return False

        self.clean_dragging()
        self.dragging = False
        source.complete_drag()
        self.widget_dragged = None
        return False


class DragableLayoutBehavior(object):
    """Adds support to a layout such that we can drag widgets **into** this
    layout and preview it while dragging.

    Only :class:`DragableObjectBehavior` widgets whose
    :attr:`DragableObjectBehavior.drag_cls` are in :attr:`drag_classes` will be
    dropable into the layout.
    """

    spacer_props = DictProperty({})
    """The properties of :attr:`spacer_widget`, which will be set according to
    this dict. This enables setting the sizing info for the preview widget in
    the layout.
    """

    spacer_widget = ObjectProperty(None)
    """The widget that is added to the layout to show where the dragged widget
    could be dropped.
    
    Defaults to :class:`SpacerWidget` if not set.
    """

    drag_classes = ListProperty([])
    """During a drag, the controller will try to preview and add the dragged
    :class:`DragableObjectBehavior` to this layout widget when it is over the
    widget's area. But, it will only do it if the dragged widget's 
    :attr:`DragableObjectBehavior.drag_cls` is in the layout's 
    :attr:`drag_classes`.
    
    This allows selecting which widgets can be dropped where.
    """

    drag_append_end = BooleanProperty(False)
    """Whether the :class:`DragableObjectBehavior` when dragged over the
    layout's area should be previewed and return an index that would add it at
    that location in its children, or if it will only support adding the widget
    to the end of children.
    """

    def __init__(self, **kwargs):
        super(DragableLayoutBehavior, self).__init__(**kwargs)
        self.spacer_widget = SpacerWidget()
        self.fbind('spacer_props', self._track_spacer_props)
        self._track_spacer_props()

    def _track_spacer_props(self, *largs):
        for key, value in self.spacer_props.items():
            setattr(self.spacer_widget, key, value)

    def _touch_uid(self):
        return '{}.{}'.format(self.__class__.__name__, self.uid)

    def compare_pos_to_widget(self, widget, pos):
        """After we call :meth:`get_widget_under_drag` to find the widget in
        ``children`` that is currently under the given pos (the current mouse
        pos that drags a widget), we call this to find whether the mouse pos
        indicates that the dragged widget needs to be added before or after
        the widget returned by :meth:`get_widget_under_drag`.

        It must return either the string `"before"`, or `"after"`.

        See :meth:`get_drop_insertion_index_move` and
        :meth:`get_drop_insertion_index_up`.
        """
        return 'before'

    def get_widget_under_drag(self, x, y):
        """Returns the widget in children that is under the given position
        (current mouse pos that drags the widget).

        See :meth:`get_drop_insertion_index_move` and
        :meth:`get_drop_insertion_index_up`.
        """
        for widget in self.children:
            if widget.collide_point(x, y):
                return widget
        return None

    def handle_drag_release(self, index, drag_widget):
        """This is called when a widget is dropped in the layout.
        ``index`` is the index in `children` where the widget should be added.
        ``drag_widget`` is the :class:`DragableObjectBehavior` that was dropped
        there.

        This must be overwritten by the inherited class to actually do the
        ``add_widget`` or something else.
        """
        pass

    def get_drop_insertion_index_move(self, x, y):
        """During a drag, it is called with when we need to figure out where
        to display the spacer widget in the layout.

        It calls :meth:`get_widget_under_drag` to find the widget in the layout
        currently under the mouse pos. Then it uses
        :meth:`compare_pos_to_widget` to figure out if it should be added
        before, or after that widget and returns the index in ``children``
        where the spacer should be added to represent the potential drop.

        If the spacer is under the current pos, or if no widget is under it
        (:meth:`get_widget_under_drag` returned ``None``), we return None,
        otherwise the index.
        """
        spacer = self.spacer_widget
        widget = self.get_widget_under_drag(x, y)
        if widget == spacer:
            return None

        if widget is None:
            if spacer.parent:
                self.remove_widget(spacer)
            self.add_widget(spacer)
            return None

        i = self.children.index(widget)
        j = None
        if self.compare_pos_to_widget(widget, (x, y)) == 'before':
            if i == len(self.children) - 1 or self.children[i + 1] != spacer:
                j = i + 1
        else:
            if not i or self.children[i - 1] != spacer:
                j = i
        return j

    def get_drop_insertion_index_up(self, x, y):
        """When dropping a drag, it is called to get the index in children of
        the layout where the widget was dropped and where it needs to be
        inserted.

        It calls :meth:`get_widget_under_drag` to find the widget in the layout
        currently under the mouse pos. Then it uses
        :meth:`compare_pos_to_widget` to figure out if it should be added
        before, or after that widget and returns the index in ``children``
        where the it should be added to complete the drop.
        """
        spacer = self.spacer_widget
        widget = self.get_widget_under_drag(x, y)
        if widget == spacer:
            index = self.children.index(spacer)
        elif widget is None:
            index = len(self.children)
        else:
            if self.compare_pos_to_widget(widget, (x, y)) == 'before':
                index = self.children.index(widget) + 1
            else:
                index = self.children.index(widget)

        if spacer.parent:
            i = self.children.index(spacer)
            self.remove_widget(spacer)
            if i < index:
                index -= 1
        return index

    def on_touch_move(self, touch):
        spacer = self.spacer_widget
        if touch.grab_current is not self:
            if not touch.ud.get(self._touch_uid()):
                # we haven't dealt with this before
                if self.collide_point(*touch.pos) and \
                        touch.ud.get('drag_cls') in self.drag_classes:
                    if super(DragableLayoutBehavior, self).on_touch_move(
                            touch):
                        return True
                    touch.grab(self)
                    touch.ud[self._touch_uid()] = True
                    x, y = touch.pos
                else:
                    return super(DragableLayoutBehavior, self).on_touch_move(
                        touch)
            else:
                # we have dealt with this touch before, do it when grab_current
                return True
        else:
            x, y = touch.pos
            if touch.ud.get('drag_cls') not in self.drag_classes or \
                    not collide_parent_tree(self, x, y):
                touch.ungrab(self)
                del touch.ud[self._touch_uid()]
                if spacer.parent:
                    self.remove_widget(spacer)
                return False
            if super(DragableLayoutBehavior, self).on_touch_move(touch):
                touch.ungrab(self)
                del touch.ud[self._touch_uid()]
                if spacer.parent:
                    self.remove_widget(spacer)
                return True

        if self.drag_append_end:
            if not spacer.parent:
                self.add_widget(spacer)
            return True

        j = self.get_drop_insertion_index_move(x, y)
        if j is not None:
            if spacer.parent:
                i = self.children.index(spacer)
                self.remove_widget(spacer)
                if i < j:
                    j -= 1
            self.add_widget(spacer, index=j)
        return True

    def on_touch_up(self, touch):
        spacer = self.spacer_widget
        if touch.grab_current is not self:
            if not touch.ud.get(self._touch_uid()):
                # we haven't dealt with this before
                if self.collide_point(*touch.pos) and \
                        touch.ud.get('drag_cls') in self.drag_classes:
                    if super(DragableLayoutBehavior, self).on_touch_up(touch):
                        return True
                    x, y = touch.pos
                else:
                    return super(DragableLayoutBehavior, self).on_touch_up(
                        touch)
            else:
                # we have dealt with this touch before, do it when grab_current
                return True
        else:
            touch.ungrab(self)
            del touch.ud[self._touch_uid()]
            x, y = touch.pos
            if touch.ud.get('drag_cls') not in self.drag_classes or \
                    not collide_parent_tree(self, x, y):
                if spacer.parent:
                    self.remove_widget(spacer)
                return False
            if super(DragableLayoutBehavior, self).on_touch_up(touch):
                if spacer.parent:
                    self.remove_widget(spacer)
                return True

        if self.drag_append_end:
            if spacer.parent:
                self.remove_widget(spacer)
            self.handle_drag_release(
                len(self.children), touch.ud['drag_widget'])
            return True

        self.handle_drag_release(
            self.get_drop_insertion_index_up(x, y), touch.ud['drag_widget'])
        return True


Factory.register('DragableObjectBehavior', DragableObjectBehavior)
Factory.register('DragableController', DragableController)
Factory.register('DragableLayoutBehavior', DragableLayoutBehavior)

if __name__ == '__main__':
    from kivy.app import runTouchApp
    from kivy.uix.label import Label
    from kivy.uix.boxlayout import BoxLayout

    class DragableBoxLayout(DragableLayoutBehavior, BoxLayout):

        def compare_pos_to_widget(self, widget, pos):
            if self.orientation == 'vertical':
                return 'before' if pos[1] >= widget.center_y else 'after'
            return 'before' if pos[0] < widget.center_x else 'after'

        def handle_drag_release(self, index, drag_widget):
            self.add_widget(drag_widget, index)

    class DragLabel(DragableObjectBehavior, Label):

        def initiate_drag(self):
            # during a drag, we remove the widget from the original location
            self.parent.remove_widget(self)

    widget = Builder.load_string('''
BoxLayout:
    DragableBoxLayout:
        drag_classes: ['label']
        orientation: 'vertical'
        Label:
            text: 'A'
        Label:
            text: 'A'
        Label:
            text: 'A'
        Label:
            text: 'A'
        Label:
            text: 'A'
        Label:
            text: 'A'
        DragableBoxLayout:
            padding: '20dp', 0
            drag_classes: ['label2']
            orientation: 'vertical'
            Label:
                text: 'B'
            Label:
                text: 'B'
            Label:
                text: 'B'
    DragableBoxLayout:
        drag_classes: ['label', 'label2']
        orientation: 'vertical'
        DragLabel:
            text: 'A*'
            drag_cls: 'label'
        DragLabel:
            text: 'B*'
            drag_cls: 'label2'
        DragLabel:
            text: 'A*'
            drag_cls: 'label'
        DragLabel:
            text: 'B*'
            drag_cls: 'label2'
        DragLabel:
            text: 'A*'
            drag_cls: 'label'
        DragLabel:
            text: 'B*'
            drag_cls: 'label2'
        DragLabel:
            text: 'A*'
            drag_cls: 'label'
    ''')

    runTouchApp(widget)
