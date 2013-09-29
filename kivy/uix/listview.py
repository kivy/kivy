'''
List View
=========

.. versionadded:: 1.5

.. warning::

    This code is still experimental, and its API is subject to change in a
    future version.

The :class:`~kivy.uix.listview.ListView` widget provides a scrollable/pannable
viewport that is clipped at the scrollview's bounding box, which contains
list item view instances.

:class:`~kivy.uix.listview.ListView` implements :class:`AbstractView` as a
vertical scrollable list. :class:`AbstractView` has one property, adapter.
:class:`~kivy.uix.listview.ListView` sets adapter to one of:
:class:`~kivy.adapters.listadapter.ListAdapter`, or
:class:`~kivy.adapters.dictadapter.DictAdapter`.

.. versionchanged:: 1.8.0

    The underlying adapter and selection system were changed in support of
    operations here, which needed to receive more detailed information about
    changes to data held in adapters, either in ListAdapter or DictAdapter. The
    data_changed() method replaces a call to bind_triggers_to_view(), now
    removed. Previously, with limited information about data change, only broad
    scrolling and child handling reactions could be made. Now, in the new
    data_changed() method, there is an opportunity to react to individual item
    resets, to insertions, deletions, sort, etc. For these reactions, sometimes
    it is necessary to remove and force re-creation of views, sometimes it is
    necessary to make a specific scroll action, and so on.

    Removed ListItemLabel.

    SelectableView now subclasses ButtonBehavior, and has a
    carry_selection_to_children property.

    CompositeListItem now has a bind_selection_from_children property. Also,
    its is_representing_cls is now removed.

    For scrolling, added scroll_advance. Removed _count, which was unused.

    With the removal of adapters/, only kivy.adapter.py remains, which is the
    base class for ListView. There were many modifications to make the code
    formerly in ListAdapter and its ListOpHandler work in ListView directly,
    and in the new ListController, which takes over some of the functionality
    of ListAdapter. One important change is the use of binding classes,
    DataBinding and SelectionBinding, in the connection to ListController, and
    as used in ListController for binding to data sources.

Introduction
------------

Lists are central parts of many software projects. Kivy's approach to lists,
from Kivy 1.5 to 1.8, started with an emphasis on adapters, an influence from
the Android platform.  This approach was replaced in Kivy 1.8 with a
controller-based system that has similarities to Cocoa and SproutCore. Much of
the code in the former ListAdapter and DictAdapter was reused in ListController
and DictController, and there is still a lone Adapter base class for ListView.
If you are familiar with the former adapter-based approach, you will want to
study the examples and controller code for differences.

There is more to the change than a different set of names; the use of
controllers allows a better separation of the "middle" logic code layer of a
typical application from the "top" layer of views.

Narrative discussion is provided below for using controllers, properties, and
other constructs with ListView and related widgets, but you can learn a lot by
running and perusing the code for the following examples:

    * kivy/examples/widgets/lists/list_basic.py
    * kivy/examples/widgets/lists/list_cascade.py
    * kivy/examples/widgets/lists/list_composite.py
    * kivy/examples/widgets/lists/list_data_changes.py
    * kivy/examples/widgets/lists/list_data_dynamic.py
    * kivy/examples/widgets/lists/list_master_detail.py
    * kivy/examples/widgets/lists/list_of_carousels.py
    * kivy/examples/widgets/lists/list_scroll.py
    * kivy/examples/widgets/lists/list_selection_binding.py

These examples have a common procedure for setting up listviews:

    1) Make the controllers needed and set bindings to connect them.

    2) Connect listviews to their controllers.

    3) If data has not yet been set when controllers were created, set data in
       the controllers when appropriate to make the listviews populate and
       appear on the screen.

This fits the traditional model-view-controller paradigm:

    * Views such as ListView are on the top.

    * Controllers, such as ListController, are in the middle, forming the
      all-important bridge between data and views.

    * Data, using the SelectableDataItem model class for each data item, are on
      the bottom.

Many of the examples feature selection. Selection is important for several
reasons:

    * controls how selection operates within a given list controller, and in
      the listview that uses it:

        - selection_mode can be 'single' or 'multiple'; if 'single', only one
          item is allowed to be selected at a time

        - selection can be automatic or not (allow_empty_selection can be
          False, which means that if ever selection is empty, especially on the
          initial load of data, the first item is selected automatically)

    * offers a powerful way, along with appropriate bindings, for connecting
      controllers, from one list controller to another, and for the very common
      need to bind the first selected item in a list to an object controller.

      For example, a list controller called fruits_controller would have
      selection enabled, and an object controller, current_fruit_controller,
      would be bound to the first selected item in fruits_controller. A
      listview using fruits_controller and a view using
      current_fruit_controller would automatically reflect any changes in fruit
      selection.

The examples are short one-file apps, which is convenient for learning, but do
not illustrate a larger app's layout, which might be::

    project/

        __init__.py
        main.py

        controllers/
            __init__.py
            this_controller.py
            that_controller.py

        views/
            __init__.py
            this_view.py
            that_view.py

The project/ directory would contain the main.py and other principle files. The
project/ directory and the two subdirectories would be set up for proper Python
imports by use of the empty __init__.py file in each, an odd but faithful
Python idiom. The controllers/ directory would contain multiple files, one for
each controller in the app. The views/ directory would contain listviews and
other widgets used in the app. Keep this example structure in mind when moving
from the simple one-file examples to a real app.

Find your own way of reading the documentation here, examining the source code
for the example apps, and running the examples. Some may prefer to read the
documentation through first, others may want to run the examples and view their
code. No matter what you do, going back and forth will likely be needed.

Basic Example
-------------

Here's how to make a listview with 100 items::

    # Actual file is kivy/examples/widgets/lists/list_basic.py.
    from kivy.binding import DataBinding
    from kivy.controllers.listcontroller import ListController
    from kivy.models import SelectableStringItem
    from kivy.uix.listview import ListItemButton
    from kivy.uix.listview import ListView
    from kivy.uix.gridlayout import GridLayout


    class MainView(GridLayout):

        def __init__(self, **kwargs):
            kwargs['cols'] = 1
            super(MainView, self).__init__(**kwargs)

            def list_item_class_args(index, data_item):
                return {'text': data_item.text,
                        'size_hint_y': None,
                        'height': 25}

            list_controller = ListController(
                data=[SelectableStringItem(text=str(index))
                          for index in range(100)],
                selection_mode='single',
                allow_empty_selection=False)

            list_view = ListView(
                data_binding=DataBinding(
                    source=list_controller),
                args_converter=list_item_class_args,
                list_item_class=ListItemButton)

            self.add_widget(list_view)

    if __name__ == '__main__':
        from kivy.base import runTouchApp
        runTouchApp(MainView(width=800))

This is about as short as we can make an app with a listview. There are three
components added to the MainView:

    - a helper args converter function to convert each data item into arguments
      to pass for each list item creation, which you see in the ListView
      declaration is ListItemButton,

    - a list controller to hold the data and selection, which you see is
      configured for single, automatic selection,

    - a list view widget, which uses the list controller and the args converter
      function.

We can make the exact same app, declaring the listview using the kv language::

    # Actual file is kivy/examples/widgets/lists/list_basic.py.
    from kivy.app import App
    from kivy.binding import DataBinding
    from kivy.controllers.listcontroller import ListController
    from kivy.lang import Builder
    from kivy.models import SelectableStringItem
    from kivy.uix.gridlayout import GridLayout

    Builder.load_string("""
    #:import DataBinding kivy.binding.DataBinding
    #:import binding_modes kivy.enums.binding_modes
    #:import ListItemButton kivy.uix.listview.ListItemButton

    <MainView>:
        cols: 1

        ListView:
            list_item_class: 'ListItemButton'
            args_converter: app.list_item_class_args
            DataBinding:
                source: app.list_controller
    """)


    class MainView(GridLayout):
        pass


    class BasicApp(App):

        def __init__(self, **kwargs):
            super(BasicApp, self).__init__(**kwargs)

            self.list_controller = ListController(
                data=[SelectableStringItem(text=str(index))
                          for index in range(100)],
                selection_mode='single',
                allow_empty_selection=False)

        def list_item_class_args(self, index, data_item):
            return {'text': data_item.text,
                    'size_hint_y': None,
                    'height': 25}

        def build(self):
            return MainView(width=800)

    if __name__ == '__main__':
        BasicApp().run()

Some differences to note, compared to the first, non-kv version:

    - We need to declare an App class, so that we can use it for a convenient
      global storage location, to which we use the handy app.attribute
      references in kv.

    - The MainView widget is declared in kv, and there is a matching class
      defined in Python, in this case just the bare declaration with pass.

    - We added a build() method to return the MainView instance.

    - In the ListView kv declaration, we used the kv syntax and indentation for
      list_item_class, args_converter, and DataBinding.

Using Dynamic Classes as List Item Classes
------------------------------------------

See the list_cascade.py example.

Using CompositeListItem
-----------------------

See the list_composite example.

Changing Data On the Fly
------------------------

ListController uses a special version of ListProperty, that under the hood uses
a class called OpObservableList. The standard ListProperty uses a class called
ObservableList (without the Op prefix). The difference is that the standard
ListProperty dispatches data change events when anything changes, but without
providing any means to determine what changed. The enhanced ListProperty using
OpObservableList dispatches for each possible 'op' that could happen, including
wholesale set (data=[new data]), insert (data[5] = 'cow'), delete
(del data[3]), and all the others that are possible for a Python list.

DictController uses a similar enhanced version of DictProperty, which uses an
OpObservableDict internally.

These detailed dispatches with op change info allow making appropriate updates
to the user interface when data changes.

So, let your app change data, and see the user interface update.

See the list_data_changes.py and list_data_dynamic.py examples.

If you take on the somewhat advanced task of making your own widgets, study how
ListController, and its data_changed() method, and ListView, and its op handler
and data_changed() method, and UI updating methods, react to the individual op
change events.

List Scrolling
--------------

See the list_scroll.py example for examples of using the scroll_to() and
related API.

Using ListView with other Kivy Widgets
--------------------------------------

Your mileage may vary on this, but experiment with using widgets for the
list_item_class.

See the list_of_carousels.py example for one attempt.

The Importance of Controllers and Selection
-------------------------------------------

Controllers provide a basis for creativity in the main structure of an app.
Bridging data to views, controllers form the logical structure, which in
general terms can be imagined as a tree, or graph. Controllers, in Kivy speak,
are EventDispatcher containers of properties that occupy nodes of the logic
tree or graph. The data and selection properties are special and wired-in to
list controllers.  Other properties used in a controller, include basic Python
primitives and Kivy properties such as ListProperty, DictProperty,
ObjectProperty, AliasProperty, and NumericProperty. These properties are used
to complete the body of the controller, centered around data and/or selection,
along with specialized methods needed for the particular app.

Bindings connect controllers. Two bindings are cater-made for controllers,
DataBinding and SelectionBinding. In the examples you will see data for fruits
used, where we have fruit categories (tree fruits, citrus fruits, etc.) and
indivdual fruits that fit into these categories (Apple, Peach, Kiwi, etc.).
Let's go through the process of writing the small fruits app in
list_cascade.py. If you haven't done so already, open that file in your editor,
and run the app. Click around to see how it behaves.

It isn't hard to see what controllers are needed for the basic data here.  We
need a fruits controller to contain the indidual fruits data. We have a notion
of fruit categories, so we need a fruit categories controller. How do we get a
list of the fruits in a given category? Some of this depends on the way the
base data is structured, but we see that in this case, luckily, the base data
is stored in Python dictionaries (You should structure your base data with
controllers in mind, if you have that luxury). We learn that if we can have a
category, we can get the fruits for it by using the category as a key in to the
base data dictionary. We make a new controller called
current_fruits_controller, to which we add a helper filter function called
get_current_fruits(). We use a binding to link this helper function to the data
property of the controller. But how to we link this current_fruits_controller
to the category, which is in the categories_controller? With another binding,
in this case with a binding to the selection property of the
category_controller, along with the very handy setting of the binding mode to
FIRST_ITEM. So far, we have::

     categories_controller      categories           current_fruits_controller
       (ListController)         selection                 (ListController)
    -----------------------  ---------------        ---------------------------
    Citrus Fruits << sel     [Citrus Fruits]     /  Grapefruit << sel
    Melons                         ^             |  Lemon
    Tree Fruits                    --------------|  Lime
    Other Fruits              FIRST_ITEM    data |  Orange
                                                 \  Tangerine

    (single selection in effect)                   (single selection in effect)
    (auto selection in effect)                     (auto selection in effect)

Some points::

    * Selection is always a list, so even if we know there will only be one
      item allowed, as with single selection, in accessing it, we must use the
      FIRST_ITEM binding mode. In other uses, as illustrated in the example
      called list_selection_binding.py, we may want to bind to the entire
      selection.

    * Selection is a key mechanism provided by the controller -- without
      selection, a list is just a boring list. Get selection on the brain and
      keep it there, for lists at least.

    * We haven't connected these controllers to list views. We can imagine a
      user interface, but mainly now we are still thinking in "controller
      mode," where we are concerned with data and logic structure. Of course,
      we need to go back and forth, to also think about the user interface
      components and what data is needed, but you will get the hang of the way
      controllers are constructed in the "headless" realm of pure programming.

    * A good rule of thumb to follow is to create new controllers at the first
      notion of subsetting data. Although it is not apparent from an example
      with just two controllers, generally you should create several small
      controllers, instead of a few monolithic controllers.

    * The phrase "auto selection" refers to the result of setting
      allow_empty_selection to False -- the system will never let selection be
      empty, which makes the connections between controllers work, at those
      that are bound together via selection, which is most common in
      programming.

It is now easy to make list views for categories and current fruits. We bind
the catetories_controller to the categories list view, and we bind the
current_fruits_controller to current fruits list view. Done. (the main work was
in setting up the controllers).

The list_cascade.py example illustrates another important concept for
controllers and selection. The third user interface component, to the right of
the two lists described above, is a detail view for the selected fruit within
the current fruits list::

     current_fruits_controller    current fruits      current_fruit_controller
          (ListController)          selection           (ObjectController)
    --------------------------- -----------------    --------------------------
    Grapefruit << sel            [Grapefruit]      / Name: Grapefruit
    Lemon                             ^            | Calories: 160
    Lime                              -------------| Calories from fat: 60
    Orange                       FIRST_ITEM   data | Total fat: 2
    Tangerine                                      | Sodium: 0

    (single selection in effect)

More points::

    * We use the same binding approach as above: bind to the selection of a
      list controller, using binding mode FIRST_ITEM.

    * The controller on the right is an ObjectController, for containing a
      single object as its single data item. The object can be anything (even a
      listor dict), but in this case it is the selected current fruit,
      Grapefruit.

    * Object controllers are the linchpin for the wheel for controllers in
      general, serving to link list controllers to one another.

    * When you examine the code, you see that a widget called ObjectView is
      bound to the current fruit ObjectController. This is a handy generic view
      for a single item, sort of like ListView without the list -- in fact, the
      code for ObjectView was adapted from ListView, so you will see welcome
      similarities.

Other Examples
--------------

What can we do with controllers and selection? Combining selection with the
system of bindings in Kivy, we can build a wide range of user interface
designs.

We could make data items that contain the names of dog breeds, and connect the
selection of dog breed to the display of details in another view, which would
update automatically on selection. This is done via a binding to selection.
See the example called list_master_detail.py, and imagine that the list on the
left would be a list of dog breeds, and the detail view on the right would show
details for a selected dog breed.

In another example, we could set the selection_mode of a listview to
'multiple', and load it with a list of answers to a multiple-choice question.
The question could have several correct answers. A color swatch view could be
bound to selection change, as above, so that it turns green as soon as the
correct choices are made, unless the number of touches exeeds a limit, when the
answer session would be terminated. See the list_cascade.py example, which
features a thumbnail image, to get some ideas. See the
list_selection_binding.py example for how to connect the selection of one
controller to the data of another.

There are so many ways that listviews and Kivy bindings functionality can be
used, that we have only scratched the surface here.
'''

__all__ = ('SelectableView', 'SelectableStringItem', 'ListItemLabel',
           'ListItemButton', 'CompositeListItem', 'ListView', )

from math import ceil, floor

from kivy.adapter import Adapter
from kivy.binding import DataBinding
from kivy.binding import SelectionBinding
from kivy.clock import Clock

from kivy.event import EventDispatcher
from kivy.lang import Builder

from kivy.properties import BooleanProperty
from kivy.properties import DictProperty
from kivy.properties import ListProperty
from kivy.properties import NumericProperty
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty

from kivy.properties import DictOpInfo
from kivy.properties import ListOpHandler
from kivy.properties import ListOpInfo

from kivy.selection import SelectionTool

from kivy.uix.abstractview import AbstractView
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget


class SelectableView(ButtonBehavior):
    '''The :class:`~kivy.uix.listview.SelectableView` mixin is used to design
    list item and other classes.

    For children, there are two directions for selection, from parent to
    children, and from a child up to parent. The default for
    carry_selection_to_children is True, so selection of children will follow
    that of the parent. This can be handy if the SelectableView is treated as a
    container, without its own cosmetic selection effects, and the UI
    reflection of selection is done by the children (if the SelectableView
    contains a combination of ListItemButtons and Labels for a listview
    row item, the buttons will show selection of the row).

    For the other direction, depending on the layout, the parent (the
    SelectableView) may get events such as on_release. Or, if children
    are ListItemButtons, they might get the events. In the second case, if
    children are to fire selection for the parent, do something like the
    following on the child:

        on_release: self.parent.trigger_action(duration=0)

    Depending on the need, on_release: could be, among other possibilities, an
    on_touch_up: set. SelectableView, the parent, mixes in ButtonBehavior,
    which has the trigger_action() method.

    .. versionadded:: 1.5

    '''

    index = NumericProperty(-1)
    '''The index into the underlying data list item, to the data item this
    view represents.

    :data:`index` is a :class:`~kivy.properties.NumericProperty`, default
    to -1.
    '''

    ksel = ObjectProperty(None)
    '''The selection tool for the view item.

    .. versionadded:: 1.8

    :data:`ksel` is a SelectionTool instance, set either from kwargs or to
    False after the super() call in __init__().
    '''

    def __init__(self, **kwargs):
        super(SelectableView, self).__init__(**kwargs)
        if 'ksel' not in kwargs:
            self.ksel = SelectionTool(False)
        self.ksel.bind_to(self.selection_changed)

    def selection_changed(self, *args):
        if args[1]:
            self.do_select_effects(args)
        else:
            self.do_deselect_effects(args)

    def do_select_effects(self, *args):
        '''The list item is responsible for updating the display for being
        selected, if desired.

        .. versionadded:: 1.8
        '''
        for c in self.children:
            if hasattr(c, 'do_select_effects'):
                c.do_select_effects(args)

    def do_deselect_effects(self, *args):
        '''The list item is responsible for updating the display for being
        deselected, if desired.

        .. versionadded:: 1.8
        '''
        for c in self.children:
            if hasattr(c, 'do_deselect_effects'):
                c.do_deselect_effects(args)


class ListItemButton(SelectableView, Button):
    ''':class:`~kivy.uix.listview.ListItemButton` mixes
    :class:`~kivy.uix.listview.SelectableView` with
    :class:`~kivy.uix.button.Button` to produce a button suitable for use in
    :class:`~kivy.uix.listview.ListView`.

    .. versionadded:: 1.5

    '''

    selected_color = ListProperty([1., 0., 0., 1])
    '''

    :data:`selected_color` is a :class:`~kivy.properties.ListProperty`,
    default to [1., 0., 0., 1].
    '''

    deselected_color = ListProperty([0., 1., 0., 1])
    '''
    :data:`selected_color` is a :class:`~kivy.properties.ListProperty`,
    default to [0., 1., 0., 1].
    '''

    def __init__(self, **kwargs):
        super(ListItemButton, self).__init__(**kwargs)

        # Set Button bg color to be deselected_color.
        self.background_color = self.deselected_color

    def do_select_effects(self, *args):
        '''The default cosmetic reflection of selection state is the background
        color. To change, subclass ListItemButton and override this method,
        making sure to call super(), as shown, or make a new subclass of
        SelectableView.

        .. versionadded:: 1.8
        '''
        super(ListItemButton, self).do_select_effects(args)
        self.background_color = self.selected_color

    def do_deselect_effects(self, *args):
        '''The default cosmetic reflection of selection state is the background
        color. To change, subclass ListItemButton and override this method,
        making sure to call super(), as shown, or make a new subclass of
        SelectableView.

        .. versionadded:: 1.8
        '''
        super(ListItemButton, self).do_deselect_effects(args)
        self.background_color = self.deselected_color

    def __repr__(self):
        return '<%s text=%s>' % (self.__class__.__name__, self.text)


class CompositeListItem(SelectableView, BoxLayout):
    ''':class:`~kivy.uix.listview.CompositeListItem` mixes
    :class:`~kivy.uix.listview.SelectableView` with :class:`BoxLayout` for a
    generic container-style list item.

    .. versionadded:: 1.5

    '''

    background_color = ListProperty([1, 1, 1, 1])
    '''ListItem sublasses Button, which has background_color, but
    for a composite list item, we must add this property.

    :data:`background_color` is a :class:`~kivy.properties.ListProperty`,
    default to [1, 1, 1, 1].
    '''

    selected_color = ListProperty([1., 0., 0., 1])
    '''
    :data:`selected_color` is a :class:`~kivy.properties.ListProperty`,
    default to [1., 0., 0., 1].
    '''

    deselected_color = ListProperty([.33, .33, .33, 1])
    '''
    :data:`deselected_color` is a :class:`~kivy.properties.ListProperty`,
    default to [.33, .33, .33, 1].
    '''

    bind_selection_from_children = BooleanProperty(True)
    '''The selectable children of CompositeListItem, depending on use, may need
    to fire selection events for the CompositeListItem. If so, set this to True
    so that bindings are created on instantiation of the children.

    .. versionadded:: 1.8
    '''

    component_args = ListProperty([])
    '''component_args is a list of dictionaries. Each component of the
    composite needs to be instantiated for each data item, so there must be
    individual sets of arguments for each component.

    :data:`component_args` is a :class:`~kivy.properties.ListProperty`,
    with default [].

    .. versionadded:: 1.8
    '''

    def __init__(self, **kwargs):
        super(CompositeListItem, self).__init__(**kwargs)

        # There is an index to the data item this composite list item view
        # represents. Get it from kwargs and pass it along to children in the
        # loop below.
        index = kwargs['index']

        for component_args_dict in self.component_args:
            cls = component_args_dict['component_class']
            component_kwargs = \
                    component_args_dict.get('component_kwargs', None)

            if component_kwargs:
                component_kwargs['index'] = index

                if 'text' not in component_kwargs:
                    component_kwargs['text'] = kwargs['text']
            else:
                component_kwargs = {}
                component_kwargs['index'] = index
                if 'text' in kwargs:
                    component_kwargs['text'] = kwargs['text']

            child = cls(**component_kwargs)

            self.add_widget(child)

    def bind_composite(self, callback):

        self.bind(on_release=callback)

        if self.bind_selection_from_children:
            for child in self.children:
                if hasattr(child, 'ksel'):
                    child.bind(on_release=self.call_trigger_action)

    def call_trigger_action(self, *args):
        self.trigger_action(duration=0)

    def do_select_effects(self, *args):
        super(CompositeListItem, self).do_select_effects(args)
        self.background_color = self.selected_color

    def do_deselect_effects(self, *args):
        super(CompositeListItem, self).do_deselect_effects(args)
        self.background_color = self.deselected_color


class ListItemLabel(SelectableView, Label):
    text = StringProperty('')

    def __init__(self, **kwargs):
        super(ListItemLabel, self).__init__(**kwargs)

list_item_class_args = lambda row_index, x: {'text': x,
                                             'size_hint_y': None,
                                             'height': 25}
'''
List item args converters

The default list item args converter for list adapters is a function (shown
below) that takes a row index and a string. It returns a dict with the string
as the *text* item, along with two properties suited for simple text items with
a height of 25.

Argument converters may be normal functions or, as in the case of the default
args converter, lambdas::

    list_item_class_args = lambda row_index, x: {'text': x,
                                                     'size_hint_y': None,
                                                     'height': 25}
.. versionadded:: 1.5

.. versionchanged:: 1.8

    list_item_class_args absorbed from kivy.adapters.

'''


class DataOpHandler(ListOpHandler):
    ''':class:`~kivy.adapters.list_ops.DataOpHandler` is a helper class
    that reacts to the following operations that are possible for a data
    OpObservableList (OOL) instance:

        handle_add_first_item_op()

            OOL_append
            OOL_extend
            OOL_insert

        handle_add_op()

            OOL_append
            OOL_extend
            OOL_iadd
            OOL_imul

        handle_insert_op()

            OOL_insert

        handle_setitem_op()

            OOL_setitem

        handle_setslice_op()

            OOL_setslice

        handle_delete_op()

            OOL_delitem
            OOL_delslice
            OOL_remove
            OOL_pop

        handle_sort_op()

            OOL_sort
            OOL_reverse

        These methods adjust cached_views and selection.

    .. versionadded:: 1.8

        Modified from adapters system.
    '''

    def __init__(self, listview, duplicates_allowed):

        self.listview = listview
        self.duplicates_allowed = duplicates_allowed

        super(DataOpHandler, self).__init__()

    def data_changed(self, *args):

        if not args:
            return

        if not self.listview.data_binding:
            return

        # NOTE: args[1] is the modified list.

        data = self.listview.data_binding.source.data

        if not hasattr(data, 'op_change_info'):
            op_info = ListOpInfo('OOL_set', 0, 0)
        else:
            op_info = data.op_change_info

            if not op_info:
                op_info = ListOpInfo('OOL_set', 0, 0)

        # Make a copy in the listview for more convenient access.
        self.listview.data_op_info = op_info

        op = op_info.op_name
        start_index = op_info.start_index
        end_index = op_info.end_index

        print 'ListView data_changed, op is', op
        if op == 'OOL_sort_start':
            self.sort_started(*args)
            return

        if op == 'OOL_set':

            self.handle_set()

        elif (len(data) == 1
                and op in ['OOL_append',
                           'OOL_insert',
                           'OOL_extend']):

            self.handle_add_first_item_op()

        else:

            if op in ['OOL_iadd',
                      'OOL_imul',
                      'OOL_append',
                      'OOL_extend']:

                self.handle_add_op()

            elif op in ['OOL_setitem']:

                self.handle_setitem_op(start_index)

            elif op in ['OOL_setslice']:

                self.handle_setslice_op(start_index, end_index)

            elif op in ['OOL_insert']:

                self.handle_insert_op(start_index)

            elif op in ['OOL_delitem',
                        'OOL_delslice',
                        'OOL_remove',
                        'OOL_pop']:

                self.handle_delete_op(start_index, end_index)

            elif op in ['OOL_sort',
                        'OOL_reverse']:

                self.handle_sort_op()

    def handle_set(self):

        self.listview.cached_views.clear()
        self.listview.update_ui_for_data_changes()
        self.listview.update_ui_for_selection_change()
        #self.listview.initialize_selection()

    def handle_add_first_item_op(self):
        '''Special case: deletion resulted in no data, leading up to the
        present op, which adds one or more items. Cached views should
        have already been treated.  Call check_for_empty_selection()
        to re-establish selection if needed.
        '''
        self.listview.update_ui_for_selection_change()
        #self.listview.check_for_empty_selection()

    def handle_add_op(self):
        '''An item was added to the end of the list, or the list was extended
        by several items. This shouldn't affect anything here, as cached_views
        items can be built as needed through normal get_view() calls to build
        views for the added items.
        '''
        self.listview.update_ui_for_data_changes()

    def handle_insert_op(self, index):
        '''An item was added at index. Adjust the indices of any cached_view
        items affected.
        '''

        new_cached_views = {}

        for k, v in self.listview.cached_views.iteritems():

            if k < index:
                new_cached_views[k] = self.listview.cached_views[k]
            else:
                new_cached_views[k + 1] = self.listview.cached_views[k]
                new_cached_views[k + 1].index += 1

        self.listview.cached_views = new_cached_views
        self.listview.update_ui_for_data_changes()

    def handle_setitem_op(self, index):
        '''Force a rebuild of the item view for which the associated data item
        has changed.  If the item view was selected before, maintain the
        selection.
        '''

        del self.listview.cached_views[index]
        #item_view = self.listview.get_view(index)
        #if item_view and is_selected:
            #self.listview.handle_selection(item_view)
        self.listview.update_ui_for_data_changes()
        #self.listview.update_ui_for_selection_change()

    def handle_setslice_op(self, start_index, end_index):
        '''Force a rebuild of item views for which data items have changed.
        Although it is hard to guess what might be preferred, a "positional"
        priority for selection is observed here, where the indices of selected
        item views is maintained. We call check_for_empty_selection() if no
        selection remains after the op.
        '''

        changed_indices = range(start_index, end_index + 1)

        is_selected_indices = []
        for i in changed_indices:
            item_view = self.listview.cached_views[i]
            if item_view.ksel.is_selected():
                is_selected_indices.append(i)

        for i in reversed(changed_indices):
            del self.listview.cached_views[i]

#        for i in changed_indices:
#            item_view = self.listview.get_view(i)
#            if item_view and item_view.index in is_selected_indices:
#                self.listview.handle_selection(item_view)

        # Remove deleted views from selection.
        #for selected_index in [item.index for item in self.selection]:
#        for sel in self.listview.selection:
#            if sel.index in changed_indices:
#                self.listview.selection.remove(sel)

        # Do a check_for_empty_selection type step, if data remains.
#        if (len(data) > 0
#                and not self.listview.selection
#                and not self.listview.allow_empty_selection):
#            # Find a good index to select, if the deletion results in
#            # no selection, which is common, as the selected item is
#            # often the one deleted.
#            if start_index < len(data):
#                new_sel_index = start_index
#            else:
#                new_sel_index = start_index - 1
#            v = self.listview.get_view(new_sel_index)
#            if v is not None:
#                self.listview.handle_selection(v)
        self.listview.update_ui_for_data_changes()
        self.listview.update_ui_for_selection_change()

    def handle_delete_op(self, start_index, end_index):
        '''An item has been deleted. Reset the index for item views affected.
        '''

        deleted_indices = range(start_index, end_index + 1)

#        for index in reversed(deleted_indices):
#            del self.listview.cached_views[index]

        # Delete views from cache.
        new_cached_views = {}

        i = 0
        for k, v in self.listview.cached_views.iteritems():
            if k not in deleted_indices:
                new_cached_views[i] = self.listview.cached_views[k]
                if k >= start_index:
                    new_cached_views[i].index = i
                i += 1

        self.listview.cached_views = new_cached_views

        # Remove deleted views from selection.
        #for selected_index in [item.index for item in self.selection]:
#        for sel in self.listview.selection:
#            if sel.index in deleted_indices:
#                self.listview.selection.remove(sel)

        # Do a check_for_empty_selection type step, if data remains.
#        if (len(data) > 0
#                and not self.listview.selection
#                and not self.listview.allow_empty_selection):
#            # Find a good index to select, if the deletion results in
#            # no selection, which is common, as the selected item is
#            # often the one deleted.
#            if start_index < len(data):
#                new_sel_index = start_index
#            else:
#                new_sel_index = start_index - 1
#            v = self.listview.get_view(new_sel_index)
#            if v is not None:
#                self.listview.handle_selection(v)
        self.listview.update_ui_for_data_changes()
        #self.listview.update_ui_for_selection_change()

    def sort_started(self, *args):

        # This temporary association has keys as the indices of the adapter's
        # cached_views and the adapter's data items, for use in post-sort
        # widget reordering.

        presort_indices_and_items = {}

        data = self.listview.data_binding.source.data

        if self.duplicates_allowed:
            for i in self.listview.cached_views:
                data_item = data[i]
                if isinstance(data_item, str):
                    duplicates = \
                            sorted([j for j, s in enumerate(data)
                                                 if s == data_item])
                    pos_in_instances = duplicates.index(i)
                else:
                    pos_in_instances = 0

                presort_indices_and_items[i] = \
                            {'data_item': data_item,
                             'pos_in_instances': pos_in_instances}
        else:
            for i in self.listview.cached_views:
                data_item = data[i]
                pos_in_instances = 0
                presort_indices_and_items[i] = \
                            {'data_item': data_item,
                             'pos_in_instances': pos_in_instances}

        self.presort_indices_and_items = presort_indices_and_items

        data.finish_sort_op()

    def handle_sort_op(self):
        '''Data has been sorted or reversed. Use the pre-sort information about
        previous ordering, stored in the associated ChangeMonitor instance, to
        reset the index of each cached item view, instead of deleting
        cached_views entirely.
        '''

        presort_indices_and_items = self.presort_indices_and_items

        data = self.listview.data_binding.source.data

        # We have an association of presort indices with data items.
        # Where is each data item after sort? Change the index of the
        # item_view to match present position.
        new_cached_views = {}

        if self.duplicates_allowed:
            for i in self.listview.cached_views:
                item_view = self.listview.cached_views[i]
                old_i = item_view.index
                data_item = presort_indices_and_items[old_i]['data_item']
                if isinstance(data_item, str):
                    duplicates = sorted(
                        [j for j, s in enumerate(data)
                                if s == data_item])
                    pos_in_instances = \
                        presort_indices_and_items[old_i]['pos_in_instances']
                    postsort_index = duplicates[pos_in_instances]
                else:
                    postsort_index = data.index(data_item)
                item_view.index = postsort_index
                new_cached_views[postsort_index] = item_view
        else:
            for i in self.listview.cached_views:
                item_view = self.listview.cached_views[i]
                old_i = item_view.index
                data_item = presort_indices_and_items[old_i]['data_item']
                postsort_index = data.index(data_item)
                item_view.index = postsort_index
                new_cached_views[postsort_index] = item_view

        self.listview.cached_views = new_cached_views

        # Clear temporary storage.
        self.presort_indices_and_items.clear()

        self.listview.update_ui_for_data_changes()
        self.listview.update_ui_for_selection_change()

Builder.load_string('''
<ListView>:
    container: container
    scrollview: scrollview
    ScrollView:
        id: scrollview
        pos: root.pos
        on_scroll_y: root._scroll(args[1])
        do_scroll_x: False
        GridLayout:
            id: container
            cols: 1
            size_hint_y: None
''')


class ListView(Adapter, AbstractView, EventDispatcher):
    ''':class:`~kivy.uix.listview.ListView` is a primary high-level widget,
    handling the common task of presenting items in a scrolling list.
    Flexibility is afforded by use of a variety of adapters to interface with
    data.

    The adapter property comes via the mixed in
    :class:`~kivy.uix.abstractview.AbstractView` class.

    :class:`~kivy.uix.listview.ListView` also subclasses
    :class:`EventDispatcher` for scrolling.  The event *on_scroll_complete* is
    used in refreshing the main view.

    For a simple list of string items, without selection, use
    :class:`~kivy.adapters.simplelistadapter.SimpleListAdapter`. For list items
    that respond to selection, ranging from simple items to advanced
    composites, use :class:`~kivy.adapters.listadapter.ListAdapter`.  For an
    alternate powerful adapter, use
    :class:`~kivy.adapters.dictadapter.DictAdapter`, rounding out the choice
    for designing highly interactive lists.

    :Events:
        `on_scroll_complete`: (boolean, )
            Fired when scrolling completes.

    .. versionadded:: 1.5

    .. versionchanged:: 1.8

        Removed item_strings, after having first removed SimpleListAdapter,
        because with the new controller system, it is easier to describe for
        new developers how to make a controller with a list of strings.
        Although originally intended as a way to make simple use easier, it
        added more complication really. Part of this relates to the way list
        items must now conform by having a ksel object (which can be had by
        subclassing SelectableDataItem).

        Added update methods for responding to data and selection changes.

        Added bindings system for data and selection, including initialization
        for bindings from Python init and from a special init function from kv.

        Improved scrolling and documentation. Added a scroll_to() related API.

    '''

    divider = ObjectProperty(None)
    '''[TODO] Not used.
    '''

    divider_height = NumericProperty(2)
    '''[TODO] Not used.
    '''

    data_op_handler = ObjectProperty(None)
    '''An instance of :class:`~kivy.properties.ListOpHandler`,
    containing methods that perform steps needed after the data has changed.
    The methods are responsible for updating cached_views and selection.

    :data:`data_op_handler` is a :class:`~kivy.properties.ObjectProperty` and
    defaults to None. It is instantiated and set on init.

    .. versionadded:: 1.8

    '''

    data_op_info = ObjectProperty(None)
    selection_op_info = ObjectProperty(None)

    container = ObjectProperty(None)
    '''The container is a :class:`~kivy.uix.gridlayout.GridLayout` widget held
    within a :class:`~kivy.uix.scrollview.ScrollView` widget.  (See the
    associated kv block in the Builder.load_string() setup). Item view
    instances managed and provided by the adapter are added to this container.
    The container is cleared with a call to clear_widgets() when the list is
    rebuilt by the populate() method. A padding
    :class:`~kivy.uix.widget.Widget` instance is also added as needed,
    depending on the row height calculations.

    :data:`container` is an :class:`~kivy.properties.ObjectProperty`,
    default to None.
    '''

    row_height = NumericProperty(25)
    '''The row_height property is calculated on the basis of the height of the
    container and the count of items.

    :data:`row_height` is a :class:`~kivy.properties.NumericProperty`,
    default to None.
    '''

    scrolling = BooleanProperty(False)
    '''If the scroll_to() method is called while scrolling operations are
    happening, a call recursion error can occur. scroll_to() checks to see that
    scrolling is False before calling populate(). scroll_to() dispatches a
    scrolling_complete event, which sets scrolling back to False.

    :data:`scrolling` is a :class:`~kivy.properties.BooleanProperty`,
    default to False.
    '''

    scroll_advance = NumericProperty(10)
    '''For a kind of pre-fetching during scrolling, an "advance" of view
    instances is requested when the scroll position is within some count of
    items, the scroll_advance, difference from either the start or end of the
    scroll window.  View instances are either pulled from the
    adapter.view_cache or created anew. Perhaps, for larger datasets, or for
    speed variances, this needs to be changed from the default arbitrary 10.

    .. versionadded:: 1.8

    :data:`scroll_advance` is a :class:`~kivy.properties.NumericProperty`,
    default to 10.
    '''

    # _index is the position of the window-on-the-data within data.
    _index = NumericProperty(0)

    # _sizes is used to store a cache of view instance heights, for use in
    # calculating a padding that might be needed during scrolling.
    _sizes = DictProperty({})

    # These two are for window-on-the-data-height-sum, which for a measure
    # within istart, iend, which are for the data-height-sum. These are integer
    # values, as are istart and iend.
    _wstart = NumericProperty(0)
    _wend = NumericProperty(None, allownone=True)

    __events__ = ('on_scroll_complete', )

    empty_data = ListProperty([])
    data_binding = ObjectProperty(None, allownone=True)
    selection_binding = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):

        super(ListView, self).__init__(**kwargs)

        self._trigger_populate = Clock.create_trigger(
                self._spopulate, -1)
        self._trigger_reset_spopulate = Clock.create_trigger(
                self._reset_spopulate, -1)

        self.data_op_handler = DataOpHandler(self, True)

        self.bind(size=self._trigger_populate,
                  pos=self._trigger_populate)

        if self.data_binding:
            if self.data_binding.prop == 'data':
                self.data_binding.source.bind(
                    on_data_change=self.data_op_handler.data_changed)

            if self.data_binding.prop == 'selection':
                self.data_binding.source.bind(
                    on_selection_change=self.data_op_handler.data_changed)

        if self.selection_binding:
            if self.selection_binding.prop == 'data':
                self.selection_binding.source.bind(
                    on_data_change=self.update_ui_for_selection_change)

            if self.selection_binding.prop == 'selection':
                self.selection_binding.source.bind(
                    on_selection_change=self.update_ui_for_selection_change)

    def init_kv_bindings(self, bindings):

        binding = bindings[0]

        if isinstance(binding, DataBinding):
            self.data_binding = binding
        elif isinstance(binding, SelectionBinding):
            self.selection_binding = binding

        binding.source.bind(**{binding.prop: binding.setter('value')})
        if binding.prop == 'data':
            binding.source.bind(
                    on_data_change=self.data_op_handler.data_changed)
        if binding.prop == 'selection':
            binding.source.bind(
                    on_selection_change=self.update_ui_for_selection_change)

    def get_count(self):
        return len(self.data_binding.source.data)

    def get_data_item(self, index):
        data = self.data_binding.source.data

        if not data:
            return None

        return data[index]

    def additional_args_converter_args(self, index):
        return ()

    def trim_left_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are less than the
        index of the first selected item if there is a selection.

        versionchanged:: 1.8

            Absorbed from ListAdapter.
        '''
        selection = self.selection_binding.source.selection
        if len(selection) > 0:
            first_sel_index = min([sel.index for sel in selection])
            data = self.data_binding.source.data
            data = data[first_sel_index:]

    def trim_right_of_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are greater than
        the index of the last selected item if there is a selection.

        versionchanged:: 1.8

            Absorbed from ListAdapter.
        '''
        selection = self.selection_binding.source.selection
        if len(selection) > 0:
            last_sel_index = max([sel.index for sel in selection])
            data = self.data_binding.source.data
            data = data[:last_sel_index + 1]

    def trim_to_sel(self, *args):
        '''Cut list items with indices in sorted_keys that are les than or
        greater than the index of the last selected item if there is a
        selection. This preserves intervening list items within the selected
        range.

        versionchanged:: 1.8

            Absorbed from ListAdapter.
        '''
        selection = self.selection_binding.source.selection
        if len(selection) > 0:
            sel_indices = [sel.index for sel in selection]
            first_sel_index = min(sel_indices)
            last_sel_index = max(sel_indices)
            data = self.data_binding.source.data
            data = data[first_sel_index:last_sel_index + 1]

    def cut_to_sel(self, *args):
        '''Same as trim_to_sel, but intervening list items within the selected
        range are also cut, leaving only list items that are selected.

        versionchanged:: 1.8

            Absorbed from ListAdapter.
        '''
        selection = self.selection_binding.source.selection
        if len(selection) > 0:
            self.data_binding.source.data = selection

    def _scroll(self, scroll_y):

        # Scrolling is aided by view item caching done by the adapter, via
        # calls to get_view(index), which either grabs an existing view
        # instance from the cache, or calls its create_view() for a new
        # instance. The populate() method below does the orchestration of calls
        # to the adapter.  Scrolling is done by moving a window-on-the-data,
        # for which view instances that cover this range are added to the
        # container. The variable names are illustrated below, shown for an
        # arbitrary state of scrolling:
        #
        #   0 data item --------------------
        #   1 data item --------------------
        #   2 data item --------------------
        #   3 data item --------------------
        #   4 data item --------------------
        #   5 data item --------------------
        #   6 data item --- view instance -- _wstart  x 6
        #   7 data item --- view instance --          x
        #   8 data item --- view instance --          x
        #   9 data item --- view instance --          x window-on-the-data is
        #  10 data item --- view instance --          x calculated from row
        #  11 data item --- view instance --          x heights and available
        #  12 data item --- view instance --          x space in the listview
        #  13 data item --- view instance --          x container.
        #  14 data item --- view instance --          x
        #  15 data item --- view instance --          x
        #  16 data item --- view instance --          x
        #  17 data item --- view instance --          x
        #  18 data item --- view instance -- _wend    x 18
        #  19 data item --- view instance --                - These three view
        #  20 data item --- view instance --                - instances are in
        #  21 data item --- view instance --                - the view_cache,
        #  22 data item --------------------                  but are not seen
        #  23 data item --------------------                  in the display.
        #  24 data item --------------------
        #
        # With a user action to scroll, a binding from the ScrollView's
        # scroll_y fires to here. The scroll_y value is 1.0 for "completely
        # scrolled up" and 0.0 for "completely scrolled down." There is a
        # relation made between this value and the total height of all items in
        # the ListView, and from that is determined the range of indices in the
        # data that constitute the current "window-on-the-data." The populate()
        # method is called with istart and/or iend set appropriately to get
        # views for this data range from the adapter.view_cache, or to build
        # them anew. _wstart and _wend are updated for the indices of the
        # window-on-the-data. scroll_y, set from user action, is by definition,
        # in sync.
        #
        # When we use scroll_to() to programmatically scroll, we emulate this
        # procedure, and must do a kind of inverse updating to the ScrollView,
        # to tell it the updated scroll_y.
        #
        # View instances are delivered by the adapter as needed. If scrolling
        # is downward, the window-on-the-data is walked along, and if a check
        # determines that the process is about to exhaust the supply of cached
        # views, an amount of view instances are pre-fetched. This amount is
        # determined by a configurable property called scroll_advance.  This
        # weaves a kind of batching into the process for better performance,
        # and insures that view instances are available to cover the "forward
        # edge" of the scrolled view.

        if self.row_height is None:
            return

        # container is a GridLayout.
        container = self.container

        self._scroll_y = scroll_y
        scroll_y = 1 - min(1, max(scroll_y, 0))

        # mstart and mend are the height values for the start and end of the
        # window-on-the-data in terms of total height of view instances
        # covering the entire data range.  scroll_y is the percentage for the
        # start of the window-on-the-data, relative to the total height,
        # expressed in the inverse, such that the value is 1.0 when scrolled to
        # the top and 0.0 when scrolled to the bottom. For 1000 items at 25 row
        # height each, total height would be 25000, and for a case where
        # scrolling has gone to near the "middle" of available items, mstart
        # and mend might be 11940, 12714, where self.height is 775, for the
        # actual size of the container.
        mstart = (container.height - self.height) * scroll_y
        mend = mstart + self.height

        # Convert mstart and mend to the equivalent indices within the data.
        rh = self.row_height
        istart = int(ceil(mstart / rh))
        iend = int(floor(mend / rh))

        # Don't let either istart or iend go negative.
        istart = max(0, istart - 1)
        iend = max(0, iend - 1)

        # Handle scroll up.
        if istart < self._wstart:

            # Populate backward, for view instances needed, to the istart
            # position, and a bit farther back, as configured by
            # scroll_advance.  The max() call keeps the value from going
            # negative.
            istart = max(0, istart - self.scroll_advance)
            self.populate(istart, iend)

            # Update window-on-the-data values.
            self._wstart = istart
            self._wend = iend

        # Handle scroll down.
        elif iend > self._wend:

            # Populate forward, for view instances needed, to the istart
            # position, and a bit farther forward, as configured by
            # self.scroll_advance.
            self.populate(istart, iend + self.scroll_advance)

            # Update window-on-the-data values.
            self._wstart = istart
            self._wend = iend + self.scroll_advance

    def _spopulate(self, *args):
        self.populate()
        # Simulate the scroll again, only if we already scrolled before
        # the position might not be the same, mostly because we don't know the
        # size of the new item.
        if hasattr(self, '_scroll_y'):
            self._scroll(self._scroll_y)

    def _reset_spopulate(self, *args):
        self._wend = None
        self.populate()
        # Simulate the scroll again, only if we already scrolled before
        # the position might not be the same, mostly because we don't know the
        # size of the new item.
        if hasattr(self, '_scroll_y'):
            self._scroll(self._scroll_y)

    def populate(self, istart=None, iend=None):

        container = self.container
        sizes = self._sizes
        rh = self.row_height

        # Ensure we know what we want to show.
        if istart is None:
            istart = self._wstart
            iend = self._wend

        # Clear the view.
        container.clear_widgets()

        # guess only ?
        if iend is not None:

            # Fill with a "padding" of fill height, fh.
            fh = 0
            for x in range(istart):
                fh += sizes[x] if x in sizes else rh
            container.add_widget(Widget(
                size_hint_y=None, height=fh, background_color=(0, 1, 0)))

            # Now fill with real item view instances.
            index = istart
            while index <= iend:
                item_view = self.get_view(index)
                if item_view is None:
                    continue
                index += 1
                sizes[index] = item_view.height
                container.add_widget(item_view)

        else:

            available_height = self.height
            real_height = 0
            index = self._index
            count = 0

            while available_height > 0:
                item_view = self.get_view(index)
                if item_view is None:
                    break
                sizes[index] = item_view.height
                index += 1
                count += 1
                container.add_widget(item_view)
                available_height -= item_view.height
                real_height += item_view.height

            # Extrapolate the full size of the container from the sum
            # of view instance heights.
            #
            # TODO: self._count was removed in 1.8, because it was not used,
            #       but this could be a regression, in that the call to
            #       self.get_count() is made unnecessarily often.
            #
            if count:
                container.height = \
                    (real_height / count) * self.get_count()
                if self.row_height is None:
                    self.row_height = real_height / count

    def scroll_to(self, index, position=None, position_as_percent=None):
        '''Call the scroll_to(i) method with a valid index for the data. If the
        index is out of bounds, nothing happens.

        If scroll_to() is called with scroll_to(99), then the view instance for
        the 100th data item will appear in the middle of the scrollview.

        We may use the term window-on-the-data to, literally, refer to the
        items currently shown in the scrollview, given the combination of
        row_height and layout controls of the scrollview container size.
        Consider an example where there are 1000 data items, for which the
        scrollview shows 30 view instances at a time. Scrolling will march this
        window-on-the-data along within the data.

        The position and position_as_percent args are available as conveniences
        for placing the view instance for the index at a desired position
        within the range of view instances currently shown, as measured down
        from the default top position.

        If integer values can be used effectively, when the math is understood
        for row_height and container size and so on, the position may be
        specified as an integer, position=x. The x value must not exceed the
        count of the number of items presently shown in the scrollview (the
        math about layout must be understood). For example, a call to
        scroll_to(500, position=5) in the case described, would be the
        equivalent of calling scroll_to(510).

        More often, it is presumed, the position_as_percent will be more
        useful, to ask that the given view_instance be positioned by some
        proportion of the space available for items presently shown in the
        scrollview. For example, if there are 1000 data items, and the call is
        scroll_to(500, position_as_percent=.5, and row_height and the height of
        the container are defined so that a count of 30 items are shown in the
        scrollview, this would be equivalent to calling the default
        scroll_to(500), which puts the view_instance in the middle.  Adjust the
        percentage as desired.

        The optional position argument is measured from the top, so for a value
        of 10, with a count of items in the current view of 30, the specified
        item would appear about 10 rows down from the top.

        The optional position_as_percent argument is measured from the top, so
        a value of .20, with a count of items in the current view of 30, the
        specified item would appear about 6 rows down from the top.

        If a position argument is used, pick one or the other. If both are
        passed, the position_as_percent arg will be ignored.

        .. versionadded:: 1.8

        '''

        data = self.data_binding.source.data

        if index < 0 or index > len(data) - 1:
            return

        # If this method is called while scrolling operations are happening, a
        # call recursion error can occur, hence the check to see that scrolling
        # is False before calling populate(). At the end, dispatch a
        # scrolling_complete event, which sets scrolling back to False.
        if not self.scrolling:
            if not self.row_height:
                return

            self.scrolling = True

            len_data = len(data) - 1

            n_window = int(ceil(self.height / self.row_height))

            if index == 0:
                self._index = 0
                self.scrollview.scroll_y = 1.0
                self.scrollview.update_from_scroll()

            elif index == len(data) - 1:

                self._index = max(0, index - n_window)

                # TODO: Hack to keep scrolling to end from locking up. This
                #       scrolls to near the end, but not quite far enough. This
                #       used to work, and the value before the hack was -0.0,
                #       which is an odd duck, no doubt.
                self.scrollview.scroll_y = 0.01
                self.scrollview.update_from_scroll()

            else:

                if position and position <= n_window:

                    # Adjust so that the item at index is at top.
                    index += (int(ceil(float(n_window) * 0.5)))

                    # Apply the add.
                    index = index - position

                if (position_as_percent
                        and not position
                        and 0.0 < position_as_percent <= 1.0):

                    # Adjust so that the item at index is at top.
                    index += (int(ceil(float(n_window) * 0.5)))

                    # Apply the percent.
                    index = index - int(ceil(
                        position_as_percent * float(n_window)))

                # Don't let index go out of bounds.
                index = max(0, index)

                self._index = index

                self.scrollview.scroll_y = \
                        1.0 - (float(index) / float(len_data))
                self.scrollview.update_from_scroll()

            self.dispatch('on_scroll_complete')

    def scroll_by(self, count=1):
        '''The scroll_by(count=10) method is used to scroll by a number of
        items, the count argument, forward or backward.

        Use a negative count to go backward.

        .. versionadded:: 1.8

        '''

        if count == 0:
            return

        data = self.data_binding.source.data

        if count > 0:
            if self._index < len(data) - count - 1:
                self.scroll_to(self._index + count)
        else:
            if self._index >= abs(count):
                self.scroll_to(self._index + count)

    def scroll_to_first(self):
        '''scroll_to_first() scrolls to the first item.

        .. versionadded:: 1.8

        '''

        self.scroll_to(0)

    def scroll_to_last(self):
        '''Call the scroll_to_last() method to scroll to the last item.

        .. versionadded:: 1.8

        '''

        data = self.data_binding.source.data
        self.scroll_to(len(data) - 1)

    def scroll_to_selection(self):
        '''Call the scroll_to_selection() method to scroll to the middle of the
        selection. If there is a big spread between the first and last selected
        item indices, it is possible that no selected item will be in view. See
        also scroll_to_first_selected() and scroll_to_last_selected().

        If there is no selection, nothing happens.

        .. versionadded:: 1.8

        '''

        data = self.data_binding.source.data
        selection = self.data_binding.source.selection
        if selection:
            indices = [data.index(item) for item in selection]
            first_sel_index = min(indices)
            last_sel_index = max(indices)
            spread = last_sel_index - first_sel_index
            if spread == 1:
                middle_index = first_sel_index
            else:
                middle_index = first_sel_index + spread / 2

            self.scroll_to(middle_index)

    def scroll_to_first_selected(self):
        '''Call the scroll_to_first_selected() method to scroll to the
        beginning of the selected range.

        If there is no selection, nothing happens.

        .. versionadded:: 1.8

        '''

        data = self.data_binding.source.data
        selection = self.data_binding.source.selection
        if selection:
            indices = [data.index(item) for item in selection]
            first_sel_index = min(indices)

            self.scroll_to(first_sel_index)

    def scroll_to_last_selected(self):
        '''Call the scroll_to_last_selected() method to scroll to the end of
        the selected range.

        If there is no selection, nothing happens.

        .. versionadded:: 1.8

        '''

        data = self.data_binding.source.data
        selection = self.data_binding.source.selection
        if selection:
            indices = [data.index(item) for item in selection]
            last_sel_index = max(indices)

            self.scroll_to(last_sel_index)

    def on_scroll_complete(self, *args):
        self.scrolling = False

    def update_ui_for_selection_change(self):
        # TODO: Don't repeat, for data vs. selection change. How to force them
        #       to be in proper sequence?
        #data_op_info = self.data_binding.source.data_op_info
        # TODO: Use a selection_op_info to more efficiently update selection.
        #       This is brute-force.
        self.container.clear_widgets()

        self.scrolling = True
        self.populate()
        self.dispatch('on_scroll_complete')

    def update_ui_for_data_changes(self):

        #if len(args) < 2:
            #return

        # This method is tied to list and/or dict ops handlers of the adapter,
        # and to its own similar data_changed() method. The adapter dispatches
        # data changed events from its delegated ops handler, and its
        # data_changed(), which is observed and handled here.
        #
        # Possible list and dict change ops, for which reaction may be needed
        # here, include:
        #
        #       OOL == OpObservableList
        #
        #             set ops:
        #
        #                 OOL_setitem  - single item set
        #                 OOL_setslice - range of items
        #
        #             add ops:
        #
        #                 OOL_iadd   - adds items to end
        #                 OOL_imul   - adds items to end
        #                 OOL_append - adds items to end
        #                 OOL_insert - insert
        #                 OOL_extend - adds items to end
        #
        #             delete ops:
        #
        #                 OOL_delitem  - single item
        #                 OOL_delslice - multiple items
        #                 OOL_remove   - single item
        #                 OOL_pop      - single item
        #
        #             sort ops:
        #
        #                 OOL_sort
        #                 OOL_reverse
        #
        #        OOD == OpObservableDict
        #
        #             set op:
        #
        #                 OOD_setattr     - single item set
        #                     (We do not receive.)
        #                 OOD_setitem_set - single item set
        #                     (We receive the OOD op directly.)
        #
        #             add ops:
        #
        #                 OOD_setitem_add - single item
        #                 OOD_setdefault  - single item
        #                 OOD_update      - single or multiple items
        #
        #                     (We receive OOL ops, from changes to
        #                      sorted_keys fired by these):
        #
        #             delete ops:
        #
        #                 OOD_delitem     - single item
        #                 OOD_pop         - single item
        #                 OOD_popitem     - single item
        #                   [NOTE: OOD_popitem is performed as OOL_delitem]
        #                 OOD_clear       - all items deleted
        #
        #                     (We receive OOL ops, from changes to
        #                      sorted_keys fired by these):
        #
        # Callbacks could come here from either OOL or OOD, and there could be
        # differences in handling. See the conditionals here, and also the
        # conditionals and methods used in the adapter's ops handers to
        # understand the grouping ops, e.g. for grouping insert, and append ops
        # for lists.

        op_info = self.data_op_info

        op = op_info.op_name

        if isinstance(op_info, ListOpInfo):
            start_index = op_info.start_index
            end_index = op_info.end_index
        elif isinstance(op_info, DictOpInfo):
            start_index, end_index = self.additional_op_info

        # Otherwise, we may have item_views as children of self.container
        # that should be removed.

        data = self.data_binding.source.data
        #data = self.data_binding.value
        #data = getattr(self.data_binding.source, self.data_binding.prop)

        if op in ['OOL_setitem', 'OOD_setitem_set', ]:

            widget_index = -1

            for i, item_view in enumerate(self.container.children):
                if item_view.index == start_index:
                    widget_index = i
                    break

            if widget_index >= 0:
                widget = self.container.children[widget_index]
                self.container.remove_widget(widget)

                item_view = self.get_view(start_index)
                if item_view:
                    self.container.add_widget(item_view, widget_index)

        elif op in ['OOL_setslice', ]:

            len_data = len(data)

            slice_indices = range(start_index, end_index + 1)

            widget_indices = []

            for i, item_view in enumerate(self.container.children):
                if item_view.index in slice_indices:
                    widget_indices.append(i)
                    if len(widget_indices) == len(slice_indices):
                        break

            if widget_indices:
                for widget_index in reversed(sorted(widget_indices)):
                    widget = self.container.children[widget_index]
                    self.container.remove_widget(widget)

                add_index = min(widget_indices)

                for slice_index in slice_indices:
                    item_view = self.get_view(slice_index)
                    if item_view:
                        self.container.add_widget(item_view, add_index)
            else:

                self._index = min(slice_indices)
                self.scrolling = True
                self.populate()
                self.dispatch('on_scroll_complete')

        elif op in ['OOL_append',
                    'OOL_extend',
                    'OOD_setattr',
                    'OOD_setitem_add',
                    'OOD_setdefault',
                    'OOD_update']:

            len_data = len(data)
            n_window = int(ceil(self.height / self.row_height))
            self._index = max(0, len_data - n_window)

            self.scrolling = True
            self.populate()
            self.dispatch('on_scroll_complete')

        elif op in ['OOL_delitem',
                    'OOL_delslice',
                    'OOL_remove',
                    'OOL_pop',
                    'OOD_delitem',
                    'OOD_clear',
                    'OOD_pop', ]:

            # NOTE: There is no OOD_popitem here, because it is performed as
            #       a OOD_delitem.

#            deleted_indices = range(start_index, end_index + 1)
#
#            print 'deleted_indices', deleted_indices
#
#            for item_view in self.container.children:
#                if (hasattr(item_view, 'index')
#                        and item_view.index in deleted_indices):
#                    print 'removing', item_view
#                    self.container.remove_widget(item_view)
#
            self.scrolling = True
            self.populate()
            self.dispatch('on_scroll_complete')

        elif op == 'OOL_insert':

            self.scrolling = True
            self.populate()
            self.dispatch('on_scroll_complete')

        elif op in ['OOL_sort', 'OOL_reverse', 'OOL_set', ]:

            self.container.clear_widgets()

            self.scrolling = True
            self.populate()
            self.dispatch('on_scroll_complete')

    def get_selection(self):
        '''A convenience method to call to the adapter for the all of the
        selected items.

        .. versionadded:: 1.8

        '''
        return self.get_selection() if self else None

    def get_first_selected(self):
        '''A convenience method to call to the adapter for the first selected
        item.

        .. versionadded:: 1.8

        '''
        return self.get_first_selected() if self else None

    def get_last_selected(self):
        '''A convenience method to call to the adapter for the last selected
        item.

        .. versionadded:: 1.8

        '''
        return self.get_last_selected() if self else None
