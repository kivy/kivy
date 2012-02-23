.. _pong:

Pong Game Tutorial
==================

.. highlight:: python
    :linenothreshold: 3

.. image:: pong.jpg
    :align: right

.. note:: 

    You can find the entire source code, and source code files for each step in
    the Kivy examples directory under `tutorials/pong/`

.. note:: 

    If you have read the programming guide, and understand both basic Widget
    concepts (:doc:`/guide/firstwidget`) and basic concepts of the kv language
    (:doc:`/guide/kvlang`, :doc:`/guide/designwithkv`), you can probably skip the first 2
    steps and go straight to step 3.

This tutorial will teach you how to write pon using Kivy.  We'll start with
a basic application like the one described in the :ref:`quickstart` and make
it into a playable pong game describing each step along the way.

Here is a check list for things you should know before startingt this tutorial:

* You have a working Kivy installation.  See the :doc:`/installation/installation`
  section for detailed descriptions
* You know how to run a basic Kivy application. See :doc:`/guide/quickstart`
  if you don't.

Ready? Sweet, let's get started!


Step 1 - Getting Started
------------------------

Let's start by getting a really simple Kivy app up and running. Create a
directory for the game and a file named *main.py*


.. include:: ../../../examples/tutorials/pong/steps/step1/main.py
    :literal:

Go ahead and run the application. It should just show a black window at this
point. What we've done is create a very simple Application, which creates an
instance of our ``PongGame`` Widget class and returns it as the root element
for the applications UI. In the next step, we will draw the Pong background
and scores by defining how the ``PongGame widget`` looks.


Step 2 - Some simple graphics
-----------------------------

Creation of pong.kv
~~~~~~~~~~~~~~~~~~~

We will use a .kv file to define the look and feel of the ``PongGame`` class.
Since our :class:`~kivy.app.App` class is called ``PongGameApp``, we can simply create a file
called ``pong.kv`` in the same directory that will be automatically loaded
when the application is run.  So create a new file called ``*pong.kv*`` and add
the following contents.

.. include:: ../../../examples/tutorials/pong/steps/step2/pong.kv
    :literal:

If you run the app now, you should see a vertical bar in the middle, and two
zeros where the player scores will be displayed.

.. note::

    Try to resize the application window and notice what happens.  That's
    right, the entire UI resizes automatically.  The standard behaviour of the
    Window is to resize the root element based on the elements `size_hint`. The
    default Widget size_hont is (1,1), so it will be stretched to full size.
    Since the pos and size of the Rectangle and score labels were defined with
    references to the our PongGame class, these properties will automatically
    update when the corrosponding widget properties change.  Using the Kv
    language gives you automatic property binding. :)
 

Explaning Kv file syntax
~~~~~~~~~~~~~~~~~~~~~~~~

Before going on to the next step, you might want to take a closer look at
the contents of the kv file we just created and figure out what is going on.
If you understand what's happenging, you can probably skip ahead to the next
Step.

On the very first line we have::

    #:kivy 1.0.9
    
This first line is required in every kv file. It should start with ``#:kivy``
followed by a space and the Kivy version it is intended for (So Kivy can make
sure, you have at least the required version, or handle backwards compatibility
later on)

After that, we define one rule that is applied to any PongGame instance::

    <PongGame>:
        ...
    
Like python, kv files use indendtation to define nested blocks. A block defined
with a class name inside the ``<`` and ``>`` charachters is a
:class:`~kivy.uix.widget.Widget` rule, it will be applied to any instance of
the named class. If you replaced ``PongGame`` with Widget in our example, all
Widget instances would have the vertical line and the two Label widgets inside
them for instance.

Inside a Rule section, you can add various bloks to define the style and
contents of the widgets it will be applied to. You can set property values,
child widgets that will be automatically added, or a `canvas` section in
which you can add Graphics instructions that define how the widget itself is
rendered.

The first block inside the ``<PongGame>`` rule we have is a canvas block::

    <PongGame>:
        canvas:
            Rectangle:
                pos: self.center_x - 5, 0
                size: 10, self.height
                
So this canvas block says that the ``PongGame`` widget itself should draw some
graphics primitives.  In this case, we add a Rectangle to the canvas. We set
the pos of the rectangle to be 5 pixels left of the the horizontal center of
the widget itself, and 0 for y. The size of the rectangle is set to 10 pixels
in width, and the widgets height in height. The nice thing about defining the
graphics like this, is that the rendered rectangle will be automatically
updated when the properties of any widgets used in the value expression change.

The last two section we add look pretty simmilar. Each of them adds a Label
widget as a childwidget to the ``PongGame`` widget itself. For now the text on
both of them is just set to *"0"*, we'll have to hook that up to the actual
score once we have the logic for that implemented.  But the labels already
look good, since we set a bigger font_size, and positioned them relatively
to the root widget. The ``root`` keyword can be used inside child block to
refer back to the parent/root widget the rule applies to (``PongGame`` in this
case)::

    <PongGame>:
        ...
        
        Label:
            font_size: 70  
            center_x: root.width / 4
            top: root.top - 50
            text: "0"
            
        Label:
            font_size: 70  
            center_x: root.width * 3 / 4
            top: root.top - 50
            text: "0"
    
Step 3 - Adding a ball
----------------------

Ok, so we have a basic pong arena to play in, but we still need the players and
a ball to pong around.  Let's start with the ball.  We'll add a new `PongBall`
class to create a widget that will be our ball and make it bounce around.

.. note:: 

    We'll just look at the python class and kv rule for PongBall first.
    To make it al usable, and add the ball to the arena, you'll also need to add
    the proper imports and register the `PongBall` class with the widget factory
    so you can add it as a childwidget in the `<PongGame>` rule.  But don't 
    worry, the entire code is listed at the end of this step.

PongBall class
~~~~~~~~~~~~~~

Here is the python code for the PongBall class::
    
    class PongBall(Widget):

        # velocity of the ball on x and y axis
        velocity_x = NumericProperty(0)
        velocity_y = NumericProperty(0)
        
        # referencelist property so we can use ball.velocity as 
        # a shorthand..just like e.g. w.pos for w.x and w.y
        velocity = ReferenceListProperty(velocity_x, velocity_y)
        
        # move function will move the ball one step.  This will
        # be called in equal intervals to animate the ball
        def move(self):
            self.pos = Vector(*self.velocity) + self.pos  
            
            
And here is the kv rule used to draw the ball as a white circle::

    <PongBall>:
        size: 50, 50 
        canvas:
            Ellipse:
                pos: self.pos
                size: self.size      
        
        
To make it all work, you also have to add the imports for the
:doc:`/api-kivy.properties` Property classes used, the
:class:`~kivy.vector.Vector`, and the :class:`~kivy.factory.Factory` singleton.
The factory is used to register your custom classes, so that Kivy knows what
class to instatiate when you use e.g. a custom classname inside a kv rule.
Once that's done, you can add a ``PongBall`` to the ``<PongGame>`` class, just
like we added the Labels before.

Here is the entire updated python code and kv file for this step:

    main.py:
        .. include:: ../../../examples/tutorials/pong/steps/step3/main.py
            :literal:

    pong.kv:
        .. include:: ../../../examples/tutorials/pong/steps/step3/pong.kv
            :literal:


Step 4 - Making the ball move
-----------------------------

Cool, so now we have a ball, and it even has a move function... but it's not
moving yet. Let's fix that.

Scheduling functions on the Clock
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We need the move method of our ball to be called regularly. Luckily Kivy
makes this pretty easy, by prividing letting us schedule function we want
on the :class:`~kivy.clock.Clock` and specify the interval::

    Clock.schedule_interval(game.update, 1.0/60.0)
    
That line for example, would cause the update function of the game object to
be called once every 60th of a second (60 times per second).

Object Properties/References
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We have another problem though.  We'd like to make sure the PongBall has its
move function called regularly, but in our code we don't have any references
to the ball object, since we just added it as a child widget of our ``PongGame``
class inside the kv rule for the ``PongGame`` class.  The only reference to our
game is the one we return in the Applications build method.

Since we're going to have to do more than just move the ball (e.g.
bounce it off the walls and later the players racket), we'll probably need
an update method for our ``PongGame`` class anyways.  And given that we have a
reference to the game object already, we can easily schedule its new update
method when the application gets build::

    class PongGame(Widget):

        def update(self):
            # call ball.move and other stuff
            pass
            
    class PongApp(App):

        def build(self):
            game = PongGame()
            Clock.schedule_interval(game.update, 1.0/60.0)
            return game
            

But that still doesn't help the fact that we don't have a reference to the
``PongBall`` child widget created by the kv rule.  Do fix this, we can add an
ObjectProperty to the PongGame class, and hook it up to the widget created in
the kv rule. Once that's done, we can easily reference the ball property
inside the update method and even make it bounce of the edges::

    class PongGame(Widget):
        ball = ObjectProperty(None)
        
        def update(self):
            self.ball.move()
            
            # bounce off top and bottom
            if (self.ball.y < 0) or (self.ball.top > self.height):
                self.ball.velocity_y *= -1
        
            # bounce off left and right
            if (self.ball.x < 0) or (self.ball.right > self.width):
                self.ball.velocity_x *= -1
                
Don't forget to hook it up in the kv file, by giving the child widget an id
and setting the games property to that id::

    <PongGame>:
        ball: pong_ball
    
        # ... (canvas and Labels)
        
        PongBall:
            id: pong_ball
            center: self.parent.center
    
                
.. note:: 

    At this point everything is hooked up for the ball to bounce around.  If 
    your coding along as we go, you might be wondering why the ball isn't 
    moving anywhere.  We'll the ball's velocity is set to 0 on both x and y.
    In code listing below for the entire source a ``serve_ball`` method is 
    added to the ``PongGame`` class and called in the apps build method.  It sets a
    random x and y velocity for the ball, and also resets the position, so we
    can use it later to reset the ball when a player has scored a point.
    
Here is the entire code for this step:

    main.py:
       .. include:: ../../../examples/tutorials/pong/steps/step4/main.py
        :literal:

    pong.kv:
       .. include:: ../../../examples/tutorials/pong/steps/step4/pong.kv
        :literal:

Step 5 - Adding Players and reacting to touch input
---------------------------------------------------

Sweet, out ball is bouncing around. The only thing missing now are the movable
player rackets and keeping track of the score.  We won't to go over all the
details of creating the class and kv rules again, since those concepts were
already covered in the previous steps.  Instead lets focus on how to move the
Player widgets in response to user input.  You can get the whole code and kv
rules for the ``PongPlayer`` class at the end of this section.

In Kivy, a widget can react to input by implemeting the ``on_touch_down``,
``on_touch_move`` and ``on_touch_up`` methods. By default, the Widget class
implements thes methods by just calling the corropsonding method on all it's
child widgets to pass on the event until one of the children returns True.

Pong is pretty simple, the rackets just need to move up and down. In fact it's
so simple, we don't even really need to have the player widgets handle the
events themselves.  We'll just implement the ``on_touch_move`` function for the
``PongGame`` class and have it set the position of the left or right player based
on whether the touch occured on the left or right side of the screen.

Check the ``on_touch_move`` handler::

    def on_touch_move(self, touch):
        if touch.x < self.width/3:
            self.player1.center_y = touch.y
        if touch.x > self.width - self.width/3:
            self.player2.center_y = touch.y
            
We'll keep the score for each player in a
:class:`~kivy.properties.NumericProperty`. The score labels of the ``PongGame``
are kept updated by changing the static string we had in the kv file before to
the score property of our new ``PongPlayer`` child widgets.  When the ball
get's out of bounce on of the sides, we'll update the score and serve the ball
again by changing the update method in the ``PongGame`` class.  The player
class also implements a bounce_ball method, so that the ball bounces
differently based on where on the racket it hits. Here is the code for the
`PongPlayer` class::

    class PongPaddle(Widget):

        score = NumericProperty(0)
        
        def bounce_ball(self, ball):
            if self.collide_widget(ball):
                speedup  = 1.1
                offset = 0.02 * Vector(0, ball.center_y-self.center_y)
                ball.velocity =  speedup * (offset - ball.velocity)            


And here it is in context. Pretty much done:
    main.py:
       .. include:: ../../../examples/tutorials/pong/steps/step5/main.py
        :literal:

    pong.kv:

       .. include:: ../../../examples/tutorials/pong/steps/step5/pong.kv
        :literal:


Step 6 - Have some fun
----------------------

Well, the pong game is pretty much complete.  If you understood all of the
things that are covered in this turoial, give yourself a pat on the back and
think about how you could improve the game.  Here a are a few ideas of things
you could do:

* Add some nicer graphics / images (hint check out the source property on
  the graphics instructions liek Circle or Rectangle, to set an image as the
  texture for it)

* Make the game end after a certain score.  Maybe once a player has 10
  points, you can display a large "PLAYER 1 WINS" Label and/or add a main menu
  to start, pause and reset the game (hint: chck out the 'Button' and 'Label'
  classes and figure out how to use the `add_widget` & `remove_widget`
  functions form the `Widget` class, to add or remove widgets dynamically.

* Make it a 4 player Pong Game.  Most tablets have Multi-Touch support,
  wouldn't it be cool to have a player on each side and play four people at
  the same time? 

.. note:: 

    You can find the entire source code, and source code files for each step in
    the Kivy examples directory under tutorials/pong/
