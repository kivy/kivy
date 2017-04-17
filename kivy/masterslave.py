'''
MasterSlave
===========

:class:`MasterSlave` is used to make a widget follow or follow opposite
to another widget in terms of size or path it covers on screen. The
widget which is followed can be reffered to as 'master' and the
following widget can be referred to as 'slave'.

To use MasterSlave, follow these steps:

    * Setup a MasterSlave object on two widgets(master and slave)
    * Call the desired follow methods of MasterSlave class with positive
      arguments to follow in direction of master and with negative
      arguments to follow opposite to master


Usage example
-------------
Here a MasterWidget moves on the screen for reasons like animation or
user is dragging. The SlaveWidget here moves according to the
MasterWidget.

We pass value '5' in 'follow_path' method which means the SlaveWidget
moves 1/4 of the distance moved by MasterWidget. Negative values can also
be passed to make SlaveWidget move opposite to MasterWidget.
The default argument is 1

    class MasterWidget(Widget):
        .....
        .....

    class SlaveWidget(Widget):
        .....
        .....

    class Root(Widget):
        .....
        .....
        def method(self):
            .....
            .....
            m = MasterWidget()
            s = SlaveWidget()
            .....
            # widget 'm' is moving on the screen for reasons
            # like animation or the user is dragging
            .....
            ms = MasterSlave(m, s)
            ms . follow_path(4)
        .....
        .....


The follow methods are :-
    * follow_path(path_step_factor) : follows path of MasterWidget,
                                      'path_step_factor' defaults to 1

    * follow_size(size_step_factor) : follows size of MasterWidget,
                                      'size_step_factor' defaults to 1

    * follow_all(path_step_factor, size_step_factor) :
                                      follows both path and size of
                                      MasterWidget, both the arguments
                                      defaults to 1

To stop following the MasterWidget unfollow methods are used

The unfollow methods are :-
    * unfollow_path() : Stop following the MasterWidget's path
    * unfollow_size() : Stop following the MasterWidget's size
    * unfollow_all()  : Stop following both path and size of
                        MasterWidget
'''

from kivy.clock import Clock


class MasterSlave():

    '''Create a MasterSlave definition which can be used to make a
       widget follow another widget's path or size or both

    :Parameters:
        `master_widget'
        'slave_widget'
    '''

    _instances = set()

    def __init__(self, master_widget, slave_widget):
        # initialise
        self.master_widget = master_widget
        self.slave_widget = slave_widget
        self.m_x = master_widget.x
        self.m_y = master_widget.y
        self.m_w = master_widget.width
        self.m_h = master_widget.height

    @property
    def master(self):
        '''Returns the master widget.
        '''
        return self.master_widget

    @property
    def slave(self):
        '''Returns the slave widget.
        '''
        return self.slave_widget

    @property
    def path_step_factor(self):
        '''Returns the step factor of slave for path following.
        '''
        return self.path_step_ftor

    @property
    def size_step_factor(self):
        '''Returns the step factor of slave for size following.
        '''
        return self.size_step_ftor

    #
    # follow methods.............................................
    #

    def follow_path(self, step_ftor=1):
        '''Slave widget starts following path of master widget.
           Negetive 'step_ftor' will make slave follow opposite to master.
        '''
        self._clear_instance()
        self._add_instance()
        self.path_step_ftor = step_ftor
        Clock.schedule_interval(self._update_path, 1 / 60)

    def follow_size(self, step_ftor=1):
        '''Slave widget starts following size of master widget.
           Negative 'step_ftor' will make slave follow opposite to master.
        '''
        self._clear_instance()
        self._add_instance()
        self.size_step_ftor = step_ftor
        Clock.schedule_interval(self._update_size, 1 / 60)

    def follow_all(self, step_ftor_path=1, step_ftor_size=1):
        '''Slave widget starts following both path and size of master
           widget simultaneously.
        '''
        self._clear_instance()
        self._add_instance()
        self.path_step_ftor = step_ftor_path
        self.size_step_ftor = step_ftor_size
        Clock.schedule_interval(self._update_size, 1 / 60)
        Clock.schedule_interval(self._update_path, 1 / 60)

    def unfollow_path(self):
        '''Stop following path of master widget
        '''
        Clock.unschedule(self._update_path)
        self._clear_instance()

    def unfollow_size(self):
        '''Stop following size of master widget
        '''
        Clock.unschedule(self._update_size)
        self._clear_instance()

    def unfollow_all(self):
        '''Stop following both path and size of master widget
        '''
        Clock.unschedule(self._update_path)
        Clock.unschedule(self._update_size)
        self._clear_instance()

    #
    # Private....................................................
    #

    def _add_instance(self):
        MasterSlave._instances.add(self)

    def _clear_instance(self):
        MasterSlave._instances = set()

    def _update_path(self, *args):
        self.slave_widget.x += (self.master_widget.x -
                                self.m_x) / self.path_step_ftor
        self.slave_widget.y += (self.master_widget.y -
                                self.m_y) / self.path_step_ftor
        self.m_x = self.master_widget.x
        self.m_y = self.master_widget.y

    def _update_size(self, *args):
        self.slave_widget.width += (self.master_widget.width -
                                    self.m_w) / self.size_step_ftor
        self.slave_widget.height += (self.master_widget.height -
                                     self.m_h) / self.size_step_ftor
        self.m_w = self.master_widget.width
        self.m_h = self.master_widget.height
