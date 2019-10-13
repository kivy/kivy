import sys
from os import walk
from os.path import isdir, join, normpath

import pep8


pep8_ignores = (
    'E125',  # continuation line does not
             # distinguish itself from next logical line
    'E126',  # continuation line over-indented for hanging indent
    'E127',  # continuation line over-indented for visual indent
    'E128',  # continuation line under-indented for visual indent
    'E402',  # module level import not at top of file
    'E741',  # ambiguous variable name
    'E731',  # do not assign a lambda expression, use a def
    'W503',  # allow putting binary operators after line split
)


class KivyStyleChecker(pep8.Checker):

    def __init__(self, filename):
        pep8.Checker.__init__(self, filename, ignore=pep8_ignores)

    def report_error(self, line_number, offset, text, check):
        return pep8.Checker.report_error(
            self, line_number, offset, text, check)


if __name__ == '__main__':

    def usage():
        print('Usage: python pep8kivy.py <file_or_folder_to_check>*')
        print('Folders will be checked recursively.')
        sys.exit(1)

    if len(sys.argv) < 2:
        usage()
    elif sys.argv == 2:
        targets = sys.argv[-1]
    else:
        targets = sys.argv[-1].split()

    def check(fn):
        try:
            checker = KivyStyleChecker(fn)
        except IOError:
            # File couldn't be opened, so was deleted apparently.
            # Don't check deleted files.
            return 0
        return checker.check_all()

    errors = 0

    exclude_dirs = [
        'kivy/lib',
        'kivy/deps',
        'kivy/tools/pep8checker',
        'coverage',
        'doc'
    ]
    exclude_dirs = [normpath(i) for i in exclude_dirs]
    exclude_files = [
        'kivy/gesture.py',
        'kivy/tools/stub-gl-debug.py',
        'kivy/modules/webdebugger.py',
        'kivy/modules/_webdebugger.py'
    ]
    exclude_files = [normpath(i) for i in exclude_files]

    for target in targets:
        if isdir(target):
            for dirpath, dirnames, filenames in walk(target):
                cont = False
                dpath = normpath(dirpath)
                for pat in exclude_dirs:
                    if dpath.startswith(pat):
                        cont = True
                        break
                if cont:
                    continue
                for filename in filenames:
                    if not filename.endswith('.py'):
                        continue
                    cont = False
                    complete_filename = join(dirpath, filename)
                    for pat in exclude_files:
                        if complete_filename.endswith(pat):
                            cont = True
                    if cont:
                        continue

                    errors += check(complete_filename)

        else:
            # Got a single file to check
            for pat in exclude_dirs + exclude_files:
                if pat in target:
                    break
            else:
                if target.endswith('.py'):
                    errors += check(target)

    if errors:
        print("Error: {} style guide violation(s) encountered.".format(errors))
        sys.exit(1)
