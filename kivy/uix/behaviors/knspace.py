'''
Kivy Namespaces
===============

.. versionadded:: 1.9.1

.. warning::
    This code is still experimental, and its API is subject to change in a
    future version.

The :class:`KNSpaceBehavior` `mixin <https://en.wikipedia.org/wiki/Mixin>`_
class provides namespace functionality for Kivy objects. It allows kivy objects
to be named and then accessed using namespaces.

:class:`KNSpace` instances are the namespaces that store the named objects
in Kivy :class:`~kivy.properties.ObjectProperty` instances.
In addition, when inheriting from :class:`KNSpaceBehavior`, if the derived
object is named, the name will automatically be added to the associated
namespace and will point to a :attr:`~kivy.uix.widget.proxy_ref` of the
derived object.

Basic examples
--------------

By default, there's only a single namespace: the :attr:`knspace` namespace. The
simplest example is adding a widget to the namespace:

.. code-block:: python

    from kivy.uix.behaviors.knspace import knspace
    widget = Widget()
    knspace.my_widget = widget

This adds a kivy :class:`~kivy.properties.ObjectProperty` with `rebind=True`
and `allownone=True` to the :attr:`knspace` namespace with a property name
`my_widget`. And the property now also points to this widget.

This can be done automatically with:

.. code-block:: python

    class MyWidget(KNSpaceBehavior, Widget):
        pass

    widget = MyWidget(knsname='my_widget')

Or in kv:

.. code-block:: kv

    <MyWidget@KNSpaceBehavior+Widget>

    MyWidget:
        knsname: 'my_widget'

Now, `knspace.my_widget` will point to that widget.

When one creates a second widget with the same name, the namespace will
also change to point to the new widget. E.g.:

.. code-block:: python

    widget = MyWidget(knsname='my_widget')
    # knspace.my_widget now points to widget
    widget2 = MyWidget(knsname='my_widget')
    # knspace.my_widget now points to widget2

Setting the namespace
---------------------

One can also create ones own namespace rather than using the default
:attr:`knspace` by directly setting :attr:`KNSpaceBehavior.knspace`:

.. code-block:: python

    class MyWidget(KNSpaceBehavior, Widget):
        pass

    widget = MyWidget(knsname='my_widget')
    my_new_namespace = KNSpace()
    widget.knspace = my_new_namespace

Initially, `my_widget` is added to the default namespace, but when the widget's
namespace is changed to `my_new_namespace`, the reference to `my_widget` is
moved to that namespace. We could have also of course first set the namespace
to `my_new_namespace` and then have named the widget `my_widget`, thereby
avoiding the initial assignment to the default namespace.

Similarly, in kv:

.. code-block:: kv

    <MyWidget@KNSpaceBehavior+Widget>

    MyWidget:
        knspace: KNSpace()
        knsname: 'my_widget'

Inheriting the namespace
------------------------

In the previous example, we directly set the namespace we wished to use.
In the following example, we inherit it from the parent, so we only have to set
it once:

.. code-block:: kv

    <MyWidget@KNSpaceBehavior+Widget>
    <MyLabel@KNSpaceBehavior+Label>

    <MyComplexWidget@MyWidget>:
        knsname: 'my_complex'
        MyLabel:
            knsname: 'label1'
        MyLabel:
            knsname: 'label2'

Then, we do:

.. code-block:: python

    widget = MyComplexWidget()
    new_knspace = KNSpace()
    widget.knspace = new_knspace

The rule is that if no knspace has been assigned to a widget, it looks for a
namespace in its parent and parent's parent and so on until it find one to
use. If none are found, it uses the default :attr:`knspace`.

When `MyComplexWidget` is created, it still used the default namespace.
However, when we assigned the root widget its new namespace, all its
children switched to using that new namespace as well. So `new_knspace` now
contains `label1` and `label2` as well as `my_complex`.

If we had first done:

.. code-block:: python

    widget = MyComplexWidget()
    new_knspace = KNSpace()
    knspace.label1.knspace = knspace
    widget.knspace = new_knspace

Then `label1` would remain stored in the default :attr:`knspace` since it was
directly set, but `label2` and `my_complex` would still be added to the new
namespace.

One can customize the attribute used to search the parent tree by changing
:attr:`KNSpaceBehavior.knspace_key`. If the desired knspace is not reachable
through a widgets parent tree, e.g. in a popup that is not a widget's child,
:attr:`KNSpaceBehavior.knspace_key` can be used to establish a different
search order.

Accessing the namespace
-----------------------

As seen in the previous example, if not directly assigned, the namespace is
found by searching the parent tree. Consequently, if a namespace was assigned
further up the parent tree, all its children and below could access that
namespace through their :attr:`KNSpaceBehavior.knspace` property.

This allows the creation of multiple widgets with identically given names
if each root widget instance is assigned a new namespace. For example:

.. code-block:: kv

    <MyComplexWidget@KNSpaceBehavior+Widget>:
        Label:
            text: root.knspace.pretty.text if root.knspace.pretty else ''

    <MyPrettyWidget@KNSpaceBehavior+TextInput>:
        knsname: 'pretty'
        text: 'Hello'

    <MyCompositeWidget@KNSpaceBehavior+BoxLayout>:
        MyComplexWidget
        MyPrettyWidget

Now, when we do:

.. code-block:: python

    knspace1, knspace2 = KNSpace(), KNSpace()
    composite1 = MyCompositeWidget()
    composite1.knspace = knspace1

    composite2 = MyCompositeWidget()
    composite2.knspace = knspace2

    knspace1.pretty = "Here's the ladder, now fix the roof!"
    knspace2.pretty = "Get that raccoon off me!"

Because each of the `MyCompositeWidget` instances have a different namespace
their children also use different namespaces. Consequently, the
pretty and complex widgets of each instance will have different text.

Further, because both the namespace :class:`~kivy.properties.ObjectProperty`
references, and :attr:`KNSpaceBehavior.knspace` have `rebind=True`, the
text of the `MyComplexWidget` label is rebound to match the text of
`MyPrettyWidget` when either the root's namespace changes or when the
`root.knspace.pretty` property changes, as expected.

Forking a namespace
-------------------

Forking a namespace provides the opportunity to create a new namespace
from a parent namespace so that the forked namespace will contain everything
in the origin namespace, but the origin namespace will not have access to
anything added to the forked namespace.

For example:

.. code-block:: python

    child = knspace.fork()
    grandchild = child.fork()

    child.label = Label()
    grandchild.button = Button()

Now label is accessible by both child and grandchild, but not by knspace. And
button is only accessible by the grandchild but not by the child or by knspace.
Finally, doing `grandchild.label = Label()` will leave `grandchild.label`
and `child.label` pointing to different labels.

A motivating example is the example from above:

.. code-block:: kv

    <MyComplexWidget@KNSpaceBehavior+Widget>:
        Label:
            text: root.knspace.pretty.text if root.knspace.pretty else ''

    <MyPrettyWidget@KNSpaceBehavior+TextInput>:
        knsname: 'pretty'
        text: 'Hello'

    <MyCompositeWidget@KNSpaceBehavior+BoxLayout>:
        knspace: 'fork'
        MyComplexWidget
        MyPrettyWidget

Notice the addition of `knspace: 'fork'`. This is identical to doing
`knspace: self.knspace.fork()`. However, doing that would lead to infinite
recursion as that kv rule would be executed recursively because `self.knspace`
will keep on changing. However, allowing `knspace: 'fork'` cirumvents that.
See :attr:`KNSpaceBehavior.knspace`.

Now, having forked, we just need to do:

.. code-block:: python

    composite1 = MyCompositeWidget()
    composite2 = MyCompositeWidget()

    composite1.knspace.pretty = "Here's the ladder, now fix the roof!"
    composite2.knspace.pretty = "Get that raccoon off me!"

Since by forking we automatically created a unique namespace for each
`MyCompositeWidget` instance.
'''

__all__ = ('KNSpace', 'KNSpaceBehavior', 'knspace')

from kivy.event import EventDispatcher
from kivy.properties import StringProperty, ObjectProperty, AliasProperty

knspace = None
'''The default :class:`KNSpace` namespace. See :attr:`KNSpaceBehavior.knspace`
for more details.
'''


class KNSpace(EventDispatcher):
    '''Each :class:`KNSpace` instance is a namespace that stores the named Kivy
    objects associated with this namespace. Each named object is
    stored as the value of a Kivy :class:`~kivy.properties.ObjectProperty` of
    this instance whose property name is the object's given name. Both `rebind`
    and `allownone` are set to `True` for the property.

    See :attr:`KNSpaceBehavior.knspace` for details on how a namespace is
    associated with a named object.

    When storing an object in the namespace, the object's `proxy_ref` is
    stored if the object has such an attribute.

    :Parameters:

        `parent`: (internal) A :class:`KNSpace` instance or None.
            If specified, it's a parent namespace, in which case, the current
            namespace will have in its namespace all its named objects
            as well as the named objects of its parent and parent's parent
            etc. See :meth:`fork` for more details.
    '''

    parent = None
    '''(internal) The parent namespace instance, :class:`KNSpace`, or None. See
    :meth:`fork`.
    '''
    __has_applied = None

    keep_ref = False
    '''Whether a direct reference should be kept to the stored objects.
    If ``True``, we use the direct object, otherwise we use
    :attr:`~kivy.uix.widget.proxy_ref` when present.

    Defaults to False.
    '''

    def __init__(self, parent=None, keep_ref=False, **kwargs):
        self.keep_ref = keep_ref
        super(KNSpace, self).__init__(**kwargs)
        self.parent = parent
        self.__has_applied = set(self.properties().keys())

    def __setattr__(self, name, value):
        prop = super(KNSpace, self).property(name, quiet=True)
        has_applied = self.__has_applied
        if prop is None:
            if hasattr(self, name):
                super(KNSpace, self).__setattr__(name, value)
            else:
                self.apply_property(
                    **{name:
                       ObjectProperty(None, rebind=True, allownone=True)}
                )
                if not self.keep_ref:
                    value = getattr(value, 'proxy_ref', value)
                has_applied.add(name)
                super(KNSpace, self).__setattr__(name, value)
        elif name not in has_applied:
            self.apply_property(**{name: prop})
            has_applied.add(name)
            if not self.keep_ref:
                value = getattr(value, 'proxy_ref', value)
            super(KNSpace, self).__setattr__(name, value)
        else:
            if not self.keep_ref:
                value = getattr(value, 'proxy_ref', value)
            super(KNSpace, self).__setattr__(name, value)

    def __getattribute__(self, name):
        if name in super(KNSpace, self).__getattribute__('__dict__'):
            return super(KNSpace, self).__getattribute__(name)

        try:
            value = super(KNSpace, self).__getattribute__(name)
        except AttributeError:
            parent = super(KNSpace, self).__getattribute__('parent')
            if parent is None:
                raise AttributeError(name)
            return getattr(parent, name)

        if value is not None:
            return value

        parent = super(KNSpace, self).__getattribute__('parent')
        if parent is None:
            return None

        try:
            return getattr(parent, name)  # if parent doesn't have it
        except AttributeError:
            return None

    def property(self, name, quiet=False):
        # needs to overwrite EventDispatcher.property so kv lang will work
        prop = super(KNSpace, self).property(name, quiet=True)
        if prop is not None:
            return prop

        prop = ObjectProperty(None, rebind=True, allownone=True)
        self.apply_property(**{name: prop})
        self.__has_applied.add(name)
        return prop

    def fork(self):
        '''Returns a new :class:`KNSpace` instance which will have access to
        all the named objects in the current namespace but will also have a
        namespace of its own that is unique to it.

        For example:

        .. code-block:: python

            forked_knspace1 = knspace.fork()
            forked_knspace2 = knspace.fork()

        Now, any names added to `knspace` will be accessible by the
        `forked_knspace1` and `forked_knspace2` namespaces by the normal means.
        However, any names added to `forked_knspace1` will not be accessible
        from `knspace` or `forked_knspace2`. Similar for `forked_knspace2`.
        '''
        return KNSpace(parent=self)


class KNSpaceBehavior(object):
    '''Inheriting from this class allows naming of the inherited objects, which
    are then added to the associated namespace :attr:`knspace` and accessible
    through it.

    Please see the :mod:`knspace behaviors module <kivy.uix.behaviors.knspace>`
    documentation for more information.
    '''

    _knspace = ObjectProperty(None, allownone=True)
    _knsname = StringProperty('')
    __last_knspace = None
    __callbacks = None

    def __init__(self, knspace=None, **kwargs):
        self.knspace = knspace
        super(KNSpaceBehavior, self).__init__(**kwargs)

    def __knspace_clear_callbacks(self, *largs):
        for obj, name, uid in self.__callbacks:
            obj.unbind_uid(name, uid)
        last = self.__last_knspace
        self.__last_knspace = self.__callbacks = None

        assert self._knspace is None
        assert last

        new = self.__set_parent_knspace()
        if new is last:
            return
        self.property('_knspace').dispatch(self)

        name = self.knsname
        if not name:
            return

        if getattr(last, name) == self:
            setattr(last, name, None)

        if new:
            setattr(new, name, self)
        else:
            raise ValueError('Object has name "{}", but no namespace'.
                             format(name))

    def __set_parent_knspace(self):
        callbacks = self.__callbacks = []
        fbind = self.fbind
        append = callbacks.append
        parent_key = self.knspace_key
        clear = self.__knspace_clear_callbacks

        append((self, 'knspace_key', fbind('knspace_key', clear)))
        if not parent_key:
            self.__last_knspace = knspace
            return knspace

        append((self, parent_key, fbind(parent_key, clear)))
        parent = getattr(self, parent_key, None)
        while parent is not None:
            fbind = parent.fbind

            parent_knspace = getattr(parent, 'knspace', 0)
            if parent_knspace is not 0:
                append((parent, 'knspace', fbind('knspace', clear)))
                self.__last_knspace = parent_knspace
                return parent_knspace

            append((parent, parent_key, fbind(parent_key, clear)))
            new_parent = getattr(parent, parent_key, None)
            if new_parent is parent:
                break
            parent = new_parent
        self.__last_knspace = knspace
        return knspace

    def _get_knspace(self):
        _knspace = self._knspace
        if _knspace is not None:
            return _knspace

        if self.__callbacks is not None:
            return self.__last_knspace

        # we only get here if we never accessed our knspace
        return self.__set_parent_knspace()

    def _set_knspace(self, value):
        if value is self._knspace:
            return

        knspace = self._knspace or self.__last_knspace
        name = self.knsname
        if name and knspace and getattr(knspace, name) == self:
            setattr(knspace, name, None)  # reset old namespace

        if value == 'fork':
            if not knspace:
                knspace = self.knspace  # get parents in case we haven't before
            if knspace:
                value = knspace.fork()
            else:
                raise ValueError('Cannot fork with no namespace')

        for obj, prop_name, uid in self.__callbacks or []:
            obj.unbind_uid(prop_name, uid)
        self.__last_knspace = self.__callbacks = None

        if name:
            if value is None:  # if None, first update the recursive knspace
                knspace = self.__set_parent_knspace()
                if knspace:
                    setattr(knspace, name, self)
                self._knspace = None  # cause a kv trigger
            else:
                setattr(value, name, self)
                knspace = self._knspace = value

            if not knspace:
                raise ValueError('Object has name "{}", but no namespace'.
                                 format(name))
        else:
            if value is None:
                self.__set_parent_knspace()  # update before trigger below
            self._knspace = value

    knspace = AliasProperty(
        _get_knspace, _set_knspace, bind=('_knspace', ), cache=False,
        rebind=True, allownone=True)
    '''The namespace instance, :class:`KNSpace`, associated with this widget.
    The :attr:`knspace` namespace stores this widget when naming this widget
    with :attr:`knsname`.

    If the namespace has been set with a :class:`KNSpace` instance, e.g. with
    `self.knspace = KNSpace()`, then that instance is returned (setting with
    `None` doesn't count). Otherwise, if :attr:`knspace_key` is not None, we
    look for a namespace to use in the object that is stored in the property
    named :attr:`knspace_key`, of this instance. I.e.
    `object = getattr(self, self.knspace_key)`.

    If that object has a knspace property, then we return its value. Otherwise,
    we go further up, e.g. with `getattr(object, self.knspace_key)` and look
    for its `knspace` property.

    Finally, if we reach a value of `None`, or :attr:`knspace_key` was `None`,
    the default :attr:`~kivy.uix.behaviors.knspace.knspace` namespace is
    returned.

    If :attr:`knspace` is set to the string `'fork'`, the current namespace
    in :attr:`knspace` will be forked with :meth:`KNSpace.fork` and the
    resulting namespace will be assigned to this instance's :attr:`knspace`.
    See the module examples for a motivating example.

    Both `rebind` and `allownone` are `True`.
    '''

    knspace_key = StringProperty('parent', allownone=True)
    '''The name of the property of this instance, to use to search upwards for
    a namespace to use by this instance. Defaults to `'parent'` so that we'll
    search the parent tree. See :attr:`knspace`.

    When `None`, we won't search the parent tree for the namespace.
    `allownone` is `True`.
    '''

    def _get_knsname(self):
        return self._knsname

    def _set_knsname(self, value):
        old_name = self._knsname
        knspace = self.knspace
        if old_name and knspace and getattr(knspace, old_name) == self:
            setattr(knspace, old_name, None)

        self._knsname = value
        if value:
            if knspace:
                setattr(knspace, value, self)
            else:
                raise ValueError('Object has name "{}", but no namespace'.
                                 format(value))

    knsname = AliasProperty(
        _get_knsname, _set_knsname, bind=('_knsname', ), cache=False)
    '''The name given to this instance. If named, the name will be added to the
    associated :attr:`knspace` namespace, which will then point to the
    `proxy_ref` of this instance.

    When named, one can access this object by e.g. self.knspace.name, where
    `name` is the given name of this instance. See :attr:`knspace` and the
    module description for more details.
    '''


knspace = KNSpace()
