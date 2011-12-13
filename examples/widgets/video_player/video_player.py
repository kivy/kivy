from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock

from kivy.uix.widget import Widget
from kivy.uix.video import Video
from kivy.uix.button import Button
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, \
    BooleanProperty, DictProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.progressbar import ProgressBar

from super_button import SuperButton

class SuperButton2(SuperButton):
    def on_press(self):
        pass
    def on_release(self):
        pass  

class VideoPlayer(Widget):

    app = ObjectProperty( None )
    source = StringProperty('')
    hide_buttons_time_out = NumericProperty(7)
    play = BooleanProperty( False )
    options = DictProperty( {'eos':'loop'} )

    def __init__(self,**kwargs) :
            super(VideoPlayer,self).__init__(**kwargs)

            #new events
            self.register_event_type('on_mute')
            self.register_event_type('on_unmute')
            self.register_event_type('on_start')
            self.register_event_type('on_stop')
            self.register_event_type('on_fullscreen')
            self.register_event_type('on_leave_fullscreen')
            
            self.video = Video(source = self.source, play=self.play, options = self.options , size_hint = (1,1))
            #delay to load the video before launching it
            Clock.schedule_once(self.start,0.2)
            Clock.schedule_once(self.stop,2.4)             
            
            #buttons box
            self.buttons = BoxLayout(orientation = 'horizontal', size_hint = (None, None), size = (self.video.width, 30 ) )
            self.buttons.padding = 5 
            self.buttons.spacing = 5

            #play button
            self.play_button = SuperButton2(text ='', background_normal= 'style/1318898242_media-play.png', background_down= 'video_player/style/1318898242_media-play.png', size_hint = (None, None), size = (20, 20) )
            self.play_button.bind( on_press = self.start_stop_button )
            self.buttons.add_widget( self.play_button )
            #sound button
            self.sound_button = SuperButton2(text ='', background_normal = 'style/1318898261_media-volume-0.png', background_down = 'video_player/style/1318898261_media-volume-0.png', size_hint = (None, None), size = (20, 20) )
            self.sound_button.bind( on_press = self.mute_unmute_button )
            self.buttons.add_widget( self.sound_button )
            #fullscreen 
            self.fullscreen_button = SuperButton(text ='', background_normal = 'style/fullscreen-logo.png', background_down = 'style/fullscreen-logo.png', size_hint = (None, None), size = (20, 20) )
            self.fullscreen_button.bind(on_press = self.fullscreen_button_down )
            self.buttons.add_widget( self.fullscreen_button )
            #duration bar
            self.duration = -1
            self.progress_bar = ProgressBar( size_hint = (1, 1)  )
            self.progress_bar.bind(on_touch_move = self.move_to_position)
            self.buttons.add_widget( self.progress_bar )
            #manage appearance counter
            self.last_touch_down_time = 0
            #fullscreen status
            self.full_screen = False          

            #main play button
            self.main_play_button = SuperButton(text ='', background_normal= 'style/A-play-T3.png', size_hint = (None, None), size = (50, 50) )
            self.main_play_button.bind( on_press = self.start )
            self.add_widget( self.main_play_button )
                      
            #refresh bar position and size
            Clock.schedule_interval(self.refresh_player,0.005)    

            self.add_widget(self.video)

    def start_stop_button(self,a) :
            #actually does start and stop (both functions on same button)
            m = self.video 
            if m.play == False :
                self.start(a)
            else :
                self.stop(a) 

    def start(self, a):
        self.video.play = True
        self.play_button.source = 'style/1318898221_media-stop.png'
        self.remove_widget( self.main_play_button )
        self.dispatch('on_start')

    def stop(self, a):
        self.video.play=False
        self.play_button.source = 'style/1318898242_media-play.png'
        self.add_widget( self.main_play_button )
        self.dispatch('on_stop')

    def mute_unmute_button(self,a):
        if self.video.volume == 1:
            self.mute(a)        
        else :     
            self.unmute(a)    

    def mute(self, a):
        self.video.volume = 0
        self.sound_button.source = 'style/1318898286_media-volume-3.png'
        self.dispatch('on_mute')    

    def unmute(self, a):
        self.video.volume = 1
        self.sound_button.source = 'style/1318898261_media-volume-0.png'
        self.dispatch('on_unmute')

    def fullscreen_button_down(self, a):
        if self.full_screen == False:
            self.fullscreen(1)
        else :
            self.leave_fullscreen(1)

    def fullscreen(self, a):
        self.full_screen = True
        self.dispatch('on_fullscreen')
        self.parent.fullscreen()
    
    def leave_fullscreen(self,a):
        self.full_screen = False
        self.dispatch('on_leave_fullscreen')
        self.parent.leave_fullscreen()  

    def refresh_player(self, a):
        #self.size = self.app.p.size
        if self.duration in [-1,1,0] :
            self.duration = self.video.duration
            self.progress_bar.max = int(self.duration)
        self.buttons.pos = self.pos
        self.buttons.width = self.width
        self.progress_bar.width = self.width
        self.video.pos = self.pos
        self.video.size = self.size
        self.progress_bar.value = self.video.position
        self.main_play_button.center = self.video.center

    def on_touch_down(self, touch):
        super(VideoPlayer,self).on_touch_down(touch)
        self.last_touch_down_time = Clock.get_time()
        #display bar and buttons
        self.show_buttons()

    def hide_buttons(self,a):
        delta = Clock.get_time() - self.last_touch_down_time
        if delta >= (self.hide_buttons_time_out - 0.02) : 
            self.remove_widget(self.buttons)

    def show_buttons(self):
        self.remove_widget(self.buttons)
        self.add_widget(self.buttons)
        Clock.schedule_once(self.hide_buttons, self.hide_buttons_time_out)

    def move_to_position(self, a, touch):
        return
        x = touch.x
        x_hint = x / self.progress_bar.width
        self.video.play = False
        self.video.position = x_hint * self.duration
        self.video.play = True
    
    def on_mute(self):
        pass

    def on_unmute(self):
        pass

    def on_start(self):
        pass

    def on_stop(self):
        pass

    def on_fullscreen(self):
        pass

    def on_leave_fullscreen(self):
        pass  

         
from kivy.uix.scatter import Scatter        
class AppView(Scatter):
    app = ObjectProperty(None)
    properties_before_fullscreen = DictProperty( {} )  

    def __init__(self, **kwargs):
        super(AppView, self).__init__(**kwargs)

        self.p = VideoPlayer(source = '../softboy.avi', size_hint = (1,1), size = (300,200), app =self )
        self.add_widget( self.p)

    def adjust_target_angle(self, target_angle, current_angle):
        #avoid looping while rotating
        a = target_angle
        b = current_angle
        #flip 360 degrees when smallest angle is negative
        smallest_angle = min( (180 - abs(a - b), abs(a - b)) )
        if a > b : r=1
        else : r=-1
        if smallest_angle <0 : 
            a = a - r*360
        return a 
        
    def fullscreen(self):        
        self.properties_before_fullscreen = {'pos':self.pos, 'size':self.p.size, 'rotation':self.rotation, 'scale':self.scale}

        rotation = self.adjust_target_angle( 0, self.rotation )
        duration =2
        anim = Animation(pos = (0,0), rotation = rotation, duration= duration)
        anim2 = Animation(size = self.get_root_window().size, duration = duration)
        anim.start(self)
        anim2.start(self.p)

    def leave_fullscreen(self):
        p = self.properties_before_fullscreen

        rotation = self.adjust_target_angle( p['rotation'], self.rotation ) 
        duration =2
        anim = Animation(pos = p['pos'], rotation = rotation, duration = duration)          
        anim.start(self)
        anim2 = Animation(size = p['size'], duration = duration)          
        anim2.start(self.p)


class PlayerApp(App):

    def build(self):
        self.p = AppView( app =self, do_scale = False )
        return self.p    


if __name__ in ('__android__', '__main__'):
    PlayerApp().run()
