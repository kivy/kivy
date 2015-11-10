'''Provides namespace functionality for Kivy objects. It allows kivy objects
to be named and then accessed using the namespace.

:class:`KNSpace` instances are the namespaces that store the named objects.
Classes need to inherit from :class:`KNSpaceBehavior` so that the class, when
named, will be stored in the namespace. :attr:`knspace` is the default
namespace where objects are stored, unless the object is associated with a
different namespace.

Simple Example
-----------------

Here, because no namespace is specified, the default
:attr:`knspace` is used so we can access its widgets directly, as in
`knspace.keyboard`, to get the keyboard widget::

    #:import knspace cutils.knspace.knspace
    #:import Factory kivy.lang.Factory
    <NamedTextInput@KNSpaceBehavior+TextInput>

    <Keyboard@Popup>:
        BoxLayout:
            GridLayout:
                cols: 1
                NamedTextInput:
                    name: 'keyboard'
                    hint_text: 'Type something'
                Label:
                    text: 'My Keyboard'
            Button:
                text: 'Close Keyboard'
                on_press: root.dismiss()

    <RootWidget@BoxLayout>:
        Button:
            on_parent: self.popup = Factory.Keyboard()
            on_release: self.popup.open()
            text: 'Open keyboard'
        Label:
            text: 'Keyboard output:\\n' + knspace.keyboard.text if \
knspace.keyboard else ''

To test, run a app with `RootWidget`.

Multiple Namespaces
-------------------

In the previous example, only the default namespace was used. However,
sometimes we need to split namespaces so we can reuse the name across
multiple widgets using the same name.

When a :class:`KNSpaceBehavior` derived widget is given a name, first we find
the associated namespace using the :attr:`KNSpaceBehavior.knspace` property.
Then, we create a :class:`~kivy.properties.ObjectProperty` in that namespace,
whose name is that name and assign the named widget as its value. See
:attr:`KNSpaceBehavior.knspace` for details on how that namespace is found.

In short, we check if the widget was assigned one, if not, we find the
namespace by walking up its parent tree using
:attr:`KNSpaceBehavior.knspace_key` and finding the first one with a namespace.
Finally, if not found, we use :attr:`knspace`. Therefore, above, the default
namespace was used since none was specified.

::

    #:import Factory kivy.lang.Factory
    <NamedTextInput@KNSpaceBehavior+TextInput>

    <Keyboard@KNSpaceBehavior+Popup>:
        knspace_key: 'knspace_parent'
        knspace_parent: None
        BoxLayout:
            GridLayout:
                cols: 1
                NamedTextInput:
                    name: 'keyboard'
                    hint_text: 'Type something'
                Label:
                    text: 'My Keyboard'
            Button:
                text: 'Close Keyboard'
                on_press: root.dismiss()

    <Typist@KNSpaceBehavior+BoxLayout>:
        knspace: getattr(self, 'knspace').fork()  \
# So we don't create a rule binding
        Button:
            on_parent:
                self.popup = Factory.Keyboard()
                self.popup.knspace_parent = root
            on_release: self.popup.open()
            text: 'Open keyboard'
        Label:
            text: 'Keyboard output:\\n' + root.knspace.keyboard.text if \
root.knspace.keyboard else ''

    <RootWidget@BoxLayout>:
        Typist
        Typist

In this example, we wanted two typists, rather than a single keyboard.
But within a typist we wanted to be able to use names, even though typist
share identical names. To do this, we have
`knspace: getattr(self, 'knspace').fork()`. This forks the current namespace
(which happens to be the default, :attr:`knspace`) and create a namespace
shared by widgets that are offspring of that `Typist`.

Now, each `Typist` gets its own namespace, while still sharing the
default namespaces from which it was forked for widgets not in its namespace.

`knspace_key: 'knspace_parent'` is required, since a `Popup` is not a child
the `Typist`, but they do have to share the namspace, so instead of using
`parent` to find the next namespace up the tree, we use the specified
`knspace_parent` attribute which points to the Typist and hence its
namespace.

Traditional namespace
---------------------

In the above example, we accessed the namespace using e.g.
`root.knspace.keyboard`. We can also access it without having access to e.g.
`root` like in a traditional namespace access.

We can change the above `RootWidget` into::

    <RootWidget@KNSpaceBehavior+BoxLayout>:
        name: 'root'
        Typist
        Typist

Now, we can do::

    knspace.root.children[0].knspace.keyboard.hint_text = 'Type something else'

And the second Typist's keyboard will have a different hint text. Of course
we could also have done
`root.children[0].knspace.keyboard.hint_text = 'Type something else'` if had
access to the root widget.
'''

__all__ = ('KNSpace', 'KNSpaceBehavior', 'knspace')

from kivy.event import EventDispatcher
from kivy.properties import StringProperty, ObjectProperty, AliasProperty

knspace = None
'''The default :class:`KNSpace` namespace. If a :class:`KNSpace` namespace has
not been assigned to a :class:`KNSpaceBehavior` instance, then this
:class:`KNSpace` namespace serves as the default namespace.

See the examples and :class:`KNSpaceBehavior` for more details.
'''


class KNSpace(EventDispatcher):
    '''Each :class:`KNSpace` instance is a namespace that stores the named Kivy
    objects when they are associated with this namespace. Each named object is
    stored as the value of a Kivy :class:`~kivy.properties.ObjectProperty` of
    this instance whose property name is the object's given name. Both `rebind`
    and `allownone` are set to `True` for the property.

    See :attr:`KNSpaceBehavior` for details on how a namespace is associated
    with a named object.

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

    def __init__(self, parent=None, **kwargs):
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
                value = getattr(value, 'proxy_ref', value)
                has_applied.add(name)
                super(KNSpace, self).__setattr__(name, value)
        elif name not in has_applied:
            self.apply_property(**{name: prop})
            has_applied.add(name)
            value = getattr(value, 'proxy_ref', value)
            super(KNSpace, self).__setattr__(name, value)
        else:
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
        return getattr(parent, name)

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
        '''Creates a new :class:`KNSpace` instance which will have access to
        all the named objects in the current namespace but will also have a
        namespace of its own that is unique to it.

        Any new names added to a :class:`KNSpaceBehavior` associated with
        this instance will be accesible only through this instance
        and not its parent(s). However, when looking for a named object using
        this namespace, if the object is not found in this namespace we search
        it's parent namespace and so on until we (don't) find it.
        '''
        return KNSpace(parent=self)


class KNSpaceBehavior(object):
    '''Inheriting from this class allows naming of the inherited object, which
    is then added to the associated namespace :attr:`knspace` and accessible
    through it.
    '''

    _knspace = ObjectProperty(None, allownone=True)
    _name = StringProperty('')
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

        name = self.name
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
        name = self.name
        if name and knspace and getattr(knspace, name) == self:
            setattr(knspace, name, None)  # reset old namespace

        if value == 'fork':
            if not knspace:
                knspace = self.knspace  # get parents in case we haven't before
            if knspace:
                value = knspace.fork()
            else:
                raise ValueError('Cannot fork with no namesapce')

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
    When this widget is named with :attr:`name` the name is added to the
    :attr:`knspace` namespace pointing to this widget.

    If the namespace has been set with a :class:`KNSpace` instance, e.g. with
    `self.knspace = ...`, then that instance is used. Otherwise, we look at
    the property named :attr:`knspace_key` of this obj. If that object has a
    knspace property we use that namespace. Otherwise, we look at its
    :attr:`knspace_key` object and walk up the parent tree until we find
    a parent who has a namespace instance. Finally, if there's no parent with
    a namespace, the default :attr:`~cutils.knspace.knspace` namespace is used.

    Both `rebind` and `allownone` are `True`.
    '''

    knspace_key = StringProperty('parent', allownone=True)
    '''The name of the property of this instance, to use to find the namespace
    associated with this instance. Defaults to `'parent'` so that we'll look
    up the parent tree to find the namespace. See :attr:`knspace`.

    When `None`, we won't search the parent tree for the namespace.
    `allownone` is `True`.
    '''

    def _get_name(self):
        return self._name

    def _set_name(self, value):
        old_name = self._name
        knspace = self.knspace
        if old_name and knspace and getattr(knspace, old_name) == self:
            setattr(knspace, old_name, None)

        self._name = value
        if value:
            if knspace:
                setattr(knspace, value, self)
            else:
                raise ValueError('Object has name "{}", but no namespace'.
                                 format(value))

    name = AliasProperty(_get_name, _set_name, bind=('_name', ), cache=False)
    '''The name given to this object. If named, the name will be added to the
    associated :attr:`knspace` and will point to the `proxy_ref` of this
    object.

    When named, one can access this object by e.g. knspace.name, where `name`
    is the given name of this instance. See :attr:`knspace` and the module
    description for more details.
    '''

knspace = KNSpace()
