# This is a "jumping" module, required for python-for-android project
# Because we are putting all the module into the same .so, there can be name
# conflict. We have one conflict with pygame.event and kivy.event => Both are
# python extension and have the same "initevent" symbol. So right now, just
# rename this one.
__all__ = ('EventDispatcher', 'ObjectWithUid', 'Observable')

import kivy._event
__doc__ = kivy._event.__doc__
EventDispatcher = kivy._event.EventDispatcher
ObjectWithUid = kivy._event.ObjectWithUid
Observable = kivy._event.Observable
