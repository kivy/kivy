from kivy.app import App
import sys

class TestApp(App):
    pass

if __name__ == '__main__':
    ''' Give commandline argument of "template1" or "template2" 
    to use the templates in respective directories
    '''
    if sys.argv.__len__() is 2:
        TestApp().run(sys.argv[1])
    else:
        TestApp().run()
