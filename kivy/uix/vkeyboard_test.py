from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.core.window import WindowBase, Window


class TextInputWithKeyboard(Widget):
    def __init__(self, **kwargs):
        
        super(TextInputWithKeyboard,self).__init__(**kwargs)
        
        self.text_input = TextInput(text='', pos = (0,200))
        self.text_input2 = TextInput(text='', pos = (400,200))
        #self.keyboard = VKeyboard(target = self.text_input)      

        #self.draw(1,1)
        #self.keyboard.bind(on_touch_move = self.draw)    
        
        self.add_widget(self.text_input)
        self.add_widget(self.text_input2)
        #self.add_widget(self.keyboard)
        #self.keyboard.move_to_target()
        
        self.button = ToggleButton(text = 'keyboard')
        self.button.pos =(0,350)
        self.button.bind(on_press = self.call_keyboard, on_release = self.remove_keyboard)
        self.add_widget(self.button)
        
        self.button2 = ToggleButton(text = 'keyboard2')
        self.button2.pos = (400,350)
        self.button2.bind(on_press = self.call_keyboard2, on_release = self.remove_keyboard2)
        self.add_widget(self.button2)

    def call_keyboard(self,b):
        if not self.button.state == "down" : return  
        window = self.get_root_window()
        window.provide_vkeyboard(target = self.text_input, callback = self.callback)        
    
    def callback(self):
        print "callback"

    def remove_keyboard(self,b):
        if not self.button.state == "normal" : return  
        window = self.get_root_window()
        window.release_vkeyboard(self.text_input)

    def call_keyboard2(self,b):
        if not self.button2.state == "down" : return  
        window = self.get_root_window()
        window.provide_vkeyboard(target = self.text_input2, callback = self.callback)        

    def remove_keyboard2(self,b):
        if not self.button2.state == "normal" : return  
        window = self.get_root_window()
        window.release_vkeyboard(self.text_input2)

    """
    def draw(self,a,b):
        #draw a line between keyb and text input
        #self.canvas.clear()
        ti = self.text_input
        k = self.keyboard
        with self.canvas : 
            Color(1., 1., 1.)
            LineWidth(15.0)
            if k.y > ti.y :
                ky = k.y
                tiy = ti.y + ti.height  
            else : 
                ky = k.y + k.get_size()[1]
                tiy = ti.y
            points = [ti.x + ti.width/2, tiy, k.x + k.get_size()[0]/2, ky]
            Line(points=points)
        #self.canvas.draw()     
    """
    
        

class TestApp(App):
    
    def build(self):
        self.g = TextInputWithKeyboard(app=self)
        return self.g
         
    

if __name__ in ('__android__', '__main__'):
    TestApp().run()
