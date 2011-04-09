from kivy.app import App
import sys


class TestApp(App):
    pass

if __name__ == '__main__':
    ''' Add template1/ or template2/
    to the command line to load different kv files'''
    if sys.argv.__len__() is 2:
        TestApp().run(sys.argv[1])
    else if sys.argv.__len__() is 1:
        TestApp().run()
    else:
        print "Usage: "+sys.argv[0]+" [directory_of_kv_file]"
