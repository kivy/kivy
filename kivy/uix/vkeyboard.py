'''
VKeyboard: Virtual keyboard with custom layout support
'''
__all__ = ('VKeyboard', )

from kivy.app import App
from kivy.uix.scatter import Scatter
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, \
    BooleanProperty, DictProperty, ListProperty 
from kivy.logger import Logger
from kivy.graphics import Color, Line, Rectangle, LineWidth
from kivy.graphics.vertex_instructions import BorderImage
from kivy.clock import Clock
from kivy.core.image import Image


from os.path import join, split, abspath, splitext#, dirname, exists
from os import listdir 
from json import loads


azerty = {
    "ID" : "azerty",
    "TITLE" : "Azerty",
    "DESCRIPTION" : "A French keyboard without international keys",
    "SIZE" : [15, 5],
    "NORMAL_5" : [
        ["@", "@", "None", 1],    ["&", "&", "None", 1],    [u"\xe9", u"\xe9", "None", 1],
        ['"', '"', "None", 1],    ["\'", "\'", "None", 1],  ["[", "[", "None", 1],
        ["-", "-", "None", 1],    [u"\xe8", u"\xe8", "None", 1],    ["_", "_", "None", 1],
        [u"\xe7", u"\xe7", "None", 1],    [u"\xe0", u"\xe0", "None", 1],    ["]", "]", "None", 1],
        ["=", "=", "None", 1],    [u"\u232b", "None", "backspace", 2]
    ],
    "NORMAL_4" : [
        [u"\u21B9", "chr[0x09]", "None", 1.5],  ["a", "a", "None", 1],    ["z", "z", "None", 1],
        ["e", "e", "None", 1],    ["r", "r", "None", 1],    ["t", "t", "None", 1],
        ["y", "y", "None", 1],    ["u", "u", "None", 1],    ["i", "i", "None", 1],
        ["o", "o", "None", 1],    ["p", "p", "None", 1],    ["^", "^", "None", 1],
        ["$", "$", "None", 1],    [u"\u23ce", "None", "enter", 1.5]
    ],
    "NORMAL_3" : [
        [u"\u21ea", "None", "capslock", 1.8],  ["q", "q", "None", 1],    ["s", "s", "None", 1],
        ["d", "d", "None", 1],    ["f", "f", "None", 1],    ["g", "g", "None", 1],
        ["h", "h", "None", 1],    ["j", "j", "None", 1],    ["k", "k", "None", 1],
        ["l", "l", "None", 1],    ["m", "m", "None", 1],    [u"\xf9", u"\xf9", "None", 1],
        ["*", "*", "None", 1],    [u"\u23ce", "None", "enter", 1.2]
    ],
    "NORMAL_2" : [
        [u"\u21e7", "None", "shift_L", 1.5],  ["<", "<", "None", 1],    ["w", "w", "None", 1],
        ["x", "x", "None", 1],
        ["c", "c", "None", 1],    ["v", "v", "None", 1],    ["b", "b", "None", 1],
        ["n", "n", "None", 1],    [",", ",", "None", 1],    [";", ";", "None", 1],
        [":", ":", "None", 1],    ["!", "!", "None", 1],    [u"\u21e7", "None", "shift_R", 2.5]
    ],
    "NORMAL_1" : [
        [" ", " ", "None", 12], [u"\u2b12", "None", "layout", 1.5], [u"\u2a2f", "None", "escape", 1.5]
    ],
    "SHIFT_5" : [
        ["|", "|", "None", 1],    ["1", "1", "None", 1],    ["2", "2", "None", 1],
        ["3", "3", "None", 1],    ["4", "4", "None", 1],    ["5", "5", "None", 1],
        ["6", "6", "None", 1],    ["7", "7", "None", 1],    ["8", "8", "None", 1],
        ["9", "9", "None", 1],    ["0", "0", "None", 1],    ["#", "#", "None", 1],
        ["+", "+", "None", 1],    [u"\u232b", "None", "backspace", 2]
    ],
    "SHIFT_4" : [
        [u"\u21B9", "chr[0x09]", "None", 1.5],  ["A", "A", "None", 1],    ["Z", "Z", "None", 1],
        ["E", "E", "None", 1],    ["R", "R", "None", 1],    ["T", "T", "None", 1],
        ["Y", "Y", "None", 1],    ["U", "U", "None", 1],    ["I", "I", "None", 1],
        ["O", "O", "None", 1],    ["P", "P", "None", 1],    ["[", "[", "None", 1],
        ["]", "]", "None", 1],    [u"\u23ce", "None", "enter", 1.5]
    ],
    "SHIFT_3" : [
        [u"\u21ea", "None", "capslock", 1.8],  ["Q", "Q", "None", 1],    ["S", "S", "None", 1],
        ["D", "D", "None", 1],    ["F", "F", "None", 1],    ["G", "G", "None", 1],
        ["H", "H", "None", 1],    ["J", "J", "None", 1],    ["K", "K", "None", 1],
        ["L", "L", "None", 1],    ["M", "M", "None", 1],    ["%", "%", "None", 1],
        [u"\xb5", u"\xb5", "None", 1],    [u"\u23ce", "None", "enter", 1.2]
    ],
    "SHIFT_2" : [
        [u"\u21e7", "None", "shift_L", 1.5],  [">", ">", "None", 1],    ["W", "W", "None", 1],
        ["X", "X", "None", 1],    ["C", "C", "None", 1],    ["V", "V", "None", 1],
        ["B", "B", "None", 1],    ["N", "N", "None", 1],    ["?", "?", "None", 1],
        [".", ".", "None", 1],    ["/", "/", "None", 1],    [u"\xa7", u"\xa7", "None", 1],
        [u"\u21e7", "None", "shift_R", 2.5]
    ],
    "SHIFT_1" : [
        [" ", " ", "None", 12], [u"\u2b12", "None", "layout", 1.5], [u"\u2a2f", "None", "escape", 1.5]
    ]
}

qwerty = {   
    "ID" : "qwerty",
    "TITLE": "Qwerty",
    "DESCRIPTION": "A classical US Keyboard",
    "SIZE": [15, 5],
    "NORMAL_5": [
        ('`', '`', None, 1),    ('1', '1', None, 1),    ('2', '2', None, 1),
        ('3', '3', None, 1),    ('4', '4', None, 1),    ('5', '5', None, 1),
        ('6', '6', None, 1),    ('7', '7', None, 1),    ('8', '8', None, 1),
        ('9', '9', None, 1),    ('0', '0', None, 1),    ('+', '+', None, 1),
        ('=', '=', None, 1),    (u'\u232b', None, 'backspace', 2),
    ],
    "NORMAL_4" : [
        (u'\u21B9', chr(0x09), None, 1.5),  ('q', 'q', None, 1),    ('w', 'w', None, 1),
        ('e', 'e', None, 1),    ('r', 'r', None, 1),    ('t', 't', None, 1),
        ('y', 'y', None, 1),    ('u', 'u', None, 1),    ('i', 'i', None, 1),
        ('o', 'o', None, 1),    ('p', 'p', None, 1),    ('{', '{', None, 1),
        ('}', '}', None, 1),    ('|', '|', None, 1.5)
    ],
    "NORMAL_3": [
        (u'\u21ea', None, 'capslock', 1.8),  ('a', 'a', None, 1),    ('s', 's', None, 1),
        ('d', 'd', None, 1),    ('f', 'f', None, 1),    ('g', 'g', None, 1),
        ('h', 'h', None, 1),    ('j', 'j', None, 1),    ('k', 'k', None, 1),
        ('l', 'l', None, 1),    (':', ':', None, 1),    ('"', '"', None, 1),
        (u'\u23ce', None, 'enter', 2.2),
    ],
    "NORMAL_2": [
        (u'\u21e7', None, 'shift_L', 2.5),  ('z', 'z', None, 1),    ('x', 'x', None, 1),
        ('c', 'c', None, 1),    ('v', 'v', None, 1),    ('b', 'b', None, 1),
        ('n', 'n', None, 1),    ('m', 'm', None, 1),    ('<', '<', None, 1),
        ('>', '>', None, 1),    ('?', '?', None, 1),    (u'\u21e7', None, 'shift_R', 2.5),
    ],
    "NORMAL_1": [
        (' ', ' ', None, 12), (u'\u2b12', None, 'layout', 1.5), (u'\u2a2f', None, 'escape', 1.5),

    ],
    "SHIFT_5": [
        ('~', '~', None, 1),    ('!', '!', None, 1),    ('@', '@', None, 1),
        ('#', '#', None, 1),    ('$', '$', None, 1),    ('%', '%', None, 1),
        ('^', '^', None, 1),    ('&', '&', None, 1),    ('*', '*', None, 1),
        ('(', '(', None, 1),    (')', ')', None, 1),    ('_', '_', None, 1),
        ('+', '+', None, 1),    (u'\u232b', None, 'backspace', 2),
    ],
    "SHIFT_4": [
        (u'\u21B9', chr(0x09), None, 1.5),  ('Q', 'Q', None, 1),    ('W', 'W', None, 1),
        ('E', 'E', None, 1),    ('R', 'R', None, 1),    ('T', 'T', None, 1),
        ('Y', 'Y', None, 1),    ('U', 'U', None, 1),    ('I', 'I', None, 1),
        ('O', 'O', None, 1),    ('P', 'P', None, 1),    ('[', '[', None, 1),
        (']', ']', None, 1),    ('?', '?', None, 1.5)
    ],
    "SHIFT_3": [
        (u'\u21ea', None, 'capslock', 1.8),  ('A', 'A', None, 1),    ('S', 'S', None, 1),
        ('D', 'D', None, 1),    ('F', 'F', None, 1),    ('G', 'G', None, 1),
        ('H', 'H', None, 1),    ('J', 'J', None, 1),    ('K', 'K', None, 1),
        ('L', 'L', None, 1),    (':', ':', None, 1),    ('"', '"', None, 1),
        (u'\u23ce', None, 'enter', 2.2),
    ],
    "SHIFT_2": [
        (u'\u21e7', None, 'shift_L', 2.5),  ('Z', 'Z', None, 1),    ('X', 'X', None, 1),
        ('C', 'C', None, 1),    ('V', 'V', None, 1),    ('B', 'B', None, 1),
        ('N', 'N', None, 1),    ('M', 'M', None, 1),    (',', ',', None, 1),
        ('.', '.', None, 1),    ('/', '/', None, 1),    (u'\u21e7', None, 'shift_R', 2.5),
    ],
    "SHIFT_1": [
        (' ', ' ', None, 12), (u'\u2b12', None, 'layout', 1.5), (u'\u2a2f', None, 'escape', 1.5),
    ]

}


class VKeyboard(Widget):
    '''
    MTVKeyboard is an onscreen keyboard with multitouch support.
    Its layout is entirely customizable and you can switch between available
    layouts using a button in the bottom right of the widget.

    :Parameters:
        `layout` : KeyboardLayout object, default to None
            If None, keyboard layout will be created from configuration
            property.
        `time_lazy_update` : float, default to 0.2
            Time in seconds to force a lazy update when keyboard size changes
        `repeat` : float, default to 0.2
            Key repeat rate. 1/15. will repeat the last key 5 times per seconds
        `repeat_timeout` : float, default to 0.2
            Will start to repeat the key after 200ms

    :Events:
        `on_key_down` : key
            Fired when a key is down.
            The key contains: displayed_str, internal_str, internal_action, width
        `on_key_up` : key
            Fired when a key is up.
            The key contains: displayed_str, internal_str, internal_action, width
        `on_text_change` : text
            Fired when the internal text is changed

    List of internal actions available :

    * backspace
    * capslock
    * enter
    * escape
    * layout (to display layout list)
    * shift
    * shift_L
    * shift_R

    '''
    id = NumericProperty( 0 ) #id of the keyboard (if several)
    target = ObjectProperty( '' ) #the id of the current widget connected to it
    callback = ObjectProperty( None ) #the function to call when the keyboard is released
    size_k = ObjectProperty( (700, 200) )
    scale_k = NumericProperty( 1.0 )
    scale_min = NumericProperty( 0.4 )
    scale_max = NumericProperty( 1.6 )
    #pos = ObjectProperty( (0, 0) )
    layout = DictProperty( qwerty )#{} ) # )
    layout_path = StringProperty( join(abspath(''), 'layouts') )
    position_lock = BooleanProperty( True )#touch the margin to translate and scale the keyboard    
    style = DictProperty( {'margin_hint' : (0.05, 0.06, 0.05, 0.06), 'key_margin_hint' : (0.05, 0.05, 0.05, 0.05), 'background_color':(0.15,0.15,0.15),'key_color':(0.8,0.8,0.8),'key_texture_path': 'images/border29.png','background_texture_path':'images/border42.png','key_color_active':(0.8,.8,0.8),'key_texture_path_active':'images/border30.png' } ) 
    #style = DictProperty( {'margin_hint' : (0.03, 0.05, 0.03, 0.05), 'key_margin_hint' : (0.05, 0.05, 0.05, 0.05), 'background_color':(0.3,0.3,0.7),'key_color':(0.2,0.2,0.5),'key_texture_path': 'images/border23.png','background_texture_path':'images/border13.png','key_color_active':(0.,.7,0.),'key_texture_path_active':'images/border.png' } )   
    #style = DictProperty( {'margin_hint' : (0.03, 0.05, 0.03, 0.05), 'key_margin_hint' : (0.05, 0.05, 0.05, 0.05), 'background_color':(0.7,0.7,0.7),'key_color':(0.5,0.5,0.5),'key_texture_path': 'images/border29.png','background_texture_path':'images/border13.png','key_color_active':(0.5,.5,0.5),'key_texture_path_active':'images/border31.png' } )  
    #style = DictProperty( {'margin_hint' : (0.04, 0.06, 0.04, 0.06), 'key_margin_hint' : (0.05, 0.05, 0.05, 0.05), 'background_color':(0.7,0.7,0.7),'key_color':(0.5,0.5,0.5),'key_texture_path': 'images/border32.png','background_texture_path':'images/border36.png','key_color_active':(0.5,.5,0.5),'key_texture_path_active':'images/border31.png' } )
    #style = DictProperty( {'margin_hint' : (0.05, 0.06, 0.05, 0.06), 'key_margin_hint' : (0.05, 0.05, 0.05, 0.05), 'background_color':(0.15,0.15,0.15),'key_color':(0.8,0.8,0.8),'key_texture_path': 'images/border29.png','background_texture_path':'images/border44.png','key_color_active':(0.5,.5,0.5),'key_texture_path_active':'images/border30.png' } )        

    #internal variables
    mode = StringProperty('NORMAL') #Normal or Shift
    available_layouts = ListProperty( [] )
    layout_geometry = DictProperty( {} )
    caps_lock_key_on = BooleanProperty(False)
    shift_keyL = ObjectProperty( (0,0) )#pos on the layout, this value is gonna be refreshed when pressed
    shift_keyR = ObjectProperty( (0,0) )
    caps_lock_key = ObjectProperty( (0,0) ) 
    active_keys = DictProperty( {} )
    font_size = NumericProperty( 15 )
    touches = DictProperty( {} )
    old_scale = NumericProperty( 0 )   

    #time_lazy_update = NumericProperty( .2 ) 
    #repeat = NumericProperty( 1/15. ) 
    #repeat_timeout = NumericProperty( .2 )
    #old_scale = NumericProperty( 0. ) 
    #cache = DictProperty( {} )
    #current_cache = ObjectProperty( None )
    #last_update = DateProperty( '' )
    #last_update_scale = 1.
    #need_update = BooleanProperty( True )
    #self._internal_text     = u''
    #self._show_layout       = False
    #used_label = ListProperty( [] )
    #last_key_down = ListProperty( [] )
    #last_key_repeat = NumericProperty( 0 )
    #last_key_repeat_timeout = NumericProperty( 0 )
        


    def __init__(self, **kwargs):
        super(VKeyboard, self).__init__(**kwargs)
 
        """
        # first load available layouts from json files
        available_layouts = [] 
        dirList=listdir(self.layout_path)
        for fname in dirList:
            basename, extension = splitext(fname)
            if extension == '.json' :
                f = open(join(abspath(''), 'layouts',fname) , "r")
                json_content = f.read()
                json_content = '{"2":"kapin"}'#to be removed
                #print json_content
                layout = loads(json_content)
                #print layout
                available_layouts.append( layout )
        self.available_layouts = available_layouts
        """
        available_layouts = [] 
        for i in [azerty,qwerty] : 
            self.available_layouts.append(i)
        #print self.available_layouts 
         
        # load the default layout from configuration
        if self.layout is None :
            layout_loaded = False
            #config = self.config
            #config_keyboard = config.get('section1', 'keyboard')
            #config_layout = config.get('section1', 'keyboard_layout')
            config_layout = 'azerty'
            default_layout = ''
            for layout in available_layouts :
                if layout['id'] == 'qwerty' : 
                    default_layout = layout            
                if layout['id'] == config_layout :
                    self.layout = layout
                    layout_loaded = True
                    #print layout
                    log = 'Vkeyboard: <%s> keyboard layout mentionned in conf file was not found, fallback on QWERTY' % config_layout  
                    Logger.info(log)
            if not layout_loaded :
                self.layout = default_layout
                log = 'Vkeyboard: <%s> keyboard layout mentionned in conf file was not found, fallback on QWERTY' % config_layout  
                Logger.warning(log)  
        # prepare layout widget
        #mtop, mright, mbottom, mleft = self.style['margin']                   
        self.refresh_keys_hint()
        self.refresh_keys()
        self.draw_keys()

        #create a top layer to draw active keys on
        self.active_keys_layer = Widget()
        #self.active_keys_layer.bind(pos = self.pos, size = self.size)
        self.add_widget(self.active_keys_layer)
        
        #Clock.schedule_interval(self.change_layout,2.)
        
    def test_autoscale(self,dt):
        scale_k = self.scale_k
        scale_k += 0.02
        if scale_k >= 1.02 : scale_k = 0.2 
        self.scale_k = scale_k
        self.refresh(False)
        
    def reset_special_keys(self):
        self.shift_keyL = (0,0)
        self.shift_keyR = (0,0)
        self.capslock = (0,0)

    def change_layout(self):
        available_layouts = self.available_layouts
        current_index = available_layouts.index(self.layout)
        lenght = len(available_layouts)
        index = current_index +1
        if current_index == lenght-1 :
            #print lenght, current_index 
            index = 0
        self.layout = available_layouts[index]
        self.refresh(True)

    def switch_mode(self):
        
        if self.mode == 'NORMAL':
            self.mode = 'SHIFT'
        else : 
            self.mode = 'NORMAL'
        self.refresh(False)

    def refresh(self, k):
        #k : boolean . 
        #True : activates self.refresh_keys_hint()
        #True : happens only at launch or in case of a layout change 
        self.clear_widgets()
        self.canvas.clear() 
        if k == True : 
            self.reset_special_keys()
            self.refresh_keys_hint()
        self.refresh_keys()
        self.draw_keys() 
        self.add_widget(self.active_keys_layer)
        self.refresh_active_keys_layer()

    def refresh_active_keys_layer(self):
        self.active_keys_layer.clear_widgets()
        self.active_keys_layer.canvas.clear()  
        self.draw_active_keys()

    def refresh_keys_hint(self):
        layout = self.layout
        #print layout
        layout_size_l, layout_size_h = layout['SIZE'] # (5,15) for 5 lines, 15 keys
        layout_geometry = self.layout_geometry #stores keys' relative pos and size
        
        #l,h = self.size_k#self.bbox[1]#self.size
        mtop, mright, mbottom, mleft = self.style['margin_hint']
        kmtop, kmright, kmbottom, kmleft = self.style['key_margin_hint']
        #mode = self.mode        

        #get relative EFFICIENT surface of the layout without external margins
        el_hint = 1. - mleft - mright
        eh_hint = 1. - mtop - mbottom
        ex_hint = 0 + mleft
        ey_hint = 0 + mbottom
        layout_geometry['E_HINT'] = [(ex_hint,ey_hint),(el_hint,eh_hint)]  #[pos,size]
        #get relative unit surface
        ul_hint = (1. / layout_size_l) * el_hint 
        uh_hint = (1. / layout_size_h) * eh_hint 
        
        #calculate individual key RELATIVE surface and pos (without key margin)  
        current_y_hint = ey_hint
        for line_nb in range(1,layout_size_h+1):
             #get line_name 
             line_name = self.mode + '_'+ str(line_nb)
             layout_geometry['LINE_HINT_'+str(line_nb)] = []
             current_x_hint = ex_hint  
             #go through the list of keys (tupples of 4)
             for key in layout[line_name] :
                 #print key
                 #calculate relative pos, size 
                 layout_geometry['LINE_HINT_'+str(line_nb)].append( [(current_x_hint,current_y_hint),(key[3] * ul_hint,uh_hint)] ) #[pos,size]
                 #print [(kx_hint,ky_hint),(kl_hint,kh_hint)]
                 current_x_hint += key[3] * ul_hint     
             current_y_hint += uh_hint
    
        self.layout_geometry = layout_geometry
    
    def refresh_keys(self):
        layout_size_l, layout_size_h = self.layout['SIZE']
        layout_geometry = self.layout_geometry
        l,h = self.get_size()
        x = self.x
        y = self.y
        #print self.pos
        style = self.style
        kmtop, kmright, kmbottom, kmleft = style['key_margin_hint']
        
        for line_nb in range(1,layout_size_h+1):
            layout_geometry['LINE_'+ str(line_nb) ] = []
            for key in layout_geometry[ 'LINE_HINT_'+str(line_nb) ] :
                x_hint, y_hint = key[0]
                l_hint, h_hint = key[1]
                kx = x + x_hint * l
                ky = y + y_hint * h
                kl = l_hint * l
                kh = h_hint * h
                
                #now adjust, considering the key margin
                kmtop1 = kmtop * kh
                kmright1 = kmright * kl
                kmbottom1 = kmbottom * kh
                kmleft1 = kmleft * kl
                kx = int(kx + kmleft1)
                ky = int(ky + kmbottom1)
                kl = int(kl - kmleft1 - kmright1)
                kh = int(kh - kmbottom1 - kmtop1)
                
                pos = (kx,ky)
                size = (kl,kh)
                layout_geometry['LINE_'+str(line_nb)].append( [pos,size] ) 
                #print pos, size 
        
        self.layout_geometry = layout_geometry 

    def draw_keys(self):
        
        layout = self.layout
        layout_size_l, layout_size_h = layout['SIZE']
        layout_geometry = self.layout_geometry
        mode = self.mode
        #style
        a,b,c = self.style['background_color']
        d,e,f = self.style['key_color'] 
        
        #draw background
        pos = (self.x,self.y)
        l,h = self.get_size()
        #pos,size = self.bbox
        texture = Image( self.style['background_texture_path'] ).texture #transparent 'images/border17.png' plain 'images/border6.png'
        with self.canvas :
                    Color(a, b, c)        
                    #BorderImage(texture = texture, pos = pos, size =(l,h),border = (5,5,5,5))
                    Rectangle(texture = texture, pos = pos, size =(l,h) )
        #seperate drawing the keys and the fonts to avoid
        #reloading the texture each time

        #first draw keys without the font
        texture = Image(self.style['key_texture_path']).texture
        for line_nb in range(1,layout_size_h+1):
            for key in layout_geometry[ 'LINE_'+str(line_nb) ] :
                pos = key[0]
                size = key[1]       
                with self.canvas :
                    Color(d, e, f)        
                    #BorderImage(texture=texture, pos = pos, size =size, border = (2,2,2,2) ) #source=self.style['key_texture_path']
                    Rectangle(texture=texture, pos = pos, size =size )

        #then draw the text
        #calculate font_size
        font_size = int(l)/46
        self.font_size = font_size 
        #draw
        for line_nb in range(1,layout_size_h+1):
            key_nb = 0
            for key in layout_geometry[ 'LINE_'+str(line_nb) ] :
                pos = key[0]
                size = key[1]
                #print pos, size
                #retrieve the relative text
                text = layout[mode +'_'+ str(line_nb)][key_nb][0]
                #print text
                l = Label(text=text, font_size = font_size)
                l.pos = pos
                l.size = size
                self.add_widget( l )
                key_nb +=1 
          
    def draw_active_keys(self):

        active_keys = self.active_keys # { touch_id : (line_nb,index) }
        layout_geometry = self.layout_geometry
        layout = self.layout
        mode = self.mode
        d,e,f = self.style['key_color_active']
        texture_path = self.style['key_texture_path_active']
        caps_lock_key = self.caps_lock_key# [layout[mode +'_'+ str(3)][0],(3,0)] 
  
        #draw keys with the background and font at once
        keys = active_keys
        if self.caps_lock_key_on :
            keys[-1] = caps_lock_key
        else : 
            if -1 in keys.keys() : del keys[-1]
        
        texture = Image(texture_path).texture
        
        for i in keys.keys() :
            line_nb,index = keys[i]
            pos,size = layout_geometry[ 'LINE_'+str(line_nb) ][index]
              
            with self.active_keys_layer.canvas :
                Color(d, e, f)        
                Rectangle(texture = texture, pos = pos, size =size)
            
            text = layout[mode +'_'+ str(line_nb)][index][0]
            l = Label(text=text, font_size = self.font_size)
            l.pos = pos
            l.size = size
            self.active_keys_layer.add_widget( l )
        
    def send(self,key_data):             
        character, b, c, d = key_data
        #print character
        target = self.target 
        
        if key_data[2] is 'None':
            target.insert_text(key_data[0])
        else : 
            target._key_down(key_data,repeat=False)  

    def get_key_at_pos(self,pos):
            x,y = self.get_local_pos(pos)
            l,h = self.get_size()
            x_hint = x/l
            y_hint = y/h
            #focus on the surface without margins
            layout_geometry = self.layout_geometry
            layout_size_l, layout_size_h = self.layout['SIZE']
            mtop, mright, mbottom, mleft = self.style['margin_hint'] 
            
            #get the line of the layout
            e_height = h - (mbottom+mtop) * h #efficient height in pixels
            line_height = e_height / layout_size_h#line height in px
            y = y - mbottom *h
            line_nb = int(y / line_height)+1
            
            if line_nb > layout_size_h : line_nb = layout_size_h
            if line_nb < 1 : line_nb = 1
            
            #get the key within the line
            key_index = ''
            current_key_index =0
            for key in layout_geometry['LINE_HINT_'+str(line_nb)] :
                if x_hint >= key[0][0] and x_hint < key[0][0] + key[1][0] :
                    key_index = current_key_index
                    break   
                else : current_key_index +=1
            if key_index == '' : return None
            #get the full caracter
            key = self.layout['%s_%d' % (self.mode, line_nb)][key_index]
            
            return [key,(line_nb,key_index)] 

    def touch_is_in_margin(self,pos):
        l,h = self.get_size()
        mtop, mright, mbottom, mleft = self.style['margin_hint']
        
        x,y = pos
        x_hint = x/l
        y_hint = y/h

        if ( x_hint > mleft and x_hint < 1. - mright) and (y_hint > mbottom and y_hint < 1. - mtop ) :
            return False
        else : return True

    def get_local_pos(self, pos):
        #return self.to_local(pos[0],pos[1])
        x, y = pos
        x_widget = self.x
        y_widget = self.y
        return (x - x_widget, y - y_widget)
    
    def get_size(self):
        l,h = self.size_k#self.bbox[1]#(700,200)#self.size#
        l = l*self.scale_k
        h = h*self.scale_k
        return (l,h)

    def process_key_on(self, touch):
        
        x,y= touch.pos
        key = self.get_key_at_pos( (x,y) )
        if key == None : return        
        key_data = key[0]
        displayed_char, internal, special_char, size = key_data
        line_nb, key_index = key[1]
        shift = False
 
        #send info to the bus
        if not special_char in ['shift_L','shift_R','capslock','layout'] :
            self.send(key_data)
        
        self.active_keys[touch.id] = key[1]  # touch.id : (line_nb, key_index)
        
        #for caps lock or shift only :
        if special_char is not 'None':
            if special_char == 'capslock' : # CAPS LOCK
                self.caps_lock_key = key[1]
                if not self.caps_lock_key_on : 
                    self.caps_lock_key_on = True
                else : 
                    self.caps_lock_key_on = False
                ak = self.active_keys.values()
                if self.shift_keyL not in ak and self.shift_keyL not in ak:
                    self.switch_mode()
            elif special_char == 'shift_L' :
                self.shift_keyL = key[1]
                shift = True
            elif special_char == 'shift_R' :
                self.shift_keyR = key[1]
                shift = True
            elif special_char == 'layout' :
                self.change_layout() 
            if shift and not self.caps_lock_key_on :    
                self.switch_mode()
         
        self.refresh_active_keys_layer()
 
    def process_key_up(self, touch):
        shift_keyL = self.shift_keyL
        shift_keyR = self.shift_keyR 
        id = touch.id

        if id in self.active_keys.keys(): 
            #specific case of the shift_key
            if (self.active_keys[id] in [shift_keyL,shift_keyR]) and not self.caps_lock_key_on : 
                self.switch_mode()
            del(self.active_keys[id]) 
            self.refresh_active_keys_layer()
    
    def collides_inscale(self, pos):
        x,y = self.get_local_pos(pos)
        l,h = self.get_size()
        if x <= l and y <= h : return True
        else : return False
                     
    def on_touch_down(self, touch):
        #check if one key is down, and if yes which one ?
        if not self.collides_inscale(touch.pos): return
        x,y = self.get_local_pos(touch.pos)
        
        if not self.touch_is_in_margin( (x,y) ) :
            self.process_key_on(touch)
            inmargin = False
        else : inmargin = True
        self.touches[touch.id] = (touch, inmargin)    
        super(VKeyboard, self).on_touch_down( touch )
    
    def on_touch_move(self,touch):
        #super(VKeyboard, self).on_touch_move( touch )
        #if not self.collides_inscale(touch.pos): return
        x,y = touch.pos
        if self.position_lock == True and not self.touches[touch.id][1] : 
            return 
        else :
            touches = self.touches
            #if touch in self._touches and touch.grab_current == self:
            #    self.transform_with_touch(touch)
            if len(touches) == 1:
                #translate 
                self.x += touch.dx
                self.y += touch.dy
            if len(touches) == 2:
                #rescale
                list = touches.keys()
                a = list[0]
                b = list[1]
                if touches[a][1] and touches[b][1]:
                    old_scale = self.old_scale
                    new_scale = touches[a][0].distance( touches[b][0] ) / self.width
                    if old_scale > 0 : 
                        self.scale_k += (new_scale - old_scale) #* 0.5
                    self.old_scale = new_scale          
            
            self.refresh(False)

        #store the current touch with original position    
        origin_in_margin = self.touches[touch.id][1] 
        self.touches[touch.id] = (touch, origin_in_margin) 
        super(VKeyboard, self).on_touch_move( touch )
        
            
    def on_touch_up(self, touch):
        #if not self.collides_inscale(touch.pos): return
        self.process_key_up(touch)       
        if touch.id in self.touches.keys(): 
            del self.touches[touch.id]
        if len(self.touches)<2 : 
            self.old_scale = 0  
        super(VKeyboard, self).on_touch_up( touch ) 

    def move_to_target(self):
        '''Slowly go to the target position, slightly under'''
        target = self.target
        x,y = target.center
        print x,y


