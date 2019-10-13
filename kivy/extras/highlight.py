'''Pygments lexer for kv language
'''
from pygments.lexer import RegexLexer, bygroups, using
from pygments.lexers.agile import PythonLexer
from pygments import highlight
from pygments.token import *
from pygments.formatters import get_formatter_by_name
import sys


class KivyLexer(RegexLexer):
    name = 'Kivy'
    aliases = ['kivy', 'kv']
    filenames = ['*.kv']
    tokens = {
        'root': [
            (r'#:.*?$', Comment.Preproc),
            (r'#.*?$', using(PythonLexer)),
            (r'\s+', Text),
            (r'<.+>', Name.Namespace),
            (r'(\[)(\s*)(.*?)(\s*)(@)',
                bygroups(Punctuation, Text, Name.Class, Text, Operator),
                'classList'),
            (r'[A-Za-z][A-Za-z0-9]*$', Name.Attribute),
            (r'(.*?)(\s*)(:)(\s*)$',
                bygroups(Name.Class, Text, Punctuation, Text)),
            (r'(.*?)(\s*)(:)(\s*)(.*?)$',
                bygroups(Name.Attribute, Text, Punctuation, Text,
                using(PythonLexer))),
            (r'[^:]+?$', using(PythonLexer))],
        'classList': [
            (r'(,)(\s*)([A-Z][A-Za-z0-9]*)',
                bygroups(Punctuation, Text, Name.Class)),
            (r'(\+)(\s*)([A-Z][A-Za-z0-9]*)',
                bygroups(Operator, Text, Name.Class)),
            (r'\s+', Text),
            (r'[A-Z][A-Za-z0-9]*', Name.Class),
            (r'\]', Punctuation, '#pop')]}


if __name__ == '__main__':
    ''' This lexer will highlight .kv file. The first argument is the source
    file, the second argument is the format of the destination and the third
    argument is the output filename
    '''
    if len(sys.argv) is not 4:
        raise Exception('Three arguments expected, found %s' %
            (len(sys.argv) - 1))
    k = KivyLexer()
    with open(sys.argv[1], 'r') as fd:
        with open(sys.argv[3], 'w') as out:
            highlight(fd.read(), k, get_formatter_by_name(sys.argv[2]), out)
