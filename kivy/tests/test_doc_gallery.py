from doc.gallery import *


def test_parse_docstring_info():
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

if __name__ == '__main__':
    test_parse_docstring_info()
