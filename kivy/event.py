# This is a "jumping" module, required for python-for-android project
# Because we are putting all the module into the same .so, their can be name
# conflict. We have one conflict with pygame.event and kivy.event => Both are
# python extension and have the same "initevent" symbol. So right now, just
# rename this one.
__all__ = ('EventDispatcher', )

import kivy._event
__doc__ = kivy._event.__doc__
EventDispatcher = kivy._event.EventDispatcher

