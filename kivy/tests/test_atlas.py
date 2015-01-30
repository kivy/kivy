'''
Atlas tests
===========
'''

import unittest
import os

import kivy.atlas as a

class AtlasTestCase(unittest.TestCase):

    def test_usage(self):
        self.assertIn('Usage', a.run([]))
        self.assertIn('Usage', a.run(['arg1', 'arg2']))
        msg = a.run("--use-path --use-path --use-path --use-path".split())
        self.assertIn('Usage', msg)

    def test_options(self):
        msg = a.run("--foo outfile 1000x1000 x.png y.png".split())
        self.assertIn('Unknown option', msg)
        msg = a.run("--use-path --padding=x outfile 1000 x.png y.png".split())
        self.assertIn('padding', msg)
        msg = a.run("--use-path --padding=-100 outfile 1000 x.png y.png"
                    .split())
        self.assertIn('padding', msg)


    def test_size(self):
        msg = a.run('outfile SIZE x.png'.split())
        self.assertIn('size', msg)
        msg = a.run('outfile 0 x.png'.split())
        self.assertIn('size', msg)
        msg = a.run('outfile 0x0 x.png'.split())
        self.assertIn('size', msg)
        msg = a.run('outfile 0x10 x.png'.split())
        self.assertIn('size', msg)
        msg = a.run('outfile 10x0 x.png'.split())
        self.assertIn('size', msg)

    def test_missing_files(self):
        msg = a.run('outfile 100 missing_file.png'.split())
        self.assertIn('creating atlas', msg)

        # def test_dupicate_files--meta shouldn't break


        a.run('big.png 620 x.png x.png x.png'.split())




