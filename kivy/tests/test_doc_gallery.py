import unittest
from doc.gallery import *
import time
import os

class Test_write_duplicates(unittest.TestCase):
    def safe_remove(self, filename):
        try:
            os.unlink(filename)
        except OSError:
            pass

    def setUp(self):
        self.safe_remove('gallery1.txt')
        self.safe_remove('gallery2.txt')

    def tearDown(self):
        self.safe_remove('gallery1.txt')
        self.safe_remove('gallery2.txt')

    def test_write_duplicates(self):
        start_time = time.time()
        def is_new(filename):
            mod_time = os.path.getmtime(filename)
            return mod_time - start_time > 1.0
        s = "This is a\nmultiline file."
        write_file('gallery1.txt', s)
        time.sleep(2)  # yes, slows down running tests.  Can't be helped.
        write_file('gallery1.txt', s)
        assert not is_new('gallery1.txt'), 'Should ignore exact rewrite'
        write_file('gallery2.txt', s)
        assert is_new('gallery2.txt'), 'Should write new file'
        write_file('gallery1.txt', 'Something different')
        assert is_new('gallery1.txt'), 'Should write new content'


class Test_parse_docstring_info(unittest.TestCase):

    def test_parse_docstring_info(self):
        assert 'error' in parse_docstring_info("No Docstring")
        assert 'error' in parse_docstring_info("'''No Docstring Title'''")
        assert 'error' in parse_docstring_info("'''No Sentence\n======\nPeriods'''")
        assert 'error' in parse_docstring_info(
            "'\nSingle Quotes\n===\n\nNo singles.'")

        d = parse_docstring_info("""'''
3D Rendering Monkey Head
========================

This example demonstrates using OpenGL to display a
rotating monkey head. This
includes loading a Blender OBJ file, shaders written in OpenGL's Shading
Language (GLSL), and using scheduled callbacks.

The file monkey.obj is a OBJ file output form the Blender free 3D creation
software. The file is text, listing vertices and faces. It is loaded
into a scene using objloader.py's ObjFile class. The file simple.glsl is
a simple vertex and fragment shader written in GLSL.
'''
blah blah
blah blah
    """)
        assert 'error' not in d
        assert '3D Rendering' in d['docstring'] and 'This example' in d['docstring']
        assert '3D Rendering' in d['title']
        assert 'monkey head' in d['first_sentence']

