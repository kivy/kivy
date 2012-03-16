import sys
from os import walk
from os.path import isdir, join, abspath, dirname
import pep8
import time

htmlmode = False


class KivyStyleChecker(pep8.Checker):

    def __init__(self, filename):
        pep8.Checker.__init__(self, filename)

    def report_error(self, line_number, offset, text, check):
        if htmlmode is False:
            return pep8.Checker.report_error(self,
                line_number, offset, text, check)

        # html generation
        print '<tr><td>%d</td><td>%s</td></tr>' % (line_number, text)


if __name__ == '__main__':

    def usage():
        print 'Usage: python pep8kivy.py [-html] <file_or_folder_to_check>*'
        print 'Folders will be checked recursively.'
        sys.exit(1)

    if len(sys.argv) < 2:
        usage()
    if sys.argv[1] == '-html':
        if len(sys.argv) < 3:
            usage()
        else:
            htmlmode = True
            targets = sys.argv[-1].split()
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
    pep8.process_options([''])
    exclude_dirs = ['/lib', '/coverage', '/pep8', '/doc']
    exclude_files = ['kivy/gesture.py', 'osx/build.py', 'win32/build.py',
                     'kivy/tools/stub-gl-debug.py']
    for target in targets:
        if isdir(target):
            if htmlmode:
                path = join(dirname(abspath(__file__)), 'pep8base.html')
                print open(path, 'r').read()
                print '''<p>Generated: %s</p><table>''' % (time.strftime('%c'))

            for dirpath, dirnames, filenames in walk(target):
                cont = False
                for pat in exclude_dirs:
                    if pat in dirpath:
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

                    if htmlmode:
                        print '<tr><th colspan="2">%s</td></tr>' \
                             % complete_filename
                    errors += check(complete_filename)

            if htmlmode:
                print '</div></div></table></body></html>'

        else:
            # Got a single file to check
            for pat in exclude_dirs + exclude_files:
                if pat in target:
                    break
            else:
                if target.endswith('.py'):
                    errors += check(target)

    # If errors is 0 we return with 0. That's just fine.
    sys.exit(errors)
