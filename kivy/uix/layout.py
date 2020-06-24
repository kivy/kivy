'''
Layout
======

Layouts are used to calculate and assign widget positions.

The :class:`Layout` class itself cannot be used directly.
You should use one of the following layout classes:

- Anchor layout: :class:`kivy.uix.anchorlayout.AnchorLayout`
- Box layout: :class:`kivy.uix.boxlayout.BoxLayout`
- Float layout: :class:`kivy.uix.floatlayout.FloatLayout`
- Grid layout: :class:`kivy.uix.gridlayout.GridLayout`
- Page Layout: :class:`kivy.uix.pagelayout.PageLayout`
- Relative layout: :class:`kivy.uix.relativelayout.RelativeLayout`
- Scatter layout: :class:`kivy.uix.scatterlayout.ScatterLayout`
- Stack layout: :class:`kivy.uix.stacklayout.StackLayout`


Understanding the `size_hint` Property in `Widget`
--------------------------------------------------

The :attr:`~kivy.uix.Widget.size_hint` is a tuple of values used by
layouts to manage the sizes of their children. It indicates the size
relative to the layout's size instead of an absolute size (in
pixels/points/cm/etc). The format is::

    widget.size_hint = (width_proportion, height_proportion)

The proportions are specified as floating point numbers in the range 0-1. For
example, 0.5 represents 50%, 1 represents 100%.

If you want a widget's width to be half of the parent's width and the
height to be identical to the parent's height, you would do::

    widget.size_hint = (0.5, 1.0)

If you don't want to use a size_hint for either the width or height, set the
value to None. For example, to make a widget that is 250px wide and 30%
of the parent's height, do::

    widget.size_hint = (None, 0.3)
    widget.width = 250

Being :class:`Kivy properties <kivy.properties>`, these can also be set via
constructor arguments::

    widget = Widget(size_hint=(None, 0.3), width=250)

.. versionchanged:: 1.4.1
    The `reposition_child` internal method (made public by mistake) has
    been removed.

'''

__all__ = ('Layout', )

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.compat import isclose


class Layout(Widget):
    '''Layout interface class, used to implement every layout. See module
    documentation for more information.
    '''

    _trigger_layout = None

    def __init__(self, **kwargs):
        if self.__class__ == Layout:
            raise Exception('The Layout class is abstract and \
                cannot be used directly.')
        if self._trigger_layout is None:
            self._trigger_layout = Clock.create_trigger(self.do_layout, -1)
        super(Layout, self).__init__(**kwargs)

    def do_layout(self, *largs):
        '''This function is called when a layout is called by a trigger.
        If you are writing a new Layout subclass, don't call this function
        directly but use :meth:`_trigger_layout` instead.

        The function is by default called *before* the next frame, therefore
        the layout isn't updated immediately. Anything depending on the
        positions of e.g. children should be scheduled for the next frame.

        .. versionadded:: 1.0.8
        '''
        raise NotImplementedError('Must be implemented in subclasses.')

    def add_widget(self, widget, index=0, canvas=None):
        fbind = widget.fbind
        fbind('size', self._trigger_layout)
        fbind('size_hint', self._trigger_layout)
        fbind('size_hint_max', self._trigger_layout)
        fbind('size_hint_min', self._trigger_layout)
        return super(Layout, self).add_widget(widget, index, canvas)

    def remove_widget(self, widget):
        funbind = widget.funbind
        funbind('size', self._trigger_layout)
        funbind('size_hint', self._trigger_layout)
        funbind('size_hint_max', self._trigger_layout)
        funbind('size_hint_min', self._trigger_layout)
        return super(Layout, self).remove_widget(widget)

    def layout_hint_with_bounds(
            self, sh_sum, available_space, min_bounded_size, sh_min_vals,
            sh_max_vals, hint):
        '''(internal) Computes the appropriate (size) hint for all the
        widgets given (potential) min or max bounds on the widgets' size.
        The ``hint`` list is updated with appropriate sizes.

        It walks through the hints and for any widgets whose hint will result
        in violating min or max constraints, it fixes the hint. Any remaining
        or missing space after all the widgets are fixed get distributed
        to the widgets making them smaller or larger according to their
        size hint.

        This algorithms knows nothing about the widgets other than what is
        passed through the input params, so it's fairly generic for laying
        things out according to constraints using size hints.

        :Parameters:

            `sh_sum`: float
                The sum of the size hints (basically ``sum(size_hint)``).
            `available_space`: float
                The amount of pixels available for all the widgets
                whose size hint is not None. Cannot be zero.
            `min_bounded_size`: float
                The minimum amount of space required according to the
                `size_hint_min` of the widgets (basically
                ``sum(size_hint_min)``).
            `sh_min_vals`: list or iterable
                Items in the iterable are the size_hint_min for each widget.
                Can be None. The length should be the same as ``hint``
            `sh_max_vals`: list or iterable
                Items in the iterable are the size_hint_max for each widget.
                Can be None. The length should be the same as ``hint``
            `hint`: list
                A list whose size is the same as the length of ``sh_min_vals``
                and ``sh_min_vals`` whose each element is the corresponding
                size hint value of that element. This list is updated in place
                with correct size hints that ensure the constraints are not
                violated.

        :returns:
            Nothing. ``hint`` is updated in place.
        '''
        if not sh_sum:
            return
        # TODO: test when children have size_hint, max/min of zero

        # all divs are float denominator ;)
        stretch_ratio = sh_sum / float(available_space)
        if available_space <= min_bounded_size or \
                isclose(available_space, min_bounded_size):
            # too small, just set to min
            for i, (sh, sh_min) in enumerate(zip(hint, sh_min_vals)):
                if sh is None:
                    continue

                if sh_min is not None:
                    hint[i] = sh_min * stretch_ratio  # set to min size
                else:
                    hint[i] = 0.  # everything else is zero
            return

        # these dicts take i (widget child) as key
        not_mined_contrib = {}  # all who's sh > min_sh or had no min_sh
        not_maxed_contrib = {}  # all who's sh < max_sh or had no max_sh
        sh_mins_avail = {}  # the sh amt removable until we hit sh_min
        sh_maxs_avail = {}  # the sh amt addable until we hit sh_max
        oversize_amt = undersize_amt = 0
        hint_orig = hint[:]

        # first, for all the items, set them to be within their max/min
        # size_hint bound, also find how much their size_hint can be reduced
        # or increased
        for i, (sh, sh_min, sh_max) in enumerate(
                zip(hint, sh_min_vals, sh_max_vals)):
            if sh is None:
                continue

            diff = 0

            if sh_min is not None:
                sh_min *= stretch_ratio
                diff = sh_min - sh  # how much we are under the min

                if diff > 0:
                    hint[i] = sh_min
                    undersize_amt += diff
                else:
                    not_mined_contrib[i] = None

                sh_mins_avail[i] = hint[i] - sh_min
            else:
                not_mined_contrib[i] = None
                sh_mins_avail[i] = hint[i]

            if sh_max is not None:
                sh_max *= stretch_ratio
                diff = sh - sh_max

                if diff > 0:
                    hint[i] = sh_max  # how much we are over the max
                    oversize_amt += diff
                else:
                    not_maxed_contrib[i] = None

                sh_maxs_avail[i] = sh_max - hint[i]
            else:
                not_maxed_contrib[i] = None
                sh_maxs_avail[i] = sh_sum - hint[i]

            if i in not_mined_contrib:
                not_mined_contrib[i] = max(0., diff)  # how much got removed
            if i in not_maxed_contrib:
                not_maxed_contrib[i] = max(0., diff)  # how much got added

        # if margin is zero, the amount of the widgets that were made smaller
        # magically equals the amount of the widgets that were made larger
        # so we're all good
        margin = oversize_amt - undersize_amt
        if isclose(oversize_amt, undersize_amt, abs_tol=1e-15):
            return

        # we need to redistribute the margin among all widgets
        # if margin is positive, then we have extra space because the widgets
        # that were larger and were reduced contributed more, so increase
        # the size hint for those that are allowed to be larger by the
        # most allowed, proportionately to their size (or inverse size hint).
        # similarly for the opposite case
        if margin > 1e-15:
            contrib_amt = not_maxed_contrib
            sh_available = sh_maxs_avail
            mult = 1.
            contrib_proportion = hint_orig
        elif margin < -1e-15:
            margin *= -1.
            contrib_amt = not_mined_contrib
            sh_available = sh_mins_avail
            mult = -1.

            # when reducing the size of widgets proportionately, those with
            # larger sh get reduced less, and those with smaller, more.
            mn = min((h for h in hint_orig if h))
            mx = max((h for h in hint_orig if h is not None))
            hint_top = (2. * mn if mn else 1.) if mn == mx else mn + mx
            contrib_proportion = [None if h is None else hint_top - h for
                          h in hint_orig]

        # contrib_amt is all the widgets that are not their max/min and
        # can afford to be made bigger/smaller
        # We only use the contrib_amt indices from now on
        contrib_prop_sum = float(
            sum((contrib_proportion[i] for i in contrib_amt)))

        if contrib_prop_sum < 1e-9:
            assert mult == 1.  # should only happen when all sh are zero
            return

        contrib_height = {
            i: val / (contrib_proportion[i] / contrib_prop_sum) for
            i, val in contrib_amt.items()}
        items = sorted(
            (i for i in contrib_amt),
            key=lambda x: contrib_height[x])

        j = items[0]
        sum_i_contributed = contrib_amt[j]
        last_height = contrib_height[j]
        sh_available_i = {j: sh_available[j]}
        contrib_prop_sum_i = contrib_proportion[j]

        n = len(items)  # check when n <= 1
        i = 1
        if 1 < n:
            j = items[1]
            curr_height = contrib_height[j]

        done = False
        while not done and i < n:
            while i < n and last_height == curr_height:
                j = items[i]
                sum_i_contributed += contrib_amt[j]
                contrib_prop_sum_i += contrib_proportion[j]
                sh_available_i[j] = sh_available[j]
                curr_height = contrib_height[j]
                i += 1
            last_height = curr_height

            while not done:
                margin_height = ((margin + sum_i_contributed) /
                                 (contrib_prop_sum_i / contrib_prop_sum))
                if margin_height - curr_height > 1e-9 and i < n:
                    break

                done = True
                for k, available_sh in list(sh_available_i.items()):
                    if margin_height - available_sh / (
                            contrib_proportion[k] / contrib_prop_sum) > 1e-9:
                        del sh_available_i[k]
                        sum_i_contributed -= contrib_amt[k]
                        contrib_prop_sum_i -= contrib_proportion[k]
                        margin -= available_sh
                        hint[k] += mult * available_sh
                        done = False

                if not sh_available_i:  # all were under the margin
                    break

        if sh_available_i:
            assert contrib_prop_sum_i and margin
            margin_height = ((margin + sum_i_contributed) /
                             (contrib_prop_sum_i / contrib_prop_sum))
            for i in sh_available_i:
                hint[i] += mult * (
                    margin_height * contrib_proportion[i] / contrib_prop_sum -
                    contrib_amt[i])
