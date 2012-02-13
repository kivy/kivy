__all__ = ('FactoryBuild', )

from distutils.cmd import Command
import fnmatch
import os
import kivy
import types

ignore_list = (
    'kivy.lib',
    'kivy.input.providers',
    'kivy.input.postproc',
    'kivy.modules',
    'kivy.tools',
    'kivy.parser',
    'kivy.tests',
)


class FactoryBuild(Command):
    description = 'Build the factory relation file (for factory.py)'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        print '--------------------------------------------'
        print 'Building factory relation file'
        print '--------------------------------------------'

        root_dir = os.path.dirname(kivy.__file__)
        filename = os.path.join(root_dir, 'factory_registers.py')
        with open(filename, 'w') as fd:
            fd.close()

        # ensure we don't have any thing like doc running
        symbols = []
        for root, dirnames, filenames in os.walk(root_dir):
            if not root.startswith(root_dir):
                raise Exception('Directory should start with the kivy'
                                'directory')
            root = 'kivy' + root[len(root_dir):].replace(os.path.sep, '.')
            for filename in fnmatch.filter(filenames, '*.[ps][yo]'):
                module = '%s.%s' % (root, filename[:-3])

                # check ignore list first
                ignore = False
                for ignore in ignore_list:
                    if module.startswith(ignore):
                        ignore = True
                        break
                if ignore is True:
                    #print '<<< ignored (ignore list)'
                    continue

                # special case, core providers
                if root.startswith('kivy.core.'):
                    if not root.endswith('__init__.py'):
                        #print '<<< ignored (not a __init__.py)'
                        continue

                print '>>>', module, '::',

                try:
                    m = __import__(name=module, fromlist='.')
                except Exception, e:
                    print
                    print 'ERROR:', e
                    continue
                if not hasattr(m, '__all__'):
                    print
                    continue
                for symbol in getattr(m, '__all__'):
                    if symbol.startswith('_'):
                        continue
                    attr = getattr(m, symbol)
                    if type(attr) not in (
                            types.TypeType,
                            types.ClassType,
                        ):
                        continue
                    symbols.append((symbol, module))
                    print symbol,
                print

        print
        print '--------------------------------------------'
        print 'Found %d symbols, generating file' % len(symbols)
        print '--------------------------------------------'

        filename = os.path.join(root_dir, 'factory_registers.py')
        with open(filename, 'w') as fd:
            fd.write('# Auto-generated file by setup.py build_factory\n')
            fd.write('\n')
            fd.write('from kivy.factory import Factory\n')
            fd.write('\n')
            fd.write('r = Factory.register\n')
            for x in symbols:
                fd.write("r('%s', module='%s')\n" % x)

        print 'File written at', filename
