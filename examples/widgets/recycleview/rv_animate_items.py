'''How to use Animation with RecycleView items?

In case you really want to use the Animation class with RecycleView, you'll
likely encounter an issue, as widgets are moved around, they are used to
represent different items, so an animation on a specific item is going to
affect others, and this will lead to really confusing results.

This example works around that by creating a "proxy" widget for the animation,
and, by putting it in the data, allowing the displayed widget to mimic the
animation. As the item always refers to its proxy, whichever widget is used to
display the item will keep in sync with the animation.

'''
from copy import copy

from kivy.app import App
from kivy.clock import triggered
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.uix.button import Button
from kivy.properties import (
    ObjectProperty, ListProperty
)


KV = '''
<Item>:
    index: None
    animation_proxy: None
    on_release: app.animate_item(self.index)


RecycleView:
    data: app.data
    viewclass: 'Item'
    RecycleBoxLayout:
        orientation: 'vertical'
        size_hint: 1, None
        height: self.minimum_height
        default_size_hint: 1, None
        default_size: 0, dp(40)
'''


class Item(Button):
    animation_proxy = ObjectProperty(allownone=True)
    _animation_proxy = None

    def update_opacity(self, proxy, opacity):
        # sync one animated property to the value in the proxy
        self.opacity = opacity

    def on_animation_proxy(self, *args):
        """When we create an animation proxy for an item, we need to bind to
        the animated property to update our own.
        """
        if self._animation_proxy:
            self._animation_proxy.unbind(opacity=self.update_opacity)

        self._animation_proxy = self.animation_proxy
        if self.animation_proxy:
            # when we are assigned an animation_proxy, sync our properties to
            # the animated version.
            self.opacity = self.animation_proxy.opacity
            self.animation_proxy.bind(opacity=self.update_opacity)
        else:
            # if we lose our animation proxy, we need to reset the animated
            # property to their default values.
            self.opacity = 1


class Application(App):
    data = ListProperty()

    def build(self):
        self.data = [
            {'index': i, 'text': 'hello {}'.format(i), 'animation_proxy': None}
            for i in range(1000)
        ]
        return Builder.load_string(KV)

    # the triggered decorator allows delaying the animation until after the
    # blue effect on the button is removed, to avoid a flash as widgets gets
    # reordered when that happens
    @triggered(timeout=0.05)
    def animate_item(self, index):
        # the animation we actually want to do on the item, note that any
        # property animated here needs to be synchronized from the proxy to the
        # animated widget (in on_animation_proxy and using methods for each
        # animation)
        proxy = Widget(opacity=1)
        item = copy(self.data[index])
        animation = (
            Animation(opacity=0, d=.1, t='out_quad')
            + Animation(opacity=1, d=5, t='out_quad')
        )
        animation.bind(on_complete=lambda *x: self.reset_animation(item))
        item['animation_proxy'] = proxy
        self.data[index] = item
        animation.start(proxy)

    def reset_animation(self, item):
        # animation is complete, widget should be garbage collected
        item['animation_proxy'] = None


if __name__ == "__main__":
    Application().run()
