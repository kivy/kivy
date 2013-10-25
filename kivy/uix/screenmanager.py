'''
Screen Manager
==============

.. versionadded:: 1.4.0

.. warning::

    This widget is still experimental, and its API is subject to change in a
    future version.

The screen manager is a widget dedicated to managing multiple screens for your
application. The default :class:`ScreenManager` displays only one
:class:`Screen` at a time and uses a :class:`TransitionBase` to switch from one
Screen to another.

Multiple transitions are supported based on changing the screen coordinates /
scale or even performing fancy animation using custom shaders.

Basic Usage
-----------

Let's construct a Screen Manager with 4 named screens. When you are creating
a screen, you absolutely need to give a name to it::

    from kivy.uix.screenmanager import ScreenManager, Screen

    # Create the manager
    sm = ScreenManager()

    # Add few screens
    for i in range(4):
        screen = Screen(name='Title %d' % i)
        sm.add_widget(screen)

    # By default, the first screen added into the ScreenManager will be
    # displayed. You can then change to another screen.

    # Let's display the screen named 'Title 2'
    # A transition will automatically be used.
    sm.current = 'Title 2'

From 1.8.0, you can now switch dynamically to a new screen, change the
transition options and remove the previous one by using
:meth:`ScreenManager.switch_to`::

    sm = ScreenManager()
    screens = [Screen(name='Title {}'.format(i)) for i in range(4)]

    sm.switch_to(screens[0])
    # later
    sm.swith_to(screens[1], direction='right')

The default :data:`ScreenManager.transition` is a :class:`SlideTransition` with
options :data:`~SlideTransition.direction` and
:data:`~TransitionBase.duration`.

Please note that by default, a :class:`Screen` displays nothing: it's just a
:class:`~kivy.uix.relativelayout.RelativeLayout`. You need to use that class as
a root widget for your own screen, the best way being to subclass.

Here is an example with a 'Menu Screen' and a 'Settings Screen'::

    from kivy.app import App
    from kivy.lang import Builder
    from kivy.uix.screenmanager import ScreenManager, Screen

    # Create both screens. Please note the root.manager.current: this is how
    # you can control the ScreenManager from kv. Each screen has by default a
    # property manager that gives you the instance of the ScreenManager used.
    Builder.load_string("""
    <MenuScreen>:
        BoxLayout:
            Button:
                text: 'Goto settings'
                on_press: root.manager.current = 'settings'
            Button:
                text: 'Quit'

    <SettingsScreen>:
        BoxLayout:
            Button:
                text: 'My settings button'
            Button:
                text: 'Back to menu'
                on_press: root.manager.current = 'menu'
    """)

    # Declare both screens
    class MenuScreen(Screen):
        pass

    class SettingsScreen(Screen):
        pass

    # Create the screen manager
    sm = ScreenManager()
    sm.add_widget(MenuScreen(name='menu'))
    sm.add_widget(SettingsScreen(name='settings'))

    class TestApp(App):

        def build(self):
            return sm

    if __name__ == '__main__':
        TestApp().run()


Changing transitions
--------------------

You have multiple transitions available by default, such as:

- :class:`SlideTransition` - slide the screen in/out, from any direction
- :class:`SwapTransition` - implementation of the iOS swap transition
- :class:`FadeTransition` - shader to fade the screen in/out
- :class:`WipeTransition` - shader to wipe the screens from right to left

You can easily switch transitions by changing the
:data:`ScreenManager.transition` property::

    sm = ScreenManager(transition=FadeTransition())

.. note::

    Currently, none of Shader based Transitions use anti-aliasing. This
    is because they use the FBO which doesn't have any logic to handle
    supersampling.
    This is a known issue and we are working on a transparent
    implementation that will give the same results as if it had been rendered on
    screen.

    To be more concrete, if you see sharp edged text during the animation, it's
    normal.

'''

__all__ = ('Screen', 'ScreenManager', 'ScreenManagerException',
    'TransitionBase', 'ShaderTransition', 'SlideTransition', 'SwapTransition',
    'FadeTransition', 'WipeTransition')

from kivy.compat import iteritems
from kivy.logger import Logger
from kivy.event import EventDispatcher
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty, ObjectProperty, AliasProperty, \
        NumericProperty, ListProperty, OptionProperty, BooleanProperty
from kivy.animation import Animation, AnimationTransition
from kivy.uix.relativelayout import RelativeLayout
from kivy.lang import Builder
from kivy.graphics import RenderContext, Rectangle, Fbo, \
        ClearColor, ClearBuffers, BindTexture, PushMatrix, \
        PopMatrix, Translate


class ScreenManagerException(Exception):
    '''Exception for the :class:`ScreenManager`.
    '''
    pass


class Screen(RelativeLayout):
    '''Screen is an element intended to be used with a :class:`ScreenManager`.
    Check module documentation for more information.

    :Events:
        `on_pre_enter`: ()
            Event fired when the screen is about to be used: the entering
            animation is started.
        `on_enter`: ()
            Event fired when the screen is displayed: the entering animation is
            complete.
        `on_pre_leave`: ()
            Event fired when the screen is about to be removed: the leaving
            animation is started.
        `on_leave`: ()
            Event fired when the screen is removed: the leaving animation is
            finished.

    .. versionchanged:: 1.6.0
        Events `on_pre_enter`, `on_enter`, `on_pre_leave` and `on_leave` were
        added.
    '''

    name = StringProperty('')
    '''
    Name of the screen which must be unique within a :class:`ScreenManager`.
    This is the name used for :data:`ScreenManager.current`.

    :data:`name` is a :class:`~kivy.properties.StringProperty` and defaults to
    ''.
    '''

    manager = ObjectProperty(None, allownone=True)
    ''':class:`ScreenManager` object, set when the screen is added to a manager.

    :data:`manager` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None, read-only.
    '''

    transition_progress = NumericProperty(0.)
    '''Value that represents the completion of the current transition, if any
    is occuring.

    If a transition is in progress, whatever the mode, the value will change
    from 0 to 1. If you want to know if it's an entering or leaving animation,
    check the :data:`transition_state`.

    :data:`transition_progress` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0.
    '''

    transition_state = OptionProperty('out', options=('in', 'out'))
    '''Value that represents the state of the transition:

    - 'in' if the transition is going to show your screen
    - 'out' if the transition is going to hide your screen

    After the transition is complete, the state will retain it's last value (in
    or out).

    :data:`transition_state` is an :class:`~kivy.properties.OptionProperty` and
    defaults to 'out'.
    '''

    __events__ = ('on_pre_enter', 'on_enter', 'on_pre_leave', 'on_leave')

    def on_pre_enter(self, *args):
        pass

    def on_enter(self, *args):
        pass

    def on_pre_leave(self, *args):
        pass

    def on_leave(self, *args):
        pass

    def __repr__(self):
        return '<Screen name=%r>' % self.name


class TransitionBase(EventDispatcher):
    '''TransitionBase is used to animate 2 screens within the
    :class:`ScreenManager`. This class acts as a base for other
    implementations like the :class:`SlideTransition` and
    :class:`SwapTransition`.

    :Events:
        `on_progress`: Transition object, progression float
            Fired during the animation of the transition.
        `on_complete`: Transition object
            Fired when the transition is fininshed.
    '''

    screen_out = ObjectProperty()
    '''Property that contains the screen to hide.
    Automatically set by the :class:`ScreenManager`.

    :class:`screen_out` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    screen_in = ObjectProperty()
    '''Property that contains the screen to show.
    Automatically set by the :class:`ScreenManager`.

    :class:`screen_in` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    duration = NumericProperty(.4)
    '''Duration in seconds of the transition.

    :class:`duration` is a :class:`~kivy.properties.NumericProperty` and
    defaults to .4 (= 400ms).

    .. versionchanged:: 1.8.0

        Default duration has been changed from 700ms to 400ms.
    '''

    manager = ObjectProperty()
    ''':class:`ScreenManager` object, set when the screen is added to a manager.

    :data:`manager` is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None, read-only.
    '''

    is_active = BooleanProperty(False)
    '''Indicate whether the transition is currently active or not.

    :data:`is_active` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False, read-only.
    '''

    # privates

    _anim = ObjectProperty(allownone=True)

    __events__ = ('on_progress', 'on_complete')

    def start(self, manager):
        '''(internal) Starts the transition. This is automatically called by
        the :class:`ScreenManager`.
        '''
        if self.is_active:
            raise ScreenManagerException('start() is called twice!')
        self.manager = manager
        self._anim = Animation(d=self.duration, s=0)
        self._anim.bind(on_progress=self._on_progress,
                        on_complete=self._on_complete)

        self.add_screen(self.screen_in)
        self.screen_in.transition_progress = 0.
        self.screen_in.transition_state = 'in'
        self.screen_out.transition_progress = 0.
        self.screen_out.transition_state = 'out'
        self.screen_in.dispatch('on_pre_enter')
        self.screen_out.dispatch('on_pre_leave')

        self.is_active = True
        self._anim.start(self)
        self.dispatch('on_progress', 0)

    def stop(self):
        '''(internal) Stops the transition. This is automatically called by the
        :class:`ScreenManager`.
        '''
        if self._anim:
            self._anim.cancel(self)
            self.dispatch('on_complete')
            self._anim = None
        self.is_active = False

    def add_screen(self, screen):
        '''(internal) Used to add a screen to the :class:`ScreenManager`.
        '''
        self.manager.real_add_widget(screen)

    def remove_screen(self, screen):
        '''(internal) Used to remove a screen from the :class:`ScreenManager`.
        '''
        self.manager.real_remove_widget(screen)

    def on_complete(self):
        self.remove_screen(self.screen_out)

    def on_progress(self, progression):
        pass

    def _on_progress(self, *l):
        progress = l[-1]
        self.screen_in.transition_progress = progress
        self.screen_out.transition_progress = 1. - progress
        self.dispatch('on_progress', progress)

    def _on_complete(self, *l):
        self.is_active = False
        self.dispatch('on_complete')
        self.screen_in.dispatch('on_enter')
        self.screen_out.dispatch('on_leave')
        self._anim = None


class ShaderTransition(TransitionBase):
    '''Transition class that uses a Shader for animating the transition between
    2 screens. By default, this class doesn't assign any fragment/vertex
    shader. If you want to create your own fragment shader for the transition,
    you need to declare the header yourself and include the "t", "tex_in" and
    "tex_out" uniform::

        # Create your own transition. This shader implements a "fading"
        # transition.
        fs = """$HEADER
            uniform float t;
            uniform sampler2D tex_in;
            uniform sampler2D tex_out;

            void main(void) {
                vec4 cin = texture2D(tex_in, tex_coord0);
                vec4 cout = texture2D(tex_out, tex_coord0);
                gl_FragColor = mix(cout, cin, t);
            }
        """

        # And create your transition
        tr = ShaderTransition(fs=fs)
        sm = ScreenManager(transition=tr)

    '''

    fs = StringProperty(None)
    '''Fragment shader to use.

    :data:`fs` is a :class:`~kivy.properties.StringProperty` and defaults to
    None.'''

    vs = StringProperty(None)
    '''Vertex shader to use.

    :data:`vs` is a :class:`~kivy.properties.StringProperty` and defaults to
    None.'''

    def make_screen_fbo(self, screen):
        fbo = Fbo(size=screen.size)
        with fbo:
            ClearColor(0, 0, 0, 1)
            ClearBuffers()
        fbo.add(screen.canvas)
        with fbo.before:
            PushMatrix()
            Translate(-screen.x, -screen.y, 0)
        with fbo.after:
            PopMatrix()
        return fbo

    def on_progress(self, progress):
        self.render_ctx['t'] = progress

    def on_complete(self):
        self.render_ctx['t'] = 1.
        super(ShaderTransition, self).on_complete()

    def add_screen(self, screen):
        self.screen_in.pos = self.screen_out.pos
        self.screen_in.size = self.screen_out.size
        self.manager.real_remove_widget(self.screen_out)

        self.fbo_in = self.make_screen_fbo(self.screen_in)
        self.fbo_out = self.make_screen_fbo(self.screen_out)
        self.manager.canvas.add(self.fbo_in)
        self.manager.canvas.add(self.fbo_out)

        self.render_ctx = RenderContext(fs=self.fs, vs=self.vs,
                use_parent_modelview=True, use_parent_projection=True)
        with self.render_ctx:
            BindTexture(texture=self.fbo_out.texture, index=1)
            BindTexture(texture=self.fbo_in.texture, index=2)
            x, y = self.screen_in.pos
            w, h = self.fbo_in.texture.size
            Rectangle(size=(w, h), pos=(x, y),
                    tex_coords=self.fbo_in.texture.tex_coords)
        self.render_ctx['tex_out'] = 1
        self.render_ctx['tex_in'] = 2
        self.manager.canvas.add(self.render_ctx)

    def remove_screen(self, screen):
        self.manager.canvas.remove(self.fbo_in)
        self.manager.canvas.remove(self.fbo_out)
        self.manager.canvas.remove(self.render_ctx)
        self.manager.real_add_widget(self.screen_in)


class SlideTransition(TransitionBase):
    '''Slide Transition, can be used to show a new screen from any direction:
    left, right, up or down.
    '''

    direction = OptionProperty('left', options=('left', 'right', 'up', 'down'))
    '''Direction of the transition.

    :data:`direction` is an :class:`~kivy.properties.OptionProperty` and
    defaults to 'left'. Can be one of 'left', 'right', 'up' or 'down'.
    '''

    def on_progress(self, progression):
        a = self.screen_in
        b = self.screen_out
        manager = self.manager
        x, y = manager.pos
        width, height = manager.size
        direction = self.direction
        al = AnimationTransition.out_quad
        progression = al(progression)
        if direction == 'left':
            a.y = b.y = y
            a.x = x + width * (1 - progression)
            b.x = x - width * progression
        elif direction == 'right':
            a.y = b.y = y
            b.x = x + width * progression
            a.x = x - width * (1 - progression)
        elif direction == 'up':
            a.x = b.x = x
            a.y = y + height * (1 - progression)
            b.y = y - height * progression
        elif direction == 'down':
            a.x = b.x = manager.x
            b.y = y + height * progression
            a.y = y - height * (1 - progression)

    def on_complete(self):
        self.screen_in.pos = self.manager.pos
        self.screen_out.pos = self.manager.pos
        super(SlideTransition, self).on_complete()


class SwapTransition(TransitionBase):
    '''Swap transition that looks like iOS transition when a new window
    appears on the screen.
    '''

    def add_screen(self, screen):
        self.manager.real_add_widget(screen, 1)

    def on_complete(self):
        self.screen_in.scale = 1.
        self.screen_out.scale = 1.
        self.screen_in.pos = self.manager.pos
        self.screen_out.pos = self.manager.pos
        super(SwapTransition, self).on_complete()

    def on_progress(self, progression):
        a = self.screen_in
        b = self.screen_out
        manager = self.manager

        b.scale = 1. - progression * 0.7
        a.scale = 0.5 + progression * 0.5
        a.center_y = b.center_y = manager.center_y

        al = AnimationTransition.in_out_sine

        if progression < 0.5:
            p2 = al(progression * 2)
            width = manager.width * 0.7
            widthb = manager.width * 0.2
            a.x = manager.center_x + p2 * width / 2.
            b.center_x = manager.center_x - p2 * widthb / 2.
        else:
            if self.screen_in is self.manager.children[-1]:
                self.manager.real_remove_widget(self.screen_in)
                self.manager.real_add_widget(self.screen_in)
            p2 = al((progression - 0.5) * 2)
            width = manager.width * 0.85
            widthb = manager.width * 0.2
            a.x = manager.x + width * (1 - p2)
            b.center_x = manager.center_x - (1 - p2) * widthb / 2.


class WipeTransition(ShaderTransition):
    '''Wipe transition, based on a fragment Shader.
    '''

    WIPE_TRANSITION_FS = '''$HEADER$
    uniform float t;
    uniform sampler2D tex_in;
    uniform sampler2D tex_out;

    void main(void) {
        vec4 cin = texture2D(tex_in, tex_coord0);
        vec4 cout = texture2D(tex_out, tex_coord0);
        gl_FragColor = mix(cout, cin, clamp((-1.5 + 1.5*tex_coord0.x + 2.5*t),
            0.0, 1.0));
    }
    '''
    fs = StringProperty(WIPE_TRANSITION_FS)


class FadeTransition(ShaderTransition):
    '''Fade transition, based on a fragment Shader.
    '''

    FADE_TRANSITION_FS = '''$HEADER$
    uniform float t;
    uniform sampler2D tex_in;
    uniform sampler2D tex_out;

    void main(void) {
        vec4 cin = vec4(texture2D(tex_in, tex_coord0.st));
        vec4 cout = vec4(texture2D(tex_out, tex_coord0.st));
        vec4 frag_col = vec4(t * cin) + vec4((1.0 - t) * cout);
        gl_FragColor = frag_col;
    }
    '''
    fs = StringProperty(FADE_TRANSITION_FS)


class ScreenManager(FloatLayout):
    '''Screen manager. This is the main class that will control your
    :class:`Screen` stack and memory.

    By default, the manager will show only one screen at a time.
    '''

    current = StringProperty(None)
    '''Name of the screen currently shown, or the screen to show.

  ::

        from kivy.uix.screenmanager import ScreenManager, Screen

        sm = ScreenManager()
        sm.add_widget(Screen(name='first'))
        sm.add_widget(Screen(name='second'))

        # By default, the first added screen will be shown. If you want to
        # show another one, just set the 'current' property. 
        sm.current = 'second'
    '''

    transition = ObjectProperty(SlideTransition(), baseclass=TransitionBase)
    '''Transition object to use for animating the screen that will be hidden
    and the screen that will be shown. By default, an instance of
    :class:`SlideTransition` will be given.

    For example, if you want to change to a :class:`WipeTransition`::

        from kivy.uix.screenmanager import ScreenManager, Screen,
        WipeTransition

        sm = ScreenManager(transition=WipeTransition())
        sm.add_widget(Screen(name='first'))
        sm.add_widget(Screen(name='second'))

        # by default, the first added screen will be shown. If you want to
        # show another one, just set the 'current' property.
        sm.current = 'second'

    .. versionchanged:: 1.8.0

        Default transition has been changed from :class:`SwapTransition` to
        :class:`SlideTransition`.
    '''

    screens = ListProperty()
    '''List of all the :class:`Screen` widgets added. You must not change the
    list manually. Use :meth:`Screen.add_widget` instead.

    :data:`screens` is a :class:`~kivy.properties.ListProperty` and defaults to
    [], read-only.
    '''

    current_screen = ObjectProperty(None)
    '''Contains the currently displayed screen. You must not change this
    property manually, use :data:`current` instead.

    :data:`current_screen` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None, read-only.
    '''

    def _get_screen_names(self):
        return [s.name for s in self.screens]

    screen_names = AliasProperty(_get_screen_names,
            None, bind=('screens', ))
    '''List of the names of all the :class:`Screen` widgets added. The list
    is read only.

    :data:`screens_names` is an :class:`~kivy.properties.AliasProperty` and
    is read-only. It is updated if the screen list changes or the name
    of a screen changes.
    '''

    def __init__(self, **kwargs):
        super(ScreenManager, self).__init__(**kwargs)
        self.bind(pos=self._update_pos)

    def _screen_name_changed(self, screen, name):
        self.property('screen_names').dispatch(self)
        if screen == self.current_screen:
            self.current = name

    def add_widget(self, screen):
        if not isinstance(screen, Screen):
            raise ScreenManagerException(
                    'ScreenManager accepts only Screen widget.')
        if screen.manager:
            raise ScreenManagerException(
                    'Screen already managed by another ScreenManager.')
        screen.manager = self
        screen.bind(name=self._screen_name_changed)
        self.screens.append(screen)
        if self.current is None:
            self.current = screen.name

    def remove_widget(self, *l):
        screen = l[0]
        if not isinstance(screen, Screen):
            raise ScreenManagerException(
                    'ScreenManager uses remove_widget only to remove' +
                    'screens added via add_widget! use real_remove_widget.')

        if not screen in self.screens:
            return
        if self.current_screen == screen:
            other = next(self)
            if other:
                self.current = other
        screen.manager = None
        screen.unbind(name=self._screen_name_changed)
        self.screens.remove(screen)

    def real_add_widget(self, *l):
        # ensure screen is removed from it's previous parent before adding'
        if l[0].parent:
            l[0].parent.remove_widget(l[0])
        super(ScreenManager, self).add_widget(*l)

    def real_remove_widget(self, *l):
        super(ScreenManager, self).remove_widget(*l)

    def on_current(self, instance, value):
        screen = self.get_screen(value)
        if not screen:
            return
        if screen == self.current_screen:
            return

        self.transition.stop()

        previous_screen = self.current_screen
        self.current_screen = screen
        if previous_screen:
            self.transition.screen_in = screen
            self.transition.screen_out = previous_screen
            self.transition.start(self)
        else:
            screen.pos = self.pos
            self.real_add_widget(screen)
            screen.dispatch('on_pre_enter')
            screen.dispatch('on_enter')

    def get_screen(self, name):
        '''Return the screen widget associated with the name or raise a
        :class:`ScreenManagerException` if not found.
        '''
        matches = [s for s in self.screens if s.name == name]
        num_matches = len(matches)
        if num_matches == 0:
            raise ScreenManagerException('No Screen with name "%s".' % name)
        if num_matches > 1:
            Logger.warn('Multiple screens named "%s": %s' % (name, matches))
        return matches[0]

    def has_screen(self, name):
        '''Return True if a screen with the `name` has been found.

        .. versionadded:: 1.6.0
        '''
        return bool([s for s in self.screens if s.name == name])

    def __next__(self):
        '''Return the name of the next screen from the screen list.
        '''
        screens = self.screens
        if not screens:
            return
        try:
            index = screens.index(self.current_screen)
            index = (index + 1) % len(screens)
            return screens[index].name
        except ValueError:
            return

    def next(self):
        ''' Py2K backwards compatability without six or other lib'''
        return self.__next__()

    def previous(self):
        '''Return the name of the previous screen from the screen list.
        '''
        screens = self.screens
        if not screens:
            return
        try:
            index = screens.index(self.current_screen)
            index = (index - 1) % len(screens)
            return screens[index].name
        except ValueError:
            return

    def switch_to(self, screen, **options):
        '''Add a new screen to the ScreenManager and switch to it. The previous
        screen will be removed from the children. `options` are the
        :data:`transition` options that will be changed before the animation
        happens.

        If no previous screens are available, the screen will be used as the
        main one::

            sm = ScreenManager()
            sm.switch_to(screen1)
            # later
            sm.switch_to(screen2, direction='left')
            # later
            sm.switch_to(screen3, direction='right', duration=1.)

        If any animation is in progress, it will be stopped and replaced by
        this one: you should avoid this because the animation will just look
        weird. Use either :meth:`switch` or :data:`current` but not both.

        The `screen` name will be changed if there is any conflict with the
        current screen.

        .. versionadded: 1.8.0
        '''
        assert(screen is not None)

        if not isinstance(screen, Screen):
            raise ScreenManagerException(
                    'ScreenManager accepts only Screen widget.')

        # stop any transition that might be happening already
        self.transition.stop()

        # ensure the screen name will be unique
        if screen not in self.children:
            if self.has_screen(screen.name):
                screen.name = self._generate_screen_name()

        # change the transition options
        for key, value in iteritems(options):
            setattr(self.transition, key, value)

        # add and leave if we are set as the current screen
        self.add_widget(screen)
        if self.current_screen is screen:
            return

        old_current = self.current_screen

        def remove_old_screen(transition):
            if old_current in self.children:
                self.remove_widget(old_current)
            transition.unbind(on_complete=remove_old_screen)
        self.transition.bind(on_complete=remove_old_screen)

        self.current = screen.name

    def _generate_screen_name(self):
        i = 0
        while True:
            name = '_screen{}'.format(i)
            if not self.has_screen(name):
                return name
            i += 1

    def _update_pos(self, instance, value):
        for child in self.children:
            if self.transition.is_active and \
                (child == self.transition.screen_in or
                child == self.transition.screen_out):
                    continue
            child.pos = value

    def on_touch_down(self, touch):
        if self.transition.is_active:
            return False
        return super(ScreenManager, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.transition.is_active:
            return False
        return super(ScreenManager, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.transition.is_active:
            return False
        return super(ScreenManager, self).on_touch_up(touch)

if __name__ == '__main__':
    from kivy.app import App
    from kivy.uix.button import Button
    Builder.load_string('''
<Screen>:
    canvas:
        Color:
            rgb: .2, .2, .2
        Rectangle:
            size: self.size

    GridLayout:
        cols: 2
        Button:
            text: 'Hello world'
        Button:
            text: 'Hello world'
        Button:
            text: 'Hello world'
        Button:
            text: 'Hello world'
''')

    class TestApp(App):

        def change_view(self, *l):
            #d = ('left', 'up', 'down', 'right')
            #di = d.index(self.sm.transition.direction)
            #self.sm.transition.direction = d[(di + 1) % len(d)]
            self.sm.current = next(self.sm)

        def remove_screen(self, *l):
            self.sm.remove_widget(self.sm.get_screen('test1'))

        def build(self):
            root = FloatLayout()
            self.sm = sm = ScreenManager(transition=SwapTransition())

            sm.add_widget(Screen(name='test1'))
            sm.add_widget(Screen(name='test2'))

            btn = Button(size_hint=(None, None))
            btn.bind(on_release=self.change_view)

            btn2 = Button(size_hint=(None, None), x=100)
            btn2.bind(on_release=self.remove_screen)

            root.add_widget(sm)
            root.add_widget(btn)
            root.add_widget(btn2)
            return root

    TestApp().run()
