from kivy.tools.packaging.pyinstaller_hooks import get_deps_all
import sys
from os.path import dirname, join

args = sys.argv[1:]
if args and args[0] == 'hook':
    with open(join(dirname(__file__), 'hook-kivy.py')) as fh:
        src = fh.read()

    formatted_lines = []
    lines = get_deps_all()['hiddenimports']

    for i, line in enumerate(lines):
        if (i and
            line[:line.rfind('.')] != lines[i - 1][:lines[i - 1].rfind('.')]):
            formatted_lines.append('\n')

        if i == len(lines) - 1:
            formatted_lines.append("    '{}'".format(line))
        else:
            formatted_lines.append("    '{}',\n".format(line))
    lines = formatted_lines

    lines = '{}\n\nhiddenimports += [\n{}\n]\n'.format(src, ''.join(lines))
    if len(args) > 1:
        with open(args[1], 'w') as fh:
            fh.write(lines)
    else:
        print(lines)
