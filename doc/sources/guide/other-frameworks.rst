.. _other_frameworks:

Integrating with other Frameworks
=================================

.. versionadded:: 1.0.8

Using Twisted inside Kivy
-------------------------

.. note::
    You can use the `kivy.support.install_twisted_reactor` function to
    install a twisted reactor that will run inside the kivy event loop.

    Any arguments or keyword arguments passed to this function will be
    passed on the threadedselect reactors interleave function. These
    are the arguments one would usually pass to twisted's reactor.startRunning

.. warning::
    Unlike the default twisted reactor, the installed reactor will not handle
    any signals unless you set the 'installSignalHandlers' keyword argument
    to 1 explicitly.  This is done to allow kivy to handle the signals as
    usual, unless you specifically want the twisted reactor to handle the
    signals (e.g. SIGINT).



The kivy examples include a small example of a twisted server and client.
The server app has a simple twisted server running and logs any messages.
The client app can send messages to the server and will print its message
and the response it got. The examples are based mostly on the simple Echo
example from the twisted docs, which you can find here:

- https://twistedmatrix.com/documents/current/core/examples/

To try the example, run echo_server_app.py first, and then launch
echo_client_app.py.  The server will reply with simple echo messages to
anything the client app sends when you hit enter after typing something
in the textbox.

Server App
~~~~~~~~~~

.. include:: ../../../examples/frameworks/twisted/echo_server_app.py
   :literal:

Client App
~~~~~~~~~~

.. include:: ../../../examples/frameworks/twisted/echo_client_app.py
   :literal:

