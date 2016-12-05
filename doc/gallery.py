''' Create rst documentation of the examples directory.

This uses screenshots in the screenshots_dir
(currently doc/sources/images/examples) along with source code and files
in the examples/ directory to create rst files in the generation_dir
(doc/sources/examples) gallery.rst, index.rst, and gen__*.rst

'''


import os
import re
from os.path import sep
from os.path import join as slash  # just like that name better
from kivy.logger import Logger
import textwrap

base_dir = '..'  # from here to the kivy top
examples_dir = slash(base_dir, 'examples')
screenshots_dir = slash(base_dir, 'doc/sources/images/examples')
generation_dir = slash(base_dir, 'doc/sources/examples')

image_dir = "../images/examples/"  # relative to generation_dir
gallery_filename = slash(generation_dir, 'gallery.rst')


# Info is a dict built up from
# straight filename information, more from reading the docstring,
# and more from parsing the description text.  Errors are often
# shown by setting the key 'error' with the value being the error message.
#
# It doesn't quite meet the requirements for a class, but is a vocabulary
# word in this module.

def iter_filename_info(dir_name):
    """
    Yield info (dict) of each matching screenshot found walking the
    directory dir_name.  A matching screenshot uses double underscores to
    separate fields, i.e. path__to__filename__py.png as the screenshot for
    examples/path/to/filename.py.

    Files not ending with .png are ignored, others are either parsed or
    yield an error.

    Info fields 'dunder', 'dir', 'file', 'ext', 'source' if not 'error'
    """
    pattern = re.compile(r'^((.+)__(.+)__([^-]+))\.png')
    for t in os.walk(dir_name):
        for filename in t[2]:
            if filename.endswith('.png'):
                m = pattern.match(filename)
                if m is None:
                    yield {'error': 'png filename not following screenshot'
                                    ' pattern: {}'.format(filename)}
                else:
                    d = m.group(2).replace('__', sep)
                    yield {'dunder': m.group(1),
                           'dir': d,
                           'file': m.group(3),
                           'ext': m.group(4),
                           'source': slash(d, m.group(3) + '.' + m.group(4))
                           }


def parse_docstring_info(text):
    ''' parse docstring from text (normal string with '\n's) and return an info
    dict.  A docstring should the first triple quoted string, have a title
    followed by a line of equal signs, and then a description at
    least one sentence long.

    fields are 'docstring', 'title', and 'first_sentence' if not 'error'
    'first_sentence' is a single line without newlines.
    '''
    q = '\"\"\"|\'\'\''
    p = r'({})\s+([^\n]+)\s+\=+\s+(.*?)(\1)'.format(q)
    m = re.search(p, text, re.S)
    if m:
        comment = m.group(3).replace('\n', ' ')
        first_sentence = comment[:comment.find('.') + 1]
        return {'docstring': m.group(0), 'title': m.group(2),
                'description': m.group(3), 'first_sentence': first_sentence}
    else:
        return {'error': 'Did not find docstring with title at top of file.'}


def iter_docstring_info(dir_name):
    ''' Iterate over screenshots in directory, yield info from the file
     name and initial parse of the docstring.  Errors are logged, but
     files with errors are skipped.
    '''
    for file_info in iter_filename_info(dir_name):
        if 'error' in file_info:
            Logger.error(file_info['error'])
            continue
        source = slash(examples_dir, file_info['dir'],
                       file_info['file'] + '.' + file_info['ext'])
        if not os.path.exists(source):
            Logger.error('Screen shot references source code that does '
                         'not exist:  %s', source)
            continue
        with open(source) as f:
            text = f.read()
            docstring_info = parse_docstring_info(text)
            if 'error' in docstring_info:
                Logger.error(docstring_info['error'] + '  File: ' + source)
                continue  # don't want to show ugly entries
            else:
                file_info.update(docstring_info)
        yield file_info


def enhance_info_description(info, line_length=50):
    ''' Using the info['description'], add fields to info.

    info['files'] is the source filename and any filenames referenced by the
    magic words in the description, e.g. 'the file xxx.py' or
    'The image this.png'.  These are as written in the description, do
    not allow ../dir notation, and are relative to the source directory.

    info['enhanced_description'] is the description, as an array of
    paragraphs where each paragraph is an array of lines wrapped to width
    line_length.  This enhanced description include the rst links to
    the files of info['files'].
    '''

    # make text a set of long lines, one per paragraph.
    paragraphs = info['description'].split('\n\n')
    lines = [paragraph.replace('\n', ' ') for paragraph in paragraphs]
    text = '\n'.join(lines)

    info['files'] = [info['file'] + '.' + info['ext']]
    regex = r'[tT]he (?:file|image) ([\w\/]+\.\w+)'
    for name in re.findall(regex, text):
        if name not in info['files']:
            info['files'].append(name)

    # add links where the files are referenced
    folder = '_'.join(info['source'].split(sep)[:-1]) + '_'
    text = re.sub(r'([tT]he (?:file|image) )([\w\/]+\.\w+)',
                  r'\1:ref:`\2 <$folder$\2>`', text)
    text = text.replace('$folder$', folder)

    # now break up text into array of paragraphs, each an array of lines.
    lines = text.split('\n')
    paragraphs = [textwrap.wrap(line, line_length) for line in lines]
    info['enhanced_description'] = paragraphs


def get_infos(dir_name):
    ''' return infos, an array info dicts for each matching screenshot in the
    dir, sorted by source file name, and adding the field 'num' as he unique
    order in this array of dicts'.

    '''
    infos = [i for i in iter_docstring_info(dir_name)]
    infos.sort(key=lambda x: x['source'])
    for num, info in enumerate(infos):
        info['num'] = num
        enhance_info_description(info)
    return infos


def make_gallery_page(infos):
    ''' return string of the rst (Restructured Text) of the gallery page,
    showing information on all screenshots found.
    '''

    def a(s=''):
        ''' append formatted s to output, which will be joined into lines '''
        output.append(s.format(**info))

    def t(left='', right=''):
        ''' append left and right format strings into a table line. '''
        l = left.format(**info)
        r = right.format(**info)
        if len(l) > width1 or len(r) > width2:
            Logger.error('items to wide for generated table: "%s" and "%s"',
                         l, r)
            return
        output.append('| {0:{w1}} | {1:{w2}} |'
                      .format(l, r, w1=width1, w2=width2))

    gallery_top = '''
Gallery
-------

.. _Tutorials:  ../tutorials-index.html

.. container:: title

    This gallery lets you explore the many examples included with Kivy.
    Click on any screenshot to see the code.

This gallery contains:

    * Examples from the examples/ directory that show specific capabilities of
      different libraries and features of Kivy.
    * Demonstrations from the examples/demos/ directory that explore many of
      Kivy's abilities.

There are more Kivy programs elsewhere:

    * Tutorials_ walks through the development of complete Kivy applications.
    * Unit tests found in the source code under the subdirectory kivy/tests/
      can also be useful.

We hope your journey into learning Kivy is exciting and fun!

'''
    output = [gallery_top]

    for info in infos:
        a("\n.. |link{num}|  replace:: :doc:`{source}<gen__{dunder}>`")
        a("\n.. |pic{num}| image:: ../images/examples/{dunder}.png"
          "\n    :width:  216pt"
          "\n    :align:  middle"
          "\n    :target: gen__{dunder}.html")
        a("\n.. |title{num}|  replace:: **{title}**")

    # write the table
    width1, width2 = 20, 50  # not including two end spaces
    head = '+-' + '-' * width1 + '-+-' + '-' * width2 + '-+'
    a()
    a(head)

    for info in infos:
        t('| |pic{num}|', '| |title{num}|')
        t('| |link{num}|', '')
        paragraphs = info['description'].split("\n\n")
        for p in paragraphs:
            for line in textwrap.wrap(p, width2):
                t('', line)
            t()  # line between paragraphs
        t()
        a(head)
    return "\n".join(output) + "\n"


def make_detail_page(info):
    ''' return str of the rst text for the detail page of the file in info. '''

    def a(s=''):
        ''' append formatted s to output, which will be joined into lines '''
        output.append(s.format(**info))

    output = []
    a('{title}')
    a('=' * len(info['title']))
    a('\n.. |pic{num}| image:: /images/examples/{dunder}.png'
      '\n   :width: 50%'
      '\n   :align: middle')
    a('\n|pic{num}|')
    a()
    for paragraph in info['enhanced_description']:
        for line in paragraph:
            a(line)
        a()

    # include images
    last_lang = '.py'
    for fname in info['files']:
        full_name = slash(info['dir'], fname)
        ext = re.search(r'\.\w+$', fname).group(0)
        a('\n.. _`' + full_name.replace(sep, '_') + '`:')
        # double separator if building on windows (sphinx skips backslash)
        if '\\' in full_name:
            full_name = full_name.replace(sep, sep*2)

        if ext in ['.png', '.jpg', '.jpeg']:
            title = 'Image **' + full_name + '**'
            a('\n' + title)
            a('~' * len(title))
            a('\n.. image:: ../../../examples/' + full_name)
            a('     :align:  center')
        else:  # code
            title = 'File **' + full_name + '**'
            a('\n' + title)
            a('~' * len(title))
            if ext != last_lang and ext != '.txt':
                a('\n.. highlight:: ' + ext[1:])
                a('    :linenothreshold: 3')
                last_lang = ext
            # prevent highlight errors with 'none'
            elif ext == '.txt':
                a('\n.. highlight:: none')
                a('    :linenothreshold: 3')
                last_lang = ext
            a('\n.. include:: ../../../examples/' + full_name)
            a('    :code:')
    return '\n'.join(output) + '\n'


def write_file(name, s):
    ''' write the string to the filename '''
    with open(name, 'w') as f:
        f.write(s)


def make_index(infos):
    ''' return string of the rst for the gallery's index.rst file. '''
    start_string = '''
Gallery of Examples
===================

.. toctree::
    :maxdepth: 1

    gallery'''
    output = [start_string]
    for info in infos:
        output.append('    gen__{}'.format(info['dunder']))
    return '\n'.join(output) + '\n'


def write_all_rst_pages():
    ''' Do the main task of writing the gallery,
    detail, and index rst pages.
    '''
    infos = get_infos(screenshots_dir)
    s = make_gallery_page(infos)
    write_file(gallery_filename, s)

    for info in infos:
        s = make_detail_page(info)
        detail_name = slash(generation_dir,
                            'gen__{}.rst'.format(info['dunder']))
        write_file(detail_name, s)

    s = make_index(infos)
    index_name = slash(generation_dir, 'index.rst')
    write_file(index_name, s)
    Logger.info('gallery.py: Created gallery rst documentation pages.')


if __name__ == '__main__':
    write_all_rst_pages()
