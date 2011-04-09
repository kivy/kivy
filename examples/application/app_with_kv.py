from kivy.app import App
import sys
class TestApp(App):
    pass

if __name__ == '__main__':
    if sys.argv.__len__() is 2:
        TestApp().run(sys.argv[1])
    else:
        print "Usage: "+sys.argv[0]+" [directory_of_kv_file]"
        
        
