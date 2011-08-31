.. _other_frameworks

Integrating with other Frameworks
=================================

Using Twisted inside Kivy
-------------------------
You can use the `kivy.support.install_twisted_reactor` function to
install a twisted reactor that will run inside the kivy event loop.

Any arguments or keyword arguments passed to this function will be
passed on the the threadedselect reactors interleave function, these
are the arguments one would usually pass to twisted's reactor.startRunning

.. warning::
Unlike the default twisted reactor, the installed reactor will not handle
any signals unnless you set the 'installSignalHandlers' keyword argument
to 1 explicitly.  This is done to allow kivy to handle teh signals as
usual, unless you specifically want the twisted reactor to handle the
signals (e.g. SIGINT).

Here is a brief example kivy application that has a twisted server running
inside it::
    '''
    Test app using the Echo server from the twisted documentation
    you can find simpleserv.py and simpleclient.py here:
    http://twistedmatrix.com/documents/current/core/examples/simpleserv.py
    http://twistedmatrix.com/documents/current/core/examples/simpleclient.py
    '''

    from kivy.app import App
    from kivy.uix.button import Button

    class TwistedTestApp(App):
        def build(self):
            self.setup_twisted_server()
            return  Button(text="Hello" )

        def setup_twisted_server(self):
            from kivy.support import install_twisted_reactor
            install_twisted_reactor()

            from twisted.internet import reactor, protocol
            from simpleserv import Echo
            factory = protocol.ServerFactory()
            factory.protocol = Echo
            reactor.listenTCP(8000, factory)

    if __name__ == '__main__':
        setup_twisted_server()
        TwistedTestApp().run()
