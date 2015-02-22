'''CSS-like Rule Selectors
=======================

The Kivy language allows you to write rules that may be selected depending
on context.  These rules use a very small subset of CSS3 selectors.  For
example::

    <<A B.p1.p2 > C *#i3>>:
        ...

Such a rule applies to any (`*`) widget with `id=i3`, that is a descendant of a
widget whose Python class inherits from `C`, which itself is an immediate child
of a widget whose python class inherits from `B` and whose `cls` property has
elements `p1`and `p2`, and which itself is a descendant of a widget whose Python
class inherits from `A`.

Caveats
-------

Since widgets, created from kv-lang specifications, get their properties very
late (too late for rule selection), class selectors and id selectors also
consult the information stored in the rule responsible for creatng the widget.
If that information can be evaluated statically, then it can influence rule
selection (presence of an `id` or `cls` property).
'''
import re

SELECTOR_ID = "#."
SELECTOR_OP = ">*"
SELECTOR_CHARS = SELECTOR_ID + SELECTOR_OP
RE_SELECTOR = re.compile(r"([%s]|\w[\w_-]*)\s*" % SELECTOR_CHARS)

def parse_css_selector(s):
    pos = 0
    tokens = []
    for m in RE_SELECTOR.finditer(s):
        if m.start() != pos:
            raise Exception("in selector <%s> unexpected: %s" % (s, s[pos:m.start()]))
        pos = m.end()
        tok = m.group(1)
        tokens.append(m.group(1))
    if pos != len(s):
        raise Exception("in selector <%s> unexpected: %s" % (s, s[pos:]))

    selectors = []
    element_selector = None
    immediate_precedence = False
    new_element_selector = None
    new_filter_selector = None

    i = 0
    imax = len(tokens)

    while i < imax:
        tokA = tokens[i]
        i += 1
        
        if tokA == "*":
            new_element_selector = AnySelector()
        elif tokA == "#":
            if i >= imax:
                raise Exception("in selector <%s>, missing ID after `#'" % s)
            name = tokens[i]
            i += 1
            new_filter_selector = IdSelector(name)
        elif tokA == ".":
            if i >= imax:
                raise Exception("in selector <%s>, missing ID after `.'" % s)
            name = tokens[i]
            i += 1
            new_filter_selector = ClassSelector(name)
        elif tokA == ">":
            if immediate_precedence:
                raise Exception("in selector <%s>, two > in a row" % s)
            immediate_precedence = True
            element_selector = None
            continue
        else:
            new_element_selector = NameSelector(tokA)

        if new_filter_selector:
            if not element_selector:
                element_selector = new_element_selector = AnySelector()
            element_selector.add_filter(new_filter_selector)
            new_filter_selector = None

        if new_element_selector:
            if immediate_precedence:
                immediate_precedence = False
                if selectors:
                    selectors.append(NextSelector())
            elif selectors:
                selectors.append(SkipSelector())
            selectors.append(new_element_selector)
            element_selector = new_element_selector
            new_element_selector = None

    # build the chain of continuations
    head = tail = selectors.pop()
    while selectors:
        curr = selectors.pop()
        tail._next = curr
        tail = curr

    return head


class SelectorBase(object):

    def __init__(self):
        self._next = None

    def match_next(self, ctx, i):
        n = self._next
        return not n or n.match(ctx, i)


class ElementSelectorBase(SelectorBase):

    css_selector = True

    def __init__(self):
        super(ElementSelectorBase, self).__init__()
        self.filters = []

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<%s %s%s -> %s>" % (type(self).__name__, str(self), "".join(map(str,self.filters)), 
                                    repr(self._next) if self._next else "ACCEPT")

    def add_filter(self, filter):
        self.filters.append(filter)

    def match_next(self, ctx, i):
        elt = ctx[i]
        for f in self.filters:
            if not f.match(elt):
                return False
        return super(ElementSelectorBase, self).match_next(ctx, i)


class AnySelector(ElementSelectorBase):

    name = "*"

    def match(self, ctx, i):
        return self.match_next(ctx, i)


class NameSelector(ElementSelectorBase):

    def __init__(self, name):
        super(NameSelector, self).__init__()
        self.name = name

    def match(self, ctx, i):
        elt = ctx[i]
        classes = type(elt.widget).__mro__
        name = self.name
        for c in classes:
            if c.__name__ == name:
                return self.match_next(ctx, i)
            elif c.__name__ == "Widget":
                break
        return False


class FilterSelectorBase(object):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "%s%s" % (self.op, self.name)

    def __repr__(self):
        return "<%s %s>" % (type(self).__name__, str(self))


class ClassSelector(FilterSelectorBase):

    op = "."

    def match(self, elt):
        return self.name in elt.cls


class IdSelector(FilterSelectorBase):

    op = "#"

    def match(self, elt):
        return self.name == elt.id


class PrecedenceSelector(SelectorBase):

    def __repr__(self):
        return "<%s -> %s>" % (type(self).__name__, repr(self._next) if self._next else "ACCEPT")
    

class SkipSelector(PrecedenceSelector):

    def __str__(self):
        return ">"

    def match(self, ctx, i):
        # match using backtracking.
        # we could also compile into a DFA, but would that be worth it?
        while i > 0:
            i -= 1
            if self.match_next(ctx, i):
                return True
        return False


class NextSelector(PrecedenceSelector):

    def __str__(self):
        return " "

    def match(self, ctx, i):
        return i > 0 and self.match_next(ctx, i-1)
