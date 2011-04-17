from kivy.app import App
import sys
from kivy.lang import Builder


class TestApp(App):
    pass
#    def load_kv(self):
#        root=Builder.load_file('template1/test.kv')
#        if root:
#          self.root = root

if __name__ == '__main__':
    ''' Give commandline argument of "template1" or "template2"
    to use the templates in respective directories
    '''
    TestApp().run()
