'''
Widget animation
================

This example demonstrates creating and applying a multi-part animation to
a button widget. You should see a button labeled 'plop' that will move with
an animation when clicked.
'''

import kivy
kivy.require('1.0.7')

from kivy.animation import Animation
from kivy.app import App
from kivy.uix.button import Button


class TestApp(App):
    
    def __init__(self, **kwargs):
        super(TestApp, self).__init__(**kwargs)
        self.animation_duration = 1  # Default value
        
    def animate(self, instance):
        # Create an animation object. This object could be stored
        # and reused each call or reused across different widgets.
        # += is a sequential step, while &= is in parallel
        animation = Animation(pos=(100, 100), t='out_bounce', duration=self.animation_duration)
        animation += Animation(pos=(200, 100), t='out_bounce', duration=self.animation_duration)
        animation &= Animation(size=(500, 500), duration=self.animation_duration)
        animation += Animation(size=(100, 50), duration=self.animation_duration)

        # Apply the animation on the button, passed in the "instance" argument
        # Notice that default 'click' animation (changing the button
        # color while the mouse is down) is unchanged.
        animation.start(instance)

    def build(self):
        from kivy.uix.floatlayout import FloatLayout
        from kivy.uix.boxlayout import BoxLayout
        
        root = FloatLayout()
        
        # Main button
        main_button = Button(size_hint=(None, None), text='plop',
                         pos=(50, 50), size=(100, 50),
                         on_press=self.animate)
        
        # Control buttons
        controls = BoxLayout(size_hint=(None, None), size=(300, 50),
                            pos=(100, 10), orientation='horizontal')
        
        reset_btn = Button(text='Reset', on_press=self.reset_position)
        speed_btn = Button(text='Fast', on_press=self.change_speed)
        
        controls.add_widget(reset_btn)
        controls.add_widget(speed_btn)
        
        root.add_widget(main_button)
        root.add_widget(controls)
        
        self.main_button = main_button  # Save reference for reset
        return root

    def reset_position(self, instance):
        # Reset the position of the main button
        anim = Animation(pos=(50, 50), size=(100, 50), duration=0.3)
        anim.start(self.main_button)

    def change_speed(self, instance):
        # Change animation speed
        self.animation_duration = 0.2 if self.animation_duration == 1 else 1
        instance.text = 'Slow' if self.animation_duration == 1 else 'Fast'


if __name__ == '__main__':
    TestApp().run()
