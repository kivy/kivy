'''
Builder
======

Class used for the registering and application of rules for specific widgets.
'''
import sys
from os import environ
from os.path import join
from copy import copy
from types import CodeType
from functools import partial

from kivy.factory import Factory
from kivy.lang.parser import (
    Parser,
    ParserException,
    _handlers,
    global_idmap,
    ParserRuleProperty,
    ParserControlRule,
)
from kivy.logger import Logger
from kivy import kivy_data_dir
from kivy.context import register_context
from kivy.resources import resource_find
from kivy.utils import path_to_str
from kivy._event import Observable, EventDispatcher
from kivy.properties import ObjectProperty

__all__ = ('Observable', 'Builder', 'BuilderBase', 'BuilderException')


trace = Logger.trace

# late import
Instruction = None

# delayed calls are canvas expression triggered during an loop. It is one
# directional linked list of args to call call_fn with. Each element is a list
# whose last element points to the next list of args to execute when
# Builder.sync is called.
_delayed_start = None


class BuilderException(ParserException):
    '''Exception raised when the Builder fails to apply a rule on a widget.
    '''
    pass


def custom_callback(__kvlang__, idmap, *largs, **kwargs):
    idmap['args'] = largs
    exec(__kvlang__.co_value, idmap)


def call_fn(args, instance, v):
    element, key, value, rule, idmap = args
    if __debug__:
        trace('Lang: call_fn %s, key=%s, value=%r, %r' % (
            element, key, value, rule.value))
    rule.count += 1
    try:
        e_value = eval(value, idmap)
    except (BuilderException, ReferenceError):
        # a ReferenceError means a weak-referenced widget died before this
        # (delayed) update ran; Builder.sync() relies on catching it as-is
        raise
    except Exception as e:
        tb = sys.exc_info()[2]
        raise BuilderException(
            rule.ctx, rule.line,
            '{}: {}'.format(e.__class__.__name__, e), cause=tb)
    if __debug__:
        trace('Lang: call_fn => value=%r' % (e_value, ))
    setattr(element, key, e_value)


def delayed_call_fn(args, instance, v):
    # it's already on the list
    if args[-1] is not None:
        return

    global _delayed_start
    if _delayed_start is None:
        _delayed_start = args
        args[-1] = StopIteration
    else:
        args[-1] = _delayed_start
        _delayed_start = args


def update_intermediates(base, keys, bound, s, fn, args, instance, value):
    ''' Function that is called when an intermediate property is updated
    and `rebind` of that property is True. In that case, we unbind
    all bound funcs that were bound to attrs of the old value of the
    property and rebind them to the new value of the property.

    For example, if the rule is `self.a.b.c.d`, then when b is changed, we
    unbind from `b`, `c` and `d`, if they were bound before (they were not
    None and `rebind` of the respective properties was True) and we rebind
    to the new values of the attrs `b`, `c``, `d` that are not None and
    `rebind` is True.

    :Parameters:
        `base`
            A (proxied) ref to the base widget, `self` in the example
            above.
        `keys`
            A list of the name off the attrs of `base` being watched. In
            the example above it'd be `['a', 'b', 'c', 'd']`.
        `bound`
            A list 4-tuples, each tuple being (widget, attr, callback, uid)
            representing callback functions bound to the attributed `attr`
            of `widget`. `uid` is returned by `fbind` when binding.
            The callback may be None, in which case the attr
            was not bound, but is there to be able to walk the attr tree.
            E.g. in the example above, if `b` was not an eventdispatcher,
            `(_b_ref_, `c`, None)` would be added to the list so we can get
            to `c` and `d`, which may be eventdispatchers and their attrs.
        `s`
            The index in `keys` of the of the attr that needs to be
            updated. That is all the keys from `s` and further will be
            rebound, since the `s` key was changed. In bound, the
            corresponding index is `s - 1`. If `s` is None, we start from
            1 (first attr).
        `fn`
            The function to be called args, `args` on bound callback.
    '''
    # first remove all the old bound functions from `s` and down.
    for f, k, fun, uid in bound[s:]:
        if fun is None:
            continue
        try:
            f.unbind_uid(k, uid)
        except ReferenceError:
            pass
    del bound[s:]

    # find the first attr from which we need to start rebinding.
    f = getattr(*bound[-1][:2])
    if f is None:
        fn(args, None, None)
        return
    s += 1
    append = bound.append

    # bind all attrs, except last to update_intermediates
    for val in keys[s:-1]:
        # if we need to dynamically rebind, bindm otherwise just
        # add the attr to the list
        if isinstance(f, (EventDispatcher, Observable)):
            prop = f.property(val, True)
            if prop is not None and getattr(prop, 'rebind', False):
                # fbind should not dispatch, otherwise
                # update_intermediates might be called in the middle
                # here messing things up
                uid = f.fbind(
                    val, update_intermediates, base, keys, bound, s, fn, args)
                append([f.proxy_ref, val, update_intermediates, uid])
            else:
                append([f.proxy_ref, val, None, None])
        else:
            append([getattr(f, 'proxy_ref', f), val, None, None])

        f = getattr(f, val, None)
        if f is None:
            break
        s += 1

    # for the last attr we bind directly to the setting function,
    # because that attr sets the value of the rule.
    if isinstance(f, (EventDispatcher, Observable)):
        uid = f.fbind(keys[-1], fn, args)
        if uid:
            append([f.proxy_ref, keys[-1], fn, uid])
    # when we rebind we have to update the
    # rule with the most recent value, otherwise, the value might be wrong
    # and wouldn't be updated since we might not have tracked it before.
    # This only happens for a callback when rebind was True for the prop.
    fn(args, None, None)


def create_handler(iself, element, key, value, rule, idmap, delayed=False,
                   self_ref=None):
    idmap = copy(idmap)
    idmap.update(global_idmap)
    idmap['self'] = self_ref if self_ref is not None else iself.proxy_ref
    bound_list = _handlers[iself.uid][key]
    handler_append = bound_list.append

    # we need a hash for when delayed, so we don't execute duplicate canvas
    # callbacks from the same handler during a sync op
    if delayed:
        fn = delayed_call_fn
        args = [element, key, value, rule, idmap, None]  # see _delayed_start
    else:
        fn = call_fn
        args = (element, key, value, rule, idmap)

    # bind every key.value
    if rule.watched_keys is not None:
        for keys in rule.watched_keys:
            base = idmap.get(keys[0])
            if base is None:
                continue
            f = base = getattr(base, 'proxy_ref', base)
            bound = []
            was_bound = False
            append = bound.append

            # bind all attrs, except last to update_intermediates
            k = 1
            for val in keys[1:-1]:
                # if we need to dynamically rebind, bindm otherwise
                # just add the attr to the list
                if isinstance(f, (EventDispatcher, Observable)):
                    prop = f.property(val, True)
                    if prop is not None and getattr(prop, 'rebind', False):
                        # fbind should not dispatch, otherwise
                        # update_intermediates might be called in the middle
                        # here messing things up
                        uid = f.fbind(
                            val, update_intermediates, base, keys, bound, k,
                            fn, args)
                        append([f.proxy_ref, val, update_intermediates, uid])
                        was_bound = True
                    else:
                        append([f.proxy_ref, val, None, None])
                elif not isinstance(f, type):
                    append([getattr(f, 'proxy_ref', f), val, None, None])
                else:
                    append([f, val, None, None])
                f = getattr(f, val, None)
                if f is None:
                    break
                k += 1

            # for the last attr we bind directly to the setting
            # function, because that attr sets the value of the rule.
            if isinstance(f, (EventDispatcher, Observable)):
                uid = f.fbind(keys[-1], fn, args)  # f is not None
                if uid:
                    append([f.proxy_ref, keys[-1], fn, uid])
                    was_bound = True
            if was_bound:
                handler_append(bound)

    try:
        return eval(value, idmap), bound_list
    except Exception as e:
        tb = sys.exc_info()[2]
        raise BuilderException(rule.ctx, rule.line,
                               '{}: {}'.format(e.__class__.__name__, e),
                               cause=tb)


# ---------------------------------------------------------------------------
# Control statements runtime
#
# Each control statement compiles to a small node owning a contiguous span of
# its parent container (widget children or canvas instructions) and rebuilding
# that span when its bound expression changes. Nodes live on the host widget
# (never in a module registry), so control-using widgets stay collectable.
# ---------------------------------------------------------------------------

# late import (kivy.graphics must not load at module import time)
InstructionGroup = None

# scope classes cache, keyed by the tuple of property names
_scope_classes = {}


def _make_scope(names):
    '''Build a hidden scope object: an EventDispatcher with one reactive,
    nullable, rebindable property per name (loop targets, locals, ids).'''
    key = tuple(names)
    cls = _scope_classes.get(key)
    if cls is None:
        cls = type('KvScope', (EventDispatcher,), {
            name: ObjectProperty(None, allownone=True, rebind=True)
            for name in key})
        _scope_classes[key] = cls
    return cls()


def _unbind_captured(uid, key, captured):
    '''Unbind exactly the handler entries `captured` (as returned by
    create_handler into ``_handlers[uid][key]``), leaving every other binding
    of the property untouched.'''
    plist = _handlers.get(uid)
    entries = plist.get(key) if plist is not None else None
    for bound in captured:
        for f, k, fn, bound_uid in bound:
            if fn is None:
                continue
            try:
                f.unbind_uid(k, bound_uid)
            except ReferenceError:
                pass
        if entries is not None and bound in entries:
            entries.remove(bound)
    if plist is not None and entries is not None and not entries:
        del plist[key]
        if not plist:
            del _handlers[uid]


def _items_count(items):
    n = 0
    for it in items:
        if isinstance(it, _ControlNode):
            n += it.count()
        else:
            n += 1
    return n


def _items_scan(items, target):
    '''Return (position, found): the document position of `target` within
    the entry structure `items` (descending into nodes).'''
    pos = 0
    for it in items:
        if it is target:
            return pos, True
        if isinstance(it, _ControlNode):
            sub, found = _items_scan(it.iter_items(), target)
            pos += sub
            if found:
                return pos, True
        else:
            pos += 1
    return pos, False


def _collect_item_widgets(items, out):
    for it in items:
        if isinstance(it, _ControlNode):
            _collect_item_widgets(it.iter_items(), out)
        else:
            out.append(it)


class _SlotEntry(object):
    __slots__ = ('node', 'fill')

    def __init__(self):
        self.node = None
        self.fill = None


class _ControlNode(EventDispatcher):
    '''Base runtime node for a control statement.'''

    value = ObjectProperty(None, allownone=True)

    def __init__(self, builder, host, ctl, idmap, for_scope=None, **kwargs):
        super(_ControlNode, self).__init__(**kwargs)
        self.builder = builder
        self.host = host
        self.ctl = ctl
        self.idmap = idmap
        self.for_scope = for_scope
        self.owner_rule = None
        self._expr_captured = []
        self._active = False

    def iter_items(self):
        return ()

    def count(self):
        return _items_count(self.iter_items())

    def _position(self):
        entries = self.host.__dict__.get('_kv_entries') or ()
        pos, found = _items_scan(entries, self)
        return pos

    def _insert_index(self, pos):
        children = self.host.children
        return max(0, min(len(children), len(children) - pos))

    def _bind_expr(self, prop):
        co = prop.co_value
        if type(co) is CodeType:
            host = self.host
            blist = _handlers[host.uid]['value']
            n = len(blist)
            value, _ = create_handler(
                host, self, 'value', co, prop, self.idmap)
            self._expr_captured = blist[n:]
        else:
            value = co
        self.value = value
        self.fbind('value', self._on_value)

    def _on_value(self, *largs):
        if not self._active:
            return
        builder = self.builder
        if self in builder._node_queue:
            return
        builder._node_queue.append(self)
        if not (builder._apply_depth or builder._processing):
            builder._process_queues()

    def _run_update(self):
        pass

    def teardown(self):
        self._active = False
        _unbind_captured(self.host.uid, 'value', self._expr_captured)
        self._expr_captured = []
        queue = self.builder._node_queue
        if self in queue:
            queue.remove(self)

    def _dispatch_kv_post(self, rule_children, built):
        # dynamic builds dispatch on_kv_post themselves; initial builds are
        # dispatched by the outer apply through `rule_children`
        if rule_children is None:
            for w in built:
                w.dispatch('on_kv_post', self.host)


_canvas_attrs = ('canvas_before', 'canvas_root', 'canvas_after')


class _CanvasMark(object):
    '''Position bookmark for a conditional canvas group: registered once per
    branch section in document order, mounted/unmounted with the branch so
    inactive branches leave nothing in the canvas.'''

    __slots__ = ('group', 'mounted')

    def __init__(self, group):
        self.group = group
        self.mounted = False


def _mark_register(host, canvas, mark):
    # registration happens at node activation, i.e. in document order
    host.__dict__.setdefault('_kv_canvas_marks', {}).setdefault(
        canvas, []).append(mark)


def _mark_mount(host, canvas, mark):
    if mark.mounted:
        return
    marks = host.__dict__['_kv_canvas_marks'][canvas]
    i = marks.index(mark)
    for j in range(i - 1, -1, -1):
        if marks[j].mounted:
            canvas.insert(canvas.indexof(marks[j].group) + 1, mark.group)
            break
    else:
        for j in range(i + 1, len(marks)):
            if marks[j].mounted:
                canvas.insert(canvas.indexof(marks[j].group), mark.group)
                break
        else:
            canvas.add(mark.group)
    mark.mounted = True


def _mark_unmount(canvas, mark):
    if not mark.mounted:
        return
    try:
        canvas.remove(mark.group)
    except Exception:
        pass
    mark.mounted = False


class IfNode(_ControlNode):
    '''An ``if`` / ``elif`` / ``else`` chain: mounts the active branch's
    children, host properties, handlers and canvas; tears them down when the
    branch leaves.'''

    def __init__(self, *largs, **kwargs):
        super(IfNode, self).__init__(*largs, **kwargs)
        self.active_index = -1
        self.items = []
        self._prop_captured = {}
        self._handler_uids = []
        self._canvas_groups = {}
        self._canvas_captured = []
        self._canvas_subnodes = []
        self._branch_ids = []

    def iter_items(self):
        return self.items

    def activate(self, rule_children=None, pos=None):
        global InstructionGroup
        host = self.host
        for index, branch in enumerate(self.ctl.branches):
            for attr in _canvas_attrs:
                if getattr(branch, attr) is None:
                    continue
                if InstructionGroup is None:
                    from kivy.graphics import InstructionGroup
                mark = _CanvasMark(InstructionGroup())
                _mark_register(host, self._canvas_for(attr), mark)
                self._canvas_groups[(index, attr)] = mark
        self._bind_expr(self.ctl.selector_prop)
        self._active = True
        self.active_index = -1
        self._mount(rule_children, pos)

    def _canvas_for(self, attr):
        host = self.host
        return (host.canvas if attr == 'canvas_root' else
                host.canvas.before if attr == 'canvas_before' else
                host.canvas.after)

    def _run_update(self):
        index = self.value
        index = -1 if index is None else int(index)
        if index == self.active_index:
            return
        self._unmount()
        self._mount(None, None)

    def _mount(self, rule_children, pos):
        index = self.value
        index = -1 if index is None else int(index)
        self.active_index = index
        branches = self.ctl.branches
        if index < 0 or index >= len(branches):
            return
        branch = branches[index]
        builder = self.builder
        host = self.host
        if pos is None:
            pos = self._position()
        built = rule_children if rule_children is not None else []
        log = builder._scope_id_log
        n = len(log)
        self.items = builder._build_items(
            host, branch.children, self.idmap, pos, built, self.for_scope)
        self._branch_ids = log[n:]
        del log[n:]
        self._mount_props(branch)
        self._mount_handlers(branch)
        self._mount_canvas(index, branch)
        self._dispatch_kv_post(rule_children, built)

    def _mount_props(self, branch):
        if not branch.properties:
            return
        host = self.host
        target = self.for_scope if self.for_scope is not None else host
        if target is host:
            branch.create_missing(host)
        self_ref = host.proxy_ref if target is not host else None
        for name, prop in branch.properties.items():
            co = prop.co_value
            if type(co) is CodeType:
                blist = _handlers[target.uid][name]
                n = len(blist)
                value, _ = create_handler(
                    target, target, name, co, prop, self.idmap,
                    self_ref=self_ref)
                self._prop_captured[name] = blist[n:]
            else:
                value = co
            setattr(target, name, value)

    def _mount_handlers(self, branch):
        host = self.host
        for crule in branch.handlers:
            key = crule.name
            if not host.is_event_type(key):
                key = key[3:]
            idmap = copy(global_idmap)
            idmap.update(self.idmap)
            idmap['self'] = host.proxy_ref
            uid = host.fbind(key, custom_callback, crule, idmap)
            if not uid:
                raise BuilderException(
                    crule.ctx, crule.line,
                    'AttributeError: %s' % crule.name)
            self._handler_uids.append((key, uid))
            if crule.name == 'on_parent':
                Factory.Widget.parent.dispatch(host.__self__)

    def _mount_canvas(self, index, branch):
        builder = self.builder
        for attr in _canvas_attrs:
            crule = getattr(branch, attr)
            if crule is None:
                continue
            mark = self._canvas_groups[(index, attr)]
            _mark_mount(self.host, self._canvas_for(attr), mark)
            builder._build_canvas_content(
                mark.group, self.host, crule, self.idmap,
                self._canvas_captured, self._canvas_subnodes)

    def _unmount(self):
        host = self.host
        builder = self.builder
        for scope, name, widget in self._branch_ids:
            try:
                if getattr(scope, name) == widget:
                    setattr(scope, name, None)
            except ReferenceError:
                pass
        self._branch_ids = []
        builder._teardown_items(host, self.items)
        self.items = []
        target = self.for_scope if self.for_scope is not None else host
        for name, captured in self._prop_captured.items():
            _unbind_captured(target.uid, name, captured)
        self._prop_captured = {}
        for key, uid in self._handler_uids:
            try:
                host.unbind_uid(key, uid)
            except ReferenceError:
                pass
        self._handler_uids = []
        for node in self._canvas_subnodes:
            node.teardown()
        self._canvas_subnodes = []
        for key, captured in self._canvas_captured:
            _unbind_captured(host.uid, key, captured)
        self._canvas_captured = []
        index = self.active_index
        for (branch_index, attr), mark in self._canvas_groups.items():
            if branch_index == index:
                mark.group.clear()
                _mark_unmount(self._canvas_for(attr), mark)
        self.active_index = -1

    def teardown(self):
        self._unmount()
        marks = self.host.__dict__.get('_kv_canvas_marks') or {}
        for (branch_index, attr), mark in self._canvas_groups.items():
            _mark_unmount(self._canvas_for(attr), mark)
            registry = marks.get(self._canvas_for(attr))
            if registry and mark in registry:
                registry.remove(mark)
        self._canvas_groups = {}
        super(IfNode, self).teardown()


class _Iteration(object):
    __slots__ = ('key', 'values', 'scope', 'items', 'detached')

    def __init__(self, key, values, scope, items):
        self.key = key
        self.values = values
        self.scope = scope
        self.items = items
        self.detached = None


class ForNode(_ControlNode):
    '''A ``for`` block: one copy of the body per item, reconciled as the
    iterable changes. Same key => same widgets: the loop targets live as
    reactive properties on a per-iteration scope, so a kept key with new
    values just re-dispatches them through the existing bindings.'''

    def __init__(self, *largs, **kwargs):
        super(ForNode, self).__init__(*largs, **kwargs)
        self.iterations = []

    def iter_items(self):
        for rec in self.iterations:
            for it in rec.items:
                yield it

    def activate(self, rule_children=None, pos=None):
        self._bind_expr(self.ctl.iterator_prop)
        self._active = True
        self._reconcile(rule_children, pos)

    def _run_update(self):
        self._reconcile(None, None)

    def _reconcile(self, rule_children, pos):
        builder = self.builder
        host = self.host
        ctl = self.ctl
        tuples = list(self.value or ())
        keys = self._compute_keys(tuples)
        recs = self.iterations
        old_by_key = {rec.key: rec for rec in recs}
        new_keys = set(keys)
        for rec in recs[:]:
            if rec.key not in new_keys:
                self._destroy_iteration(rec)
                recs.remove(rec)
        moved = [rec.key for rec in recs] != [
            k for k in keys if k in old_by_key]
        if moved:
            for rec in recs:
                self._detach(rec)
        if pos is None:
            pos = self._position()
        built = rule_children if rule_children is not None else []
        cursor = pos
        new_recs = []
        targets = ctl.target_names
        for key, tup in zip(keys, tuples):
            rec = old_by_key.get(key)
            if rec is not None:
                if moved:
                    cursor += self._reattach(rec, cursor)
                else:
                    cursor += _items_count(rec.items)
                scope = rec.scope
                for name, v in zip(targets, tup):
                    setattr(scope, name, v)
                rec.values = tup
            else:
                rec = self._build_iteration(key, tup, cursor, built)
                cursor += _items_count(rec.items)
            new_recs.append(rec)
        self.iterations = new_recs
        self._dispatch_kv_post(rule_children, built)

    def _compute_keys(self, tuples):
        ctl = self.ctl
        prop = ctl.key_prop
        if prop is None:
            return list(range(len(tuples)))
        co = prop.co_value
        if type(co) is not CodeType:
            keys = [co] * len(tuples)
        else:
            base = copy(self.idmap)
            base.update(global_idmap)
            base['self'] = self.host.proxy_ref
            targets = ctl.target_names
            keys = []
            for tup in tuples:
                idmap = dict(base)
                idmap.update(zip(targets, tup))
                try:
                    keys.append(eval(co, idmap))
                except Exception as e:
                    tb = sys.exc_info()[2]
                    raise BuilderException(
                        prop.ctx, prop.line,
                        '{}: {}'.format(e.__class__.__name__, e), cause=tb)
        seen = set()
        for key in keys:
            try:
                duplicate = key in seen
                seen.add(key)
            except TypeError as e:
                tb = sys.exc_info()[2]
                raise BuilderException(
                    ctl.ctx, ctl.line, 'keys of a "for" block must be '
                    'hashable ({})'.format(e), cause=tb)
            if duplicate:
                raise BuilderException(
                    ctl.ctx, ctl.line,
                    'duplicate key %r in "for" block' % (key,))
        return keys

    def _build_iteration(self, key, tup, cursor, built):
        builder = self.builder
        host = self.host
        ctl = self.ctl
        scope = _make_scope(ctl.scope_names)
        for name, v in zip(ctl.target_names, tup):
            setattr(scope, name, v)
        idmap = dict(self.idmap)
        idmap[ctl.scope_key] = scope
        host_proxy = host.proxy_ref
        for name, prop in ctl.locals:
            co = prop.co_value
            if type(co) is CodeType:
                v, _ = create_handler(
                    scope, scope, name, co, prop, idmap, self_ref=host_proxy)
            else:
                v = co
            setattr(scope, name, v)
        log = builder._scope_id_log
        n = len(log)
        items = builder._build_items(
            host, ctl.children, idmap, cursor, built, scope)
        del log[n:]
        return _Iteration(key, tup, scope, items)

    def _destroy_iteration(self, rec):
        self.builder._teardown_items(self.host, rec.items)
        self.builder.unbind_widget(rec.scope.uid)

    def _detach(self, rec):
        widgets = []
        _collect_item_widgets(rec.items, widgets)
        host = self.host
        for w in widgets:
            host.remove_widget(w)
        rec.detached = widgets

    def _reattach(self, rec, cursor):
        widgets = rec.detached or []
        rec.detached = None
        index = self._insert_index(cursor)
        host = self.host
        for w in widgets:
            host.add_widget(w, index=index)
        return len(widgets)

    def teardown(self):
        for rec in self.iterations:
            self._destroy_iteration(rec)
        self.iterations = []
        super(ForNode, self).teardown()


class FactoryNode(_ControlNode):
    '''A ``factory <expr>`` block: one child whose class comes from an
    expression, rebuilt when the class changes; the block body is applied to
    the instance as an ordinary rule.'''

    def __init__(self, *largs, **kwargs):
        super(FactoryNode, self).__init__(*largs, **kwargs)
        self.items = []

    def iter_items(self):
        return self.items

    def activate(self, rule_children=None, pos=None):
        self._bind_expr(self.ctl.class_prop)
        self._active = True
        self._build(rule_children, pos)

    def _run_update(self):
        # resolve first: two expressions naming the same class (an alias, a
        # string vs the class object) must not rebuild the widget
        cls = self._resolve_class()
        if self.items and type(self.items[0]) is cls:
            return
        self.builder._teardown_items(self.host, self.items)
        self.items = []
        self._build_resolved(cls, None, None)

    def _resolve_class(self):
        value = self.value
        if value is None or not isinstance(value, str):
            return value
        try:
            return Factory.get(value)
        except Exception as e:
            tb = sys.exc_info()[2]
            raise BuilderException(
                self.ctl.ctx, self.ctl.line,
                '{}: {}'.format(e.__class__.__name__, e), cause=tb)

    def _build(self, rule_children, pos):
        self._build_resolved(self._resolve_class(), rule_children, pos)

    def _build_resolved(self, cls, rule_children, pos):
        if cls is None:
            return
        ctl = self.ctl
        builder = self.builder
        host = self.host
        if pos is None:
            pos = self._position()
        try:
            widget = cls(__no_builder=True)
        except Exception as e:
            tb = sys.exc_info()[2]
            raise BuilderException(
                ctl.ctx, ctl.line,
                '{}: {}'.format(e.__class__.__name__, e), cause=tb)
        host.add_widget(widget, index=self._insert_index(pos))
        built = rule_children if rule_children is not None else []
        widget.apply_class_lang_rules(
            root=self.idmap.get('root'), rule_children=built)
        builder._apply_rule(
            widget, ctl, ctl, rule_children=built, ids=dict(self.idmap))
        built.append(widget)
        self.items = [widget]
        self._dispatch_kv_post(rule_children, built)

    def teardown(self):
        self.builder._teardown_items(self.host, self.items)
        self.items = []
        super(FactoryNode, self).teardown()


class SlotNode(_ControlNode):
    '''A slot definition site: builds the best fill recorded on the host
    widget, or its own fallback. Slot-scoped locals are exposed to the
    content through the reserved ``slot`` name.'''

    def __init__(self, *largs, **kwargs):
        super(SlotNode, self).__init__(*largs, **kwargs)
        self.items = []
        self.scope = None
        self._content_ids = []

    def iter_items(self):
        return self.items

    def activate(self, rule_children=None, pos=None):
        self._active = True
        self._build(rule_children, pos)

    def _build(self, rule_children, pos):
        builder = self.builder
        host = self.host
        ctl = self.ctl
        slots = host.__dict__.get('_kv_slots') or {}
        entry = slots.get(ctl.slot_name)
        fill = entry.fill if entry is not None else None
        if fill is not None:
            crules, source_ids, fill_locals = fill
        else:
            crules, source_ids, fill_locals = ctl.children, self.idmap, []
        local_defs = list(ctl.locals)
        names = []
        for name, _ in local_defs + list(fill_locals):
            if name not in names:
                names.append(name)
        scope = _make_scope(names) if names else None
        self.scope = scope
        host_proxy = host.proxy_ref

        def bind_locals(pairs, base_ids):
            idmap = dict(base_ids)
            idmap['slot'] = scope
            for name, prop in pairs:
                co = prop.co_value
                if type(co) is CodeType:
                    v, _ = create_handler(
                        scope, scope, name, co, prop, idmap,
                        self_ref=host_proxy)
                else:
                    v = co
                setattr(scope, name, v)

        if scope is not None:
            bind_locals(local_defs, self.idmap)
            if fill_locals:
                bind_locals(fill_locals, source_ids)
        content_ids = dict(source_ids)
        if scope is not None:
            content_ids['slot'] = scope
        if pos is None:
            pos = self._position()
        built = rule_children if rule_children is not None else []
        log = builder._scope_id_log
        n = len(log)
        self.items = builder._build_items(
            host, crules, content_ids, pos, built, None)
        self._content_ids = log[n:]
        del log[n:]
        self._dispatch_kv_post(rule_children, built)

    def teardown(self):
        for scope, name, widget in self._content_ids:
            try:
                if getattr(scope, name) == widget:
                    setattr(scope, name, None)
            except ReferenceError:
                pass
        self._content_ids = []
        self.builder._teardown_items(self.host, self.items)
        self.items = []
        if self.scope is not None:
            self.builder.unbind_widget(self.scope.uid)
            self.scope = None
        slots = self.host.__dict__.get('_kv_slots')
        if slots is not None:
            entry = slots.get(self.ctl.slot_name)
            if entry is not None and entry.node is self:
                entry.node = None
        super(SlotNode, self).teardown()


class _CanvasNode(_ControlNode):
    '''Base for canvas control nodes: owns one InstructionGroup slotted at
    the block's position in the enclosing canvas (or group).'''

    def __init__(self, builder, host, ctl, idmap, group, **kwargs):
        super(_CanvasNode, self).__init__(builder, host, ctl, idmap, **kwargs)
        self.group = group
        self._captured = []
        self._subnodes = []

    def _clear_content(self):
        for node in self._subnodes:
            node.teardown()
        self._subnodes = []
        for key, captured in self._captured:
            _unbind_captured(self.host.uid, key, captured)
        self._captured = []
        self.group.clear()

    def teardown(self):
        self._clear_content()
        super(_CanvasNode, self).teardown()


class CanvasIfNode(_CanvasNode):

    def __init__(self, *largs, **kwargs):
        super(CanvasIfNode, self).__init__(*largs, **kwargs)
        self.active_index = -1

    def activate(self, rule_children=None, pos=None):
        self._bind_expr(self.ctl.selector_prop)
        self._active = True
        self._mount()

    def _run_update(self):
        index = self.value
        index = -1 if index is None else int(index)
        if index == self.active_index:
            return
        self._clear_content()
        self._mount()

    def _mount(self):
        index = self.value
        index = -1 if index is None else int(index)
        self.active_index = index
        branches = self.ctl.branches
        if index < 0 or index >= len(branches):
            return
        self.builder._build_canvas_content(
            self.group, self.host, branches[index], self.idmap,
            self._captured, self._subnodes)


class _CanvasSub(object):
    __slots__ = ('group', 'values', 'captured', 'subnodes')

    def __init__(self, group):
        self.group = group
        self.values = None
        self.captured = []
        self.subnodes = []


class CanvasForNode(_CanvasNode):
    '''A canvas ``for``. Without ``key:`` the group is rebuilt wholesale;
    with it, per-iteration sub-groups are kept, moved or rebuilt by key.'''

    def __init__(self, *largs, **kwargs):
        super(CanvasForNode, self).__init__(*largs, **kwargs)
        self.subs = {}
        self._order = []

    def activate(self, rule_children=None, pos=None):
        self._bind_expr(self.ctl.iterator_prop)
        self._active = True
        self._mount()

    def _run_update(self):
        self._mount()

    def _content_idmap(self, tup):
        idmap = dict(self.idmap)
        idmap.update(zip(self.ctl.target_names, tup))
        return idmap

    def _mount(self):
        global InstructionGroup
        builder = self.builder
        ctl = self.ctl
        tuples = list(self.value or ())
        if ctl.key_prop is None:
            self._clear_content()
            for tup in tuples:
                builder._build_canvas_content(
                    self.group, self.host, ctl, self._content_idmap(tup),
                    self._captured, self._subnodes)
            return
        # keyed: reconcile per-iteration sub-groups
        keys = ForNode._compute_keys(self, tuples)
        if InstructionGroup is None:
            from kivy.graphics import InstructionGroup
        old = self.subs
        new_keys = set(keys)
        for key in list(old):
            if key not in new_keys:
                sub = old.pop(key)
                self._destroy_sub(sub, remove=True)
        self._order = [k for k in self._order if k in new_keys]
        subs = {}
        for key, tup in zip(keys, tuples):
            sub = old.get(key)
            if sub is None:
                sub = _CanvasSub(InstructionGroup())
                self.group.add(sub.group)
                self._fill_sub(sub, tup)
            elif sub.values != tup:
                self._destroy_sub(sub, remove=False)
                self._fill_sub(sub, tup)
            subs[key] = sub
        # kept groups sit in old order and new ones were appended in new
        # order, so nothing moves when the kept order is a prefix of the new
        if self._order != keys[:len(self._order)]:
            for sub in subs.values():
                try:
                    self.group.remove(sub.group)
                except Exception:
                    pass
            for key in keys:
                self.group.add(subs[key].group)
        self.subs = subs
        self._order = keys

    def _fill_sub(self, sub, tup):
        sub.values = tup
        self.builder._build_canvas_content(
            sub.group, self.host, self.ctl, self._content_idmap(tup),
            sub.captured, sub.subnodes)

    def _destroy_sub(self, sub, remove):
        for node in sub.subnodes:
            node.teardown()
        sub.subnodes = []
        for key, captured in sub.captured:
            _unbind_captured(self.host.uid, key, captured)
        sub.captured = []
        sub.group.clear()
        if remove:
            try:
                self.group.remove(sub.group)
            except Exception:
                pass

    def _clear_content(self):
        for sub in self.subs.values():
            self._destroy_sub(sub, remove=False)
        self.subs = {}
        self._order = []
        super(CanvasForNode, self)._clear_content()

    def teardown(self):
        self._clear_content()
        _ControlNode.teardown(self)


class BuilderBase(object):
    '''The Builder is responsible for creating a :class:`Parser` for parsing a
    kv file, merging the results into its internal rules, dynamic classes,
    etc.

    By default, :class:`Builder` is a global Kivy instance used in widgets
    that you can use to load other kv files in addition to the default ones.

    See :mod:`kivy.lang` for details about the rules built here.

    :attributes:
        `files`: list
            Filenames of Kivy-language code that have already been loaded.
            Not necessarily real files on disk; see :meth:`load_string`.
        `dynamic_classes`:  dict
            Classes crated in Kivy-language code.
            They were created with the ``<Class@Superclass>:`` syntax,
            rather than in Python.
        `rules`: list
            Rules loaded from Kivy-language code.
        `rulectx`: dict
            Context used by each rule.
            Mostly, the IDs of widgets.

    .. versionchanged:: 3.0.0
        The deprecated Kivy lang templates feature has been removed.
        ``Builder.template`` and the ``Builder.templates`` dict no longer
        exist; use dynamic classes (``<Name@Base>:``) instead.
    '''

    def __init__(self):
        super(BuilderBase, self).__init__()
        self._match_cache = {}
        self._match_name_cache = {}
        self.files = []
        self.dynamic_classes = {}
        self.rules = []
        self.rulectx = {}
        # control statements runtime state
        self._apply_depth = 0
        self._processing = False
        self._pending = []
        self._node_queue = []
        self._scope_id_log = []
        # rule_children lists awaiting their on_kv_post dispatch: a widget
        # destroyed while one is pending is scrubbed from it, so the event
        # never fires on a widget a control statement already tore down
        self._rc_stack = []

    def _end_apply(self, failed=False):
        # closes one apply level; at the outermost level, either run the
        # deferred control-statement work or (on failure) drop it
        self._apply_depth -= 1
        if self._apply_depth == 0:
            if failed:
                del self._pending[:]
                del self._node_queue[:]
            elif not self._processing:
                self._process_queues()

    def _process_queues(self):
        '''Run deferred control-statement builds and queued node updates
        until both queues drain. Content built here may enqueue more work
        (nested rules, reactive handlers); an update firing while another
        apply or rebuild is in flight lands in these queues instead of
        re-entering it.'''
        if self._processing:
            return
        self._processing = True
        try:
            while self._pending or self._node_queue:
                if self._pending:
                    self._pending.pop(0)()
                else:
                    self._node_queue.pop(0)._run_update()
        except BaseException:
            del self._pending[:]
            del self._node_queue[:]
            raise
        finally:
            self._processing = False

    @classmethod
    def create_from(cls, builder):
        """Creates a instance of the class, and initializes to the state of
        ``builder``.

        :param builder: The builder to initialize from.
        :return: A new instance of this class.
        """
        obj = cls()
        obj._match_cache = copy(builder._match_cache)
        obj._match_name_cache = copy(builder._match_name_cache)
        obj.files = copy(builder.files)
        obj.dynamic_classes = copy(builder.dynamic_classes)
        obj.rules = list(builder.rules)
        assert not builder.rulectx
        obj.rulectx = dict(builder.rulectx)

        return obj

    def load_file(self, filename, encoding='utf8', **kwargs):
        '''Insert a file into the language builder and return the root widget
        (if defined) of the kv file.

        :parameters:
            `rulesonly`: bool, defaults to False
                If True, the Builder will raise an exception if you have a root
                widget inside the definition.

            `encoding`: File character encoding. Defaults to utf-8,

        .. versionchanged:: 3.0.0
            `filename` may be a :class:`os.PathLike` (e.g. :class:`pathlib.Path`)
            in addition to a ``str``.
        '''

        filename = path_to_str(filename)
        filename = resource_find(filename) or filename
        if __debug__:
            trace('Lang: load file %s, using %s encoding', filename, encoding)

        kwargs['filename'] = filename
        with open(filename, 'r', encoding=encoding) as fd:
            data = fd.read()
            return self.load_string(data, **kwargs)

    def unload_file(self, filename):
        '''Unload all rules associated with a previously imported file.

        .. versionadded:: 1.0.8

        .. warning::

            This will not remove rules already applied/used on current
            widgets. It will only effect the next widgets creation.

        .. versionchanged:: 3.0.0
            `filename` may be a :class:`os.PathLike` (e.g. :class:`pathlib.Path`)
            in addition to a ``str``.
        '''
        # remove rules associated with this file
        filename = path_to_str(filename)
        filename = resource_find(filename) or filename
        self.rules = [x for x in self.rules if x[1].ctx.filename != filename]
        self._clear_matchcache()

        if filename in self.files:
            self.files.remove(filename)

        # unregister all the dynamic classes
        Factory.unregister_from_filename(filename)

    def load_string(self, string, **kwargs):
        '''Insert a string into the Language Builder and return the root widget
        (if defined) of the kv string.

        :Parameters:
            `rulesonly`: bool, defaults to False
                If True, the Builder will raise an exception if you have a root
                widget inside the definition.
            `filename`: str, defaults to None
                If specified, the filename used to index the kv rules.

        The filename parameter can be used to unload kv strings in the same way
        as you unload kv files. This can be achieved using pseudo file names
        e.g.::

            Build.load_string("""
                <MyRule>:
                    Label:
                        text="Hello"
            """, filename="myrule.kv")

        can be unloaded via::

            Build.unload_file("myrule.kv")

        '''

        kwargs.setdefault('rulesonly', False)
        self._current_filename = fn = path_to_str(kwargs.get('filename', None))

        # put a warning if a file is loaded multiple times
        if fn in self.files:
            Logger.warning(
                'Lang: The file {} is loaded multiples times, '
                'you might have unwanted behaviors.'.format(fn))

        try:
            # parse the string
            parser = Parser(content=string, filename=fn)

            # merge rules with our rules
            self.rules.extend(parser.rules)
            self._clear_matchcache()

            # register all the dynamic classes
            for name, baseclasses in parser.dynamic_classes.items():
                Factory.register(name, baseclasses=baseclasses, filename=fn,
                                 warn=True)

            # create root object is exist
            if kwargs['rulesonly'] and parser.root:
                filename = kwargs.get('rulesonly', '<string>')
                raise Exception('The file <%s> contain also non-rules '
                                'directives' % filename)

            # save the loaded files only if there is a root without
            # dynamic classes
            if fn and (parser.dynamic_classes or parser.rules):
                self.files.append(fn)

            if parser.root:
                widget = Factory.get(parser.root.name)(__no_builder=True)
                rule_children = []
                # one apply level for the whole root build, so deferred
                # control-statement work (branches, slots) runs only once
                # every rule -- class and root -- has been applied
                self._apply_depth += 1
                self._rc_stack.append(rule_children)
                failed = True
                try:
                    widget.apply_class_lang_rules(
                        root=widget, rule_children=rule_children)
                    self._apply_rule(
                        widget, parser.root, parser.root,
                        rule_children=rule_children)
                    failed = False
                finally:
                    self._end_apply(failed=failed)
                    self._rc_stack.pop()

                for child in rule_children:
                    child.dispatch('on_kv_post', widget)
                widget.dispatch('on_kv_post', widget)
                return widget
        finally:
            self._current_filename = None

    def apply_rules(
            self, widget, rule_name, ignored_consts=set(), rule_children=None,
            dispatch_kv_post=False):
        '''Search all the rules that match the name `rule_name`
        and apply them to `widget`.

        .. versionadded:: 1.10.0

        :Parameters:

            `widget`: :class:`~kivy.uix.widget.Widget`
                The widget to whom the matching rules should be applied to.
            `ignored_consts`: set
                A set or list type whose elements are property names for which
                constant KV rules (i.e. those that don't create bindings) of
                that widget will not be applied. This allows e.g. skipping
                constant rules that overwrite a value initialized in python.
            `rule_children`: list
                If not ``None``, it should be a list that will be populated
                with all the widgets created by the kv rules being applied.

                .. versionchanged:: 1.11.0

            `dispatch_kv_post`: bool
                Normally the class `Widget` dispatches the `on_kv_post` event
                to widgets created during kv rule application.
                But if the rules are manually applied by calling :meth:`apply`,
                that may not happen, so if this is `True`, we will dispatch the
                `on_kv_post` event where needed after applying the rules to
                `widget` (we won't dispatch it for `widget` itself).

                Defaults to False.

                .. versionchanged:: 1.11.0
        '''
        rules = self.match_rule_name(rule_name)
        if __debug__:
            trace('Lang: Found %d rules for %s' % (len(rules), rule_name))
        if not rules:
            return

        if dispatch_kv_post:
            rule_children = rule_children if rule_children is not None else []
        self._apply_depth += 1
        if rule_children is not None:
            self._rc_stack.append(rule_children)
        failed = True
        try:
            for rule in rules:
                self._apply_rule(
                    widget, rule, rule, ignored_consts=ignored_consts,
                    rule_children=rule_children)
            failed = False
        finally:
            self._end_apply(failed=failed)
            if rule_children is not None:
                self._rc_stack.pop()
        if dispatch_kv_post:
            for w in rule_children:
                w.dispatch('on_kv_post', widget)

    def apply(self, widget, ignored_consts=set(), rule_children=None,
              dispatch_kv_post=False):
        '''Search all the rules that match the widget and apply them.

        :Parameters:

            `widget`: :class:`~kivy.uix.widget.Widget`
                The widget whose class rules should be applied to this widget.
            `ignored_consts`: set
                A set or list type whose elements are property names for which
                constant KV rules (i.e. those that don't create bindings) of
                that widget will not be applied. This allows e.g. skipping
                constant rules that overwrite a value initialized in python.
            `rule_children`: list
                If not ``None``, it should be a list that will be populated
                with all the widgets created by the kv rules being applied.

                .. versionchanged:: 1.11.0

            `dispatch_kv_post`: bool
                Normally the class `Widget` dispatches the `on_kv_post` event
                to widgets created during kv rule application.
                But if the rules are manually applied by calling :meth:`apply`,
                that may not happen, so if this is `True`, we will dispatch the
                `on_kv_post` event where needed after applying the rules to
                `widget` (we won't dispatch it for `widget` itself).

                Defaults to False.

                .. versionchanged:: 1.11.0
        '''
        rules = self.match(widget)
        if __debug__:
            trace('Lang: Found %d rules for %s' % (len(rules), widget))
        if not rules:
            return

        if dispatch_kv_post:
            rule_children = rule_children if rule_children is not None else []
        self._apply_depth += 1
        if rule_children is not None:
            self._rc_stack.append(rule_children)
        failed = True
        try:
            for rule in rules:
                self._apply_rule(
                    widget, rule, rule, ignored_consts=ignored_consts,
                    rule_children=rule_children)
            failed = False
        finally:
            self._end_apply(failed=failed)
            if rule_children is not None:
                self._rc_stack.pop()
        if dispatch_kv_post:
            for w in rule_children:
                w.dispatch('on_kv_post', widget)

    def _clear_matchcache(self):
        self._match_cache.clear()
        self._match_name_cache.clear()

    def _apply_rule(self, widget, rule, rootrule,
                    ignored_consts=set(), rule_children=None, ids=None):
        # widget: the current instantiated widget
        # rule: the current rule
        # rootrule: the current root rule (for children of a rule)
        # ids: pre-seeded ids context (used when control statements rebuild
        #      content outside the original rule application)

        # will collect reference to all the id in children
        assert rule not in self.rulectx
        self.rulectx[rule] = {
            'ids': ids if ids is not None else {'root': widget.proxy_ref},
            'set': [], 'hdl': []}

        # extract the context of the rootrule (not rule!)
        assert rootrule in self.rulectx
        rctx = self.rulectx[rootrule]

        self._apply_depth += 1
        failed = True
        try:
            self._apply_rule_body(
                widget, rule, rootrule, rctx, ignored_consts, rule_children)
            failed = False
        except Exception:
            self.rulectx.pop(rule, None)
            raise
        finally:
            self._end_apply(failed=failed)

    def _apply_rule_body(self, widget, rule, rootrule, rctx,
                         ignored_consts, rule_children):
        if rootrule is rule:
            # re-applying a rule to a widget resets its control nodes
            if (widget.__dict__.get('_kv_control_nodes') or
                    widget.__dict__.get('_kv_slots')):
                self._reset_control_state(widget, rule)
            # rule-level reactive-id scope (ids in `if`/`slot` blocks)
            if rule.id_scope_key is not None:
                scope = _make_scope(rule.id_scope_names)
                rctx['ids'][rule.id_scope_key] = scope
                widget.__dict__.setdefault('_kv_id_scopes', []).append(scope)

        # if we got an id, put it in the root rule for a later global usage
        if rule.id:
            # use only the first word as `id` discard the rest.
            rule.id = rule.id.split('#', 1)[0].strip()
            rctx['ids'][rule.id] = widget.proxy_ref
            # set id name as a attribute for root widget so one can in python
            # code simply access root_widget.id_name
            _ids = dict(rctx['ids'])
            _root = _ids.pop('root')
            _new_ids = _root.ids
            for _key, _value in _ids.items():
                if _value == _root:
                    # skip on self
                    continue
                if _key.startswith('__kvscope'):
                    # hidden scope objects are not ids
                    continue
                _new_ids[_key] = _value
            _root.ids = _new_ids

        # first, ensure that the widget have all the properties used in
        # the rule if not, they will be created as ObjectProperty.
        rule.create_missing(widget)

        # register the slot names this rule declares, so fills arriving from
        # later rules (subclasses, the usage site) find their target
        slots = widget.__dict__.get('_kv_slots')
        if rule.slot_defs:
            if slots is None:
                slots = widget._kv_slots = {}
            for name in rule.slot_defs:
                slots.setdefault(name, _SlotEntry())

        # build the widget canvas
        if rule.canvas_before:
            with widget.canvas.before:
                self._build_canvas(widget.canvas.before, widget,
                                   rule.canvas_before, rootrule)
        if rule.canvas_root:
            with widget.canvas:
                self._build_canvas(widget.canvas, widget,
                                   rule.canvas_root, rootrule)
        if rule.canvas_after:
            with widget.canvas.after:
                self._build_canvas(widget.canvas.after, widget,
                                   rule.canvas_after, rootrule)

        # create children tree. Rules using control statements (or applied
        # to a widget with slots or tracked entries) additionally maintain
        # the entry structure nodes use to track their spans; a control-free
        # rule on a plain widget only pays the two boolean tests.
        Factory_get = Factory.get
        route_default = (
            slots is not None and '' in slots and
            not (rule.slot_defs and '' in rule.slot_defs))
        entries = widget.__dict__.get('_kv_entries')
        tracked = rule.has_controls or route_default or entries is not None
        if tracked:
            if entries is None:
                entries = widget._kv_entries = list(
                    reversed(widget.children))
            nodes = widget.__dict__.get('_kv_control_nodes')
            if nodes is None:
                nodes = widget._kv_control_nodes = []
        routed = []
        explicit_default = False
        ids = rctx['ids']
        for crule in rule.children:
            if tracked and isinstance(crule, ParserControlRule):
                if crule.kind == 'slot':
                    node, is_default_fill = self._register_slot_block(
                        widget, rule, rootrule, crule, ids, rule_children)
                    if node is not None:
                        entries.append(node)
                    explicit_default = explicit_default or is_default_fill
                    if explicit_default and routed:
                        raise BuilderException(
                            crule.ctx, crule.line, 'cannot mix an explicit '
                            '"slot:" fill block with plain children')
                    continue
                node = self._make_control_node(widget, crule, ids, None)
                node.owner_rule = rootrule
                entries.append(node)
                nodes.append(node)
                self._pending.append(partial(node.activate, rule_children))
                continue

            cname = crule.name
            if cname in ('canvas', 'canvas.before', 'canvas.after'):
                raise ParserException(
                    crule.ctx, crule.line,
                    'Canvas instructions added in kv must '
                    'be declared before child widgets.')
            if route_default:
                if explicit_default:
                    raise BuilderException(
                        crule.ctx, crule.line, 'cannot mix an explicit '
                        '"slot:" fill block with plain children')
                self._check_routed_ids(crule)
                routed.append(crule)
                continue

            cls = Factory_get(cname)

            # we can't construct it without __no_builder=True, because
            # the previous implementation was doing the add_widget()
            # before apply(), and so, we could use "self.parent".
            child = cls(__no_builder=True)
            widget.add_widget(child)
            if tracked:
                entries.append(child)
            if crule.scope_id is not None:
                self._assign_scope_id(ids, crule.scope_id, child)
            child.apply_class_lang_rules(
                root=ids['root'], rule_children=rule_children)
            self._apply_rule(
                child, crule, rootrule, rule_children=rule_children)

            if rule_children is not None:
                rule_children.append(child)
        if routed:
            widget._kv_slots[''].fill = (routed, ids, [])

        # append the properties and handlers to our final resolution task
        if rule.properties:
            rctx['set'].append((widget.proxy_ref,
                                list(rule.properties.values())))
            for key, crule in rule.properties.items():
                # clear previously applied rules if asked
                if crule.ignore_prev:
                    Builder.unbind_property(widget, key)
        if rule.handlers:
            rctx['hdl'].append((widget.proxy_ref, rule.handlers))

        # if we are applying another rule that the root one, then it's done
        # for us!
        if rootrule is not rule:
            del self.rulectx[rule]
            return

        # normally, we can apply a list of properties with a proper context
        try:
            rule = None
            for widget_set, rules in reversed(rctx['set']):
                for rule in rules:
                    assert isinstance(rule, ParserRuleProperty)
                    key = rule.name
                    value = rule.co_value
                    if type(value) is CodeType:
                        value, bound = create_handler(
                            widget_set, widget_set, key, value, rule,
                            rctx['ids'])
                        # if there's a rule
                        if (widget_set != widget or bound or
                                key not in ignored_consts):
                            setattr(widget_set, key, value)
                    else:
                        if (widget_set != widget or
                                key not in ignored_consts):
                            setattr(widget_set, key, value)

        except Exception as e:
            if rule is not None:
                tb = sys.exc_info()[2]
                raise BuilderException(rule.ctx, rule.line,
                                       '{}: {}'.format(e.__class__.__name__,
                                                       e), cause=tb)
            raise e

        # build handlers
        try:
            crule = None
            for widget_set, rules in rctx['hdl']:
                for crule in rules:
                    assert isinstance(crule, ParserRuleProperty)
                    assert crule.name.startswith('on_')
                    key = crule.name
                    if not widget_set.is_event_type(key):
                        key = key[3:]
                    idmap = copy(global_idmap)
                    idmap.update(rctx['ids'])
                    idmap['self'] = widget_set.proxy_ref
                    if not widget_set.fbind(key, custom_callback, crule,
                                            idmap):
                        raise AttributeError(key)
                    # hack for on_parent
                    if crule.name == 'on_parent':
                        Factory.Widget.parent.dispatch(widget_set.__self__)
        except Exception as e:
            if crule is not None:
                tb = sys.exc_info()[2]
                raise BuilderException(
                    crule.ctx, crule.line,
                    '{}: {}'.format(e.__class__.__name__, e), cause=tb)
            raise e

        # rule finished, forget it
        del self.rulectx[rootrule]

    #
    # Control statements runtime support
    #

    def _register_slot_block(self, widget, rule, rootrule, crule, ids,
                             rule_children):
        '''Process one ``slot`` block: the first block for a declared name is
        the definition (a node is created at this position); later same-name
        blocks are fills. An unknown name degrades to a new definition, with
        a warning (it can never be filled).'''
        slots = widget.__dict__.get('_kv_slots')
        if slots is None:
            slots = widget._kv_slots = {}
        name = crule.slot_name
        entry = slots.get(name)
        if entry is None:
            Logger.warning(
                "Lang: filling unknown slot '%s': no class rule of <%s> "
                'declares it; treating the block as a new slot definition'
                % (name, type(widget).__name__))
            entry = slots[name] = _SlotEntry()
        elif not (entry.node is None and rule.slot_defs and
                  name in rule.slot_defs):
            # a fill: most derived provider wins (later rules overwrite)
            entry.fill = (list(crule.children), ids, list(crule.locals))
            return None, name == ''
        node = SlotNode(self, widget, crule, ids)
        node.owner_rule = rootrule
        entry.node = node
        self._pending.append(partial(node.activate, rule_children))
        return node, False

    def _check_routed_ids(self, crule):
        if not isinstance(crule, ParserControlRule) and crule.id:
            raise BuilderException(
                crule.ctx, crule.line, '"id" is not allowed on children '
                'routed into a slot; use an explicit "slot:" fill block '
                'instead')
        for child in crule.children:
            self._check_routed_ids(child)

    def _assign_scope_id(self, ids, scope_id, widget):
        scope_key, name = scope_id
        scope = ids.get(scope_key)
        if scope is not None:
            setattr(scope, name, widget)
            self._scope_id_log.append((scope, name, widget))

    def _make_control_node(self, widget, ctl, ids, for_scope):
        kind = ctl.kind
        if kind == 'if':
            return IfNode(self, widget, ctl, ids, for_scope=for_scope)
        if kind == 'for':
            return ForNode(self, widget, ctl, ids)
        return FactoryNode(self, widget, ctl, ids)

    def _build_items(self, host, crules, ids, pos, rule_children, for_scope):
        '''Build the entries `crules` (widgets and nested control statements)
        as children of `host`, starting at document position `pos`, with the
        ids context `ids`. Returns the item list.'''
        items = []
        cursor = pos
        for crule in crules:
            if isinstance(crule, ParserControlRule):
                if crule.kind == 'slot':
                    slots = host.__dict__.setdefault('_kv_slots', {})
                    entry = slots.setdefault(crule.slot_name, _SlotEntry())
                    node = SlotNode(self, host, crule, ids)
                    entry.node = node
                else:
                    node = self._make_control_node(host, crule, ids,
                                                   for_scope)
                items.append(node)
                node.activate(rule_children, cursor)
                cursor += node.count()
            else:
                child = self._build_child(
                    host, crule, ids, cursor, rule_children)
                items.append(child)
                cursor += 1
        return items

    def _build_child(self, host, crule, ids, cursor, rule_children):
        cls = Factory.get(crule.name)
        child = cls(__no_builder=True)
        children = host.children
        index = max(0, min(len(children), len(children) - cursor))
        host.add_widget(child, index=index)
        if crule.scope_id is not None:
            self._assign_scope_id(ids, crule.scope_id, child)
        child.apply_class_lang_rules(
            root=ids.get('root'), rule_children=rule_children)
        self._apply_rule(
            child, crule, crule, rule_children=rule_children, ids=dict(ids))
        if rule_children is not None:
            rule_children.append(child)
        return child

    def _teardown_items(self, host, items):
        for it in items:
            if isinstance(it, _ControlNode):
                it.teardown()
            else:
                self._destroy_widget(host, it)

    def _destroy_widget(self, host, widget):
        for sub in widget.walk(restrict=True):
            self.unbind_widget(sub.uid)
            for sink in self._rc_stack:
                try:
                    sink.remove(sub)
                except ValueError:
                    pass
        if widget.parent is host:
            host.remove_widget(widget)

    def _reset_control_state(self, widget, rule):
        '''Re-applying a rule to a widget tears down the control nodes that
        rule created before, so they are not duplicated.'''
        nodes = widget.__dict__.get('_kv_control_nodes')
        entries = widget.__dict__.get('_kv_entries')
        slots = widget.__dict__.get('_kv_slots')
        stale = []
        if nodes:
            stale += [n for n in nodes if n.owner_rule is rule]
        if slots:
            stale += [e.node for e in slots.values()
                      if e.node is not None and e.node.owner_rule is rule]
        for node in stale:
            node.teardown()
            if nodes and node in nodes:
                nodes.remove(node)
            if entries and node in entries:
                entries.remove(node)
        scopes = widget.__dict__.get('_kv_id_scopes')
        if scopes:
            del scopes[:]

    def _build_canvas_content(self, group, widget, rule, ids, captured,
                              subnodes):
        '''Build the canvas rule `rule`'s children into `group` (explicit
        adds: no canvas context is active here), recording created bindings
        in `captured` and nested control nodes in `subnodes`.'''
        global Instruction, InstructionGroup
        if Instruction is None:
            Instruction = Factory.get('Instruction')
        for crule in rule.children:
            if isinstance(crule, ParserControlRule):
                if InstructionGroup is None:
                    from kivy.graphics import InstructionGroup
                sub = InstructionGroup()
                group.add(sub)
                node_cls = (CanvasIfNode if crule.kind == 'if'
                            else CanvasForNode)
                node = node_cls(self, widget, crule, ids, sub)
                subnodes.append(node)
                node.activate()
                continue
            if crule.name == 'Clear':
                group.clear()
                continue
            instr = Factory.get(crule.name)()
            if not isinstance(instr, Instruction):
                raise BuilderException(
                    crule.ctx, crule.line,
                    'You can add only graphics Instruction in canvas.')
            group.add(instr)
            try:
                for prule in crule.properties.values():
                    key = prule.name
                    value = prule.co_value
                    if type(value) is CodeType:
                        blist = _handlers[widget.uid][key]
                        n = len(blist)
                        value, _ = create_handler(
                            widget, instr.proxy_ref, key, value, prule,
                            ids, True)
                        if len(blist) > n:
                            captured.append((key, blist[n:]))
                    setattr(instr, key, value)
            except BuilderException:
                raise
            except Exception as e:
                tb = sys.exc_info()[2]
                raise BuilderException(
                    prule.ctx, prule.line,
                    '{}: {}'.format(e.__class__.__name__, e), cause=tb)

    def match(self, widget):
        '''Return a list of :class:`ParserRule` objects matching the widget.
        '''
        cache = self._match_cache
        k = (widget.__class__, tuple(widget.cls))
        if k in cache:
            return cache[k]
        rules = []
        for selector, rule in self.rules:
            if selector.match(widget):
                if rule.avoid_previous_rules:
                    del rules[:]
                rules.append(rule)
        cache[k] = rules
        return rules

    def match_rule_name(self, rule_name):
        '''Return a list of :class:`ParserRule` objects matching the widget.
        '''
        cache = self._match_name_cache
        rule_name = str(rule_name)
        k = rule_name.lower()
        if k in cache:
            return cache[k]
        rules = []
        for selector, rule in self.rules:
            if selector.match_rule_name(rule_name):
                if rule.avoid_previous_rules:
                    del rules[:]
                rules.append(rule)
        cache[k] = rules
        return rules

    def sync(self):
        '''Execute all the waiting operations, such as the execution of all the
        expressions related to the canvas.

        .. versionadded:: 1.7.0
        '''
        global _delayed_start
        next_args = _delayed_start
        if next_args is None:
            return

        while next_args is not StopIteration:
            # is this try/except still needed? yes, in case widget died in this
            # frame after the call was scheduled
            try:
                call_fn(next_args[:-1], None, None)
            except ReferenceError:
                pass
            args = next_args
            next_args = args[-1]
            args[-1] = None
        _delayed_start = None

    def unbind_widget(self, uid):
        '''Unbind all the handlers created by the KV rules of the
        widget. The :attr:`kivy.uix.widget.Widget.uid` is passed here
        instead of the widget itself, because Builder is using it in the
        widget destructor.

        This effectively clears all the KV rules associated with this widget.
        For example:

        .. code-block:: python-console

            >>> w = Builder.load_string(\'''
            ... Widget:
            ...     height: self.width / 2. if self.disabled else self.width
            ...     x: self.y + 50
            ... \''')
            >>> w.size
            [100, 100]
            >>> w.pos
            [50, 0]
            >>> w.width = 500
            >>> w.size
            [500, 500]
            >>> Builder.unbind_widget(w.uid)
            >>> w.width = 222
            >>> w.y = 500
            >>> w.size
            [222, 500]
            >>> w.pos
            [50, 500]

        .. versionadded:: 1.7.2
        '''
        if uid not in _handlers:
            return
        for prop_callbacks in _handlers[uid].values():
            for callbacks in prop_callbacks:
                for f, k, fn, bound_uid in callbacks:
                    if fn is None:  # it's not a kivy prop.
                        continue
                    try:
                        f.unbind_uid(k, bound_uid)
                    except ReferenceError:
                        # proxy widget is already gone, that's cool :)
                        pass
        del _handlers[uid]

    def unbind_property(self, widget, name):
        '''Unbind the handlers created by all the rules of the widget that set
        the name.

        This effectively clears all the rules of widget that take the form::

            name: rule

        For example:

        .. code-block:: python-console

            >>> w = Builder.load_string(\'''
            ... Widget:
            ...     height: self.width / 2. if self.disabled else self.width
            ...     x: self.y + 50
            ... \''')
            >>> w.size
            [100, 100]
            >>> w.pos
            [50, 0]
            >>> w.width = 500
            >>> w.size
            [500, 500]
            >>> Builder.unbind_property(w, 'height')
            >>> w.width = 222
            >>> w.size
            [222, 500]
            >>> w.y = 500
            >>> w.pos
            [550, 500]

        .. versionadded:: 1.9.1
        '''
        uid = widget.uid
        if uid not in _handlers:
            return

        prop_handlers = _handlers[uid]
        if name not in prop_handlers:
            return

        for callbacks in prop_handlers[name]:
            for f, k, fn, bound_uid in callbacks:
                if fn is None:  # it's not a kivy prop.
                    continue
                try:
                    f.unbind_uid(k, bound_uid)
                except ReferenceError:
                    # proxy widget is already gone, that's cool :)
                    pass
        del prop_handlers[name]
        if not prop_handlers:
            del _handlers[uid]

    def _build_canvas(self, canvas, widget, rule, rootrule):
        global Instruction, InstructionGroup
        if Instruction is None:
            Instruction = Factory.get('Instruction')
        idmap = copy(self.rulectx[rootrule]['ids'])
        for crule in rule.children:
            if isinstance(crule, ParserControlRule):
                # created inside the canvas `with` block, so the group is
                # auto-added at the block's document position; the content is
                # built in the deferred phase, outside the canvas context
                if InstructionGroup is None:
                    from kivy.graphics import InstructionGroup
                group = InstructionGroup()
                node_cls = (CanvasIfNode if crule.kind == 'if'
                            else CanvasForNode)
                node = node_cls(self, widget, crule, idmap, group)
                node.owner_rule = rootrule
                widget.__dict__.setdefault(
                    '_kv_control_nodes', []).append(node)
                self._pending.append(partial(node.activate, None))
                continue
            name = crule.name
            if name == 'Clear':
                canvas.clear()
                continue
            instr = Factory.get(name)()
            if not isinstance(instr, Instruction):
                raise BuilderException(
                    crule.ctx, crule.line,
                    'You can add only graphics Instruction in canvas.')
            try:
                for prule in crule.properties.values():
                    key = prule.name
                    value = prule.co_value
                    if type(value) is CodeType:
                        value, _ = create_handler(
                            widget, instr.proxy_ref,
                            key, value, prule, idmap, True)
                    setattr(instr, key, value)
            except Exception as e:
                tb = sys.exc_info()[2]
                raise BuilderException(
                    prule.ctx, prule.line,
                    '{}: {}'.format(e.__class__.__name__, e), cause=tb)


#: Main instance of a :class:`BuilderBase`.
Builder: BuilderBase = register_context('Builder', BuilderBase)
Builder.load_file(join(kivy_data_dir, 'style.kv'), rulesonly=True)

if 'KIVY_PROFILE_LANG' in environ:
    import atexit
    from html import escape

    def match_rule(fn, index, rule):
        if rule.ctx.filename != fn:
            return
        for prop, prp in rule.properties.items():
            if prp.line != index:
                continue
            yield prp
        if isinstance(rule, ParserControlRule):
            for prp in (rule.selector_prop, rule.iterator_prop,
                        rule.key_prop, rule.class_prop):
                if prp is not None and prp.line == index:
                    yield prp
            for _, prp in rule.locals:
                if prp.line == index:
                    yield prp
            for branch in rule.branches:
                for r in match_rule(fn, index, branch):
                    yield r
        for child in rule.children:
            for r in match_rule(fn, index, child):
                yield r
        if rule.canvas_root:
            for r in match_rule(fn, index, rule.canvas_root):
                yield r
        if rule.canvas_before:
            for r in match_rule(fn, index, rule.canvas_before):
                yield r
        if rule.canvas_after:
            for r in match_rule(fn, index, rule.canvas_after):
                yield r

    def dump_builder_stats():
        html = [
            '<!doctype html>'
            '<html><body>',
            '<style type="text/css">\n',
            'pre { margin: 0; }\n',
            '</style>']
        files = {x[1].ctx.filename for x in Builder.rules}
        for fn in files:
            try:
                with open(fn) as f:
                    lines = f.readlines()
            except (IOError, TypeError) as e:
                continue
            html += ['<h2>', fn, '</h2>', '<table>']
            count = 0
            for index, line in enumerate(lines):
                line = line.rstrip()
                line = escape(line)
                matched_prp = []
                for psn, rule in Builder.rules:
                    matched_prp.extend(match_rule(fn, index, rule))

                count = sum({x.count for x in matched_prp})

                color = (255, 155, 155) if count else (255, 255, 255)
                html += ['<tr style="background-color: rgb{}">'.format(color),
                         '<td>', str(index + 1), '</td>',
                         '<td>', str(count), '</td>',
                         '<td><pre>', line, '</pre></td>',
                         '</tr>']
            html += ['</table>']
        html += ['</body></html>']
        with open('builder_stats.html', 'w', encoding='utf-8') as fd:
            fd.write(''.join(html))

        print('Profiling written at builder_stats.html')

    atexit.register(dump_builder_stats)
