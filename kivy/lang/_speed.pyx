
from cpython.dict cimport PyDict_Update
from kivy._event cimport EventDispatcher, Observable
from kivy.properties cimport Property
import sys
import types
from collections import defaultdict
from functools import partial

# class types to check with isinstance
from kivy.compat import PY2
if PY2:
    _cls_type = (type, types.ClassType)
else:
    _cls_type = (type, )

cdef tuple cls_observable = (EventDispatcher, Observable)

_handlers = {}
global_idmap = {}
_delayed_start = None


def update_intermediates(base, keys, bound, s, fn, args, instance, value):
    ''' Function that is called when an intermediate property is updated
    and `rebind` of that property is True. In that case, we unbind
    all bound funcs that were bound to attrs of the old value of the
    property and rebind to the new value of the property.

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
        if isinstance(f, cls_observable):
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
    if isinstance(f, cls_observable):
        uid = f.fbind(keys[-1], fn, args)
        if uid:
            append([f.proxy_ref, keys[-1], fn, uid])
    # when we rebind we have to update the
    # rule with the most recent value, otherwise, the value might be wrong
    # and wouldn't be updated since we might not have tracked it before.
    # This only happens for a callback when rebind was True for the prop.
    fn(args, None, None)


def call_fn(args, instance, v):
    element, key, value, rule, idmap = args
    rule.count += 1
    e_value = eval(value, idmap)
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


def create_handler(iself, element, key, value, rule, dict idmap, delayed=False):
    cdef:
        dict _handlers_uids
        list bound_list
        list bound
        int was_bound, k
        Property prop
        list keys
        object val

    idmap = idmap.copy()
    PyDict_Update(idmap, global_idmap)
    idmap['self'] = iself.proxy_ref

    if iself.uid not in _handlers:
        _handlers_uids = _handlers[iself.uid] = {}
    else:
        _handlers_uids = _handlers[iself.uid]

    if key not in _handlers_uids:
        bound_list = _handlers_uids[key] = []
    else:
        bound_list = _handlers_uids[key]

    # we need a hash for when delayed, so we don't execute duplicate canvas
    # callbacks from the same handler during a sync op
    if delayed:
        fn = delayed_call_fn
        args = [element, key, value, rule, idmap, None]  # see _delayed_start
    else:
        fn = call_fn
        args = (element, key, value, rule, idmap)

    # bind every key.value
    cdef list watched_keys = rule.watched_keys
    if watched_keys is not None:
        for keys in watched_keys:
            base = idmap.get(keys[0])
            if base is None:
                continue
            f = base = getattr(base, 'proxy_ref', base)
            bound = []
            was_bound = 0

            # bind all attrs, except last to update_intermediates
            k = 1
            for val in keys[1:-1]:
                # if we need to dynamically rebind, bindm otherwise
                # just add the attr to the list
                if isinstance(f, cls_observable):
                    prop = f.property(val, True)
                    if prop is not None and prop.rebind:
                        # fbind should not dispatch, otherwise
                        # update_intermediates might be called in the middle
                        # here messing things up
                        uid = f.fbind(
                            val, update_intermediates, base, keys, bound, k,
                            fn, args)
                        bound.append([f.proxy_ref, val, update_intermediates, uid])
                        was_bound = 1
                    else:
                        bound.append([f.proxy_ref, val, None, None])
                elif not isinstance(f, _cls_type):
                    bound.append([getattr(f, 'proxy_ref', f), val, None, None])
                else:
                    bound.append([f, val, None, None])
                f = getattr(f, val, None)
                if f is None:
                    break
                k += 1

            # for the last attr we bind directly to the setting
            # function, because that attr sets the value of the rule.
            if isinstance(f, cls_observable):
                uid = f.fbind(keys[-1], fn, args)  # f is not None
                if uid:
                    bound.append([f.proxy_ref, keys[-1], fn, uid])
                    was_bound = 1
            if was_bound:
                bound_list.append(bound)

    try:
        return eval(value, idmap), bound_list
    except Exception as e:
        tb = sys.exc_info()[2]
        from kivy.lang import BuilderException
        raise BuilderException(rule.ctx, rule.line,
                               '{}: {}'.format(e.__class__.__name__, e),
                               cause=tb)
