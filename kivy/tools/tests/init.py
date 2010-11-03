__all__ = ('test', 'test_runkivy', 'test_image')

def import_kivy_no_window():
    import kivy

def import_kivy_window():
    import os
    os.environ['KIVY_WINDOW'] = 'glut'
    os.environ['KIVY_GLUT_UNITTEST'] = '1'
    import kivy

def test_image():
    pass

def test_runkivy(*largs, **kwargs):
    from kivy import runTouchApp, curry, getClock, stopTouchApp
    kwargs.setdefault('frame', 1)

    class testinfo(object):
        frame = kwargs.get('frame') + 1

    def test_runkivy_stop(info, *largs):
        info.frame -= 1
        if info.frame == 0:
            stopTouchApp()

    getClock().schedule_interval(curry(test_runkivy_stop, testinfo), 0)
    runTouchApp(*largs)

def test(cond):
    '''Test a condition, and print the result on the screen'''
    import sys
    import inspect
    import os
    frame = sys._current_frames().values()[0]
    callers = inspect.getouterframes(frame)
    caller = callers[1]
    info = inspect.getframeinfo(caller[0])
    code = info.code_context[0].replace('\n','').strip()
    if cond:
        os.environ['__test_passed'] = str(int(os.environ['__test_passed']) + 1)
        testresult(code, 'OK')
    else:
        os.environ['__test_failed'] = str(int(os.environ['__test_failed']) + 1)
        testresult(code, 'Failed')

def testresult(code, ret):
    '''Print a result on the screen'''
    import os, sys
    if '__verbose' not in os.environ:
        return
    print '%-35s %-35s %4s' % (
        '%s:%s' % (os.environ['__modname'][5:],
                   os.environ['__testname'][9:]),
        code,
        ret
    )

def _set_testinfo(a, b):
    import os
    os.environ['__modname'] = a
    os.environ['__testname'] = b
    os.environ['__test_passed'] = '0'
    os.environ['__test_failed'] = '0'


if __name__ == '__main__':
    import os
    import sys
    import time

    def testrun(modname, testname):
        _set_testinfo(modname, testname)
        __import__(modname)
        mod = sys.modules[modname]
        getattr(mod, testname)()
        passed = os.environ['__test_passed']
        failed = os.environ['__test_failed']
        print '%-35s %3s passed, %3s failed' % (
            '%s:%s' % (os.environ['__modname'][5:],
                       os.environ['__testname'][9:]),
            passed, failed)

    def testrun_launch(modname, testname):
        import subprocess
        args = []
        kargs = {}
        if '__verbose' in os.environ:
            args.append('--verbose')
        if '__debug' not in os.environ:
            kargs['stderr'] = subprocess.PIPE
        p = subprocess.Popen(
            ['python', __file__, modname, testname] + args,
            env=os.environ,
            **kargs
        )
        p.communicate()

    opts = [x for x in sys.argv if x.startswith('--')]
    sys.argv = [x for x in sys.argv if not x.startswith('--')]

    for x in opts:
        if x in ('--verbose'):
            os.environ['__verbose'] = '1'
        elif x in ('--debug'):
            os.environ['__debug'] = '1'
        elif x in ('--help'):
            print 'Usage: python init.py [options] <filter>'
            print '  --debug              show debug'
            print '  --verbose            show verbose'
            print '  --help               show this help'
            sys.exit(0)

    if len(sys.argv) == 3:
        modname = sys.argv[1][:-3]
        testname = sys.argv[2]
        testrun(modname, testname)
    else:

        flt = None
        if len(sys.argv) == 2:
            flt = sys.argv[1]

        current_dir = os.path.dirname(__file__)
        if current_dir == '':
            current_dir = '.'

        start = time.time()

        l = os.listdir(current_dir)
        l.sort()
        for modname in l:
            if not modname.startswith('test_'):
                continue
            if modname[-3:] != '.py':
                continue
            mod = __import__(modname[:-3])
            for testname in dir(mod):
                if not testname.startswith('unittest_'):
                    continue
                if flt is None or flt in testname:
                    testrun_launch(modname, testname)

        elasped = time.time() - start
        print '>> Finished in %.3fs' % (
            elasped,
        )
