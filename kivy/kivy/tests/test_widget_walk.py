import unittest


class FileWidgetWalk(unittest.TestCase):

    def test_walk_large_tree(self):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        ''' the tree
        BoxLayout
            BoxLayout
            Label
                10 labels
            BoxLayout
                10 labels
            BoxLayout
                Label
            Label
        '''

        root = BoxLayout()
        tree = [root]

        box = BoxLayout()
        tree.append(box)
        root.add_widget(box)

        label = Label()
        tree.append(label)
        root.add_widget(label)
        for i in range(10):
            tree.append(Label())
            label.add_widget(tree[-1])

        box = BoxLayout()
        tree.append(box)
        root.add_widget(box)
        for i in range(10):
            tree.append(Label())
            box.add_widget(tree[-1])

        box = BoxLayout()
        tree.append(box)
        root.add_widget(box)
        tree.append(Label())
        box.add_widget(tree[-1])

        label = Label()
        tree.append(label)
        root.add_widget(label)

        def rotate(l, n):
            return l[n:] + l[:n]

        for i in range(len(tree)):
            rotated = rotate(tree, i)   # shift list to start at i
            # walk starting with i
            walked = [n for n in tree[i].walk(loopback=True)]
            walked_reversed = [n for n in tree[i].walk_reverse(loopback=True)]

            self.assertListEqual(rotated, walked)
            self.assertListEqual(walked, list(reversed(walked_reversed)))

    def test_walk_single(self):
        from kivy.uix.label import Label

        label = Label()
        self.assertListEqual([n for n in label.walk(loopback=True)], [label])
        self.assertListEqual([n for n in label.walk_reverse(loopback=True)],
                             [label])
