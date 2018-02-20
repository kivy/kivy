import unittest
from kivy.factory import Factory as F


def historylogger(instance, value):
    if not hasattr(instance, '_history'):
        instance._history = [None]
    instance._history.append(value)


def counter(instance, value):
    if not hasattr(instance, '_counter'):
        instance._counter = 0
    instance._counter += 1


class CountWidget(F.Widget):
    def on_parent(self, *largs):
        counter(self, None)


class SwapWidgetTestCase(unittest.TestCase):
    def test_external_callback(self):
        p1, p2 = F.Widget(), F.Widget()
        p1.bind(children=counter)
        p2.bind(children=counter)
        c1, c2 = F.Widget(), F.Widget()
        c1.bind(parent=counter)
        c2.bind(parent=counter)
        self._simple_test(p1, p2, c1, c2)

    def test_method_callback(self):
        p1, p2 = F.Widget(), F.Widget()
        p1.bind(children=counter)
        p2.bind(children=counter)
        c1, c2 = CountWidget(), CountWidget()
        self._simple_test(p1, p2, c1, c2)

    def _simple_test(self, parent1, parent2, child1, child2):
        parent1.add_widget(child1)  # p1++, c1++
        self.assertEqual(child1._counter, 1)
        self.assertEqual(parent1._counter, 1)
        parent1.remove_widget(child1)  # p1++, c1++
        self.assertEqual(child1._counter, 2)
        self.assertEqual(parent1._counter, 2)

        parent1.add_widget(child1)  # p1++, c1++
        self.assertEqual(child1._counter, 3)
        self.assertEqual(parent1._counter, 3)

        parent2.add_widget(child2)  # p2++, c2++
        self.assertEqual(child2._counter, 1)
        self.assertEqual(parent2._counter, 1)

        parent1.swap_widget(child1, child2)  # p1+=2, p2+=2, c1++, c2++
        self.assertEqual(child1._counter, 4)
        self.assertEqual(child2._counter, 2)
        self.assertEqual(parent1._counter, 5)
        self.assertEqual(parent2._counter, 3)

        self.assertIs(child1.parent, parent2)
        self.assertIs(child2.parent, parent1)
        self.assertEqual(child1._counter, 4)
        self.assertEqual(child2._counter, 2)

    def test_swap_widget_extern(self):
        self._mimick = mimick = {}  # mimicks callback order per child
        parents = [F.BoxLayout(), F.FloatLayout(), F.GridLayout(cols=2),
                   F.PageLayout(), F.RelativeLayout(), F.StackLayout(),
                   F.Widget()]
        n = 17  # children per parent
        for parent in parents:
            parent.bind(children=counter)
            mimick[parent] = 0
            for _ in range(n):
                wid = F.Widget()
                wid.bind(parent=historylogger)
                mimick[parent] += 1
                mimick[wid] = [None, parent]
                parent.add_widget(wid)
            self.assertEqual(n, len(parent.children))
            for wid in parent.children:
                self.assertListEqual(wid._history, [None, parent])

        for idx in range(len(parents) * 4):
            a_idx = idx % len(parents)
            b_idx = (idx + 1) % len(parents)
            a = parents[a_idx]
            b = parents[b_idx]
            self._swap_test(a, b)

        for parent in parents:
            self.assertEqual(parent._counter, mimick[parent])
            for child in parent.children:
                mimick[parent] += 1
                mimick[child].append(None)
                parent.remove_widget(child)
                self.assertListEqual(child._history, mimick[child])
                self.assertEqual(parent._counter, mimick[parent])
                self.assertIs(child.parent, None)
                self.assertFalse(child in parent.children)

    def _swap_test(self, a, b):
        self.assertEqual(len(a.children), len(b.children))
        mimick = self._mimick
        old_a_children = a.children[:]
        old_b_children = b.children[:]
        for x in reversed(range(len(a.children))):
            child_a, child_b = a.children[x], b.children[x]
            mimick[a] += 2
            mimick[b] += 2
            mimick[child_a].append(b)
            mimick[child_b].append(a)
            a.swap_widget(child_a, child_b)
            self.assertIs(child_a.parent, b)
            self.assertIs(child_b.parent, a)
        # now swapped 1:1 in a/b
        self.assertListEqual(old_a_children, b.children)
        self.assertListEqual(old_b_children, a.children)
        for wid in old_a_children:
            self.assertIs(wid.parent, b)
            self.assertFalse(wid in a.children)
            self.assertListEqual(wid._history[-2:], [a, b])
            self.assertListEqual(wid._history, mimick[wid])
        for wid in old_b_children:
            self.assertIs(wid.parent, a)
            self.assertFalse(wid in b.children)
            self.assertListEqual(wid._history[-2:], [b, a])
            self.assertListEqual(wid._history, mimick[wid])


if __name__ == '__main__':
    unittest.main()
